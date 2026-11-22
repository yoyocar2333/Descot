#pragma once

#include <cassert>
#include <functional>
#include <limits>
#include <queue>
#include <set>
#include <vector>

#include "instruction.hpp"

std::vector<Instruction> reorder_instructions(Problem prob) {
  int m = prob.instructions.size();
  std::vector<int> next_inst_indices(prob.data_qubits.size(), -1);

  // An instruction with large values should be processed earlier.
  std::vector<int> critical_path(m, 1);

  for (int inst_index = m - 1; inst_index >= 0; inst_index--) {
    auto inst = prob.instructions[inst_index];
    for (auto&& target_id : inst.targetIds) {
      if (target_id == -1) continue;
      int next_inst_index = next_inst_indices[target_id];
      critical_path[inst_index] = std::max(critical_path[inst_index],
                                           critical_path[next_inst_index] + 1);
      next_inst_indices[target_id] = inst_index;
    }
  }

  std::vector<int> p(m);
  std::iota(p.begin(), p.end(), 0);
  std::stable_sort(p.begin(), p.end(), [&](int a, int b) {
    return critical_path[a] > critical_path[b];
  });

  std::vector<Instruction> reordered_instructions;
  reordered_instructions.reserve(m);
  for (int idx : p) reordered_instructions.push_back(prob.instructions[idx]);
  return reordered_instructions;
}

struct InstructionDependencyManager : std::set<int> {
  enum State { Ready, Unready, Finished };

  int data_count;
  std::vector<std::queue<int>> queues;
  int finish_count = 0;

  std::vector<Instruction> instructions;
  std::vector<int> in_degrees;
  std::vector<State> states;

  InstructionDependencyManager(int data_count,
                               const std::vector<Instruction>& instructions)
      : data_count(data_count), queues(data_count) {
    this->instructions.reserve(instructions.size());
    in_degrees.reserve(instructions.size());
    states.reserve(instructions.size());
    for (auto&& inst : instructions) {
      push_back_instruction(inst);
    }
  }

  void push_back_instruction(const Instruction& inst) {
    int inst_index = instructions.size();

    instructions.push_back(inst);
    in_degrees.push_back(0);
    states.push_back(Unready);

    for (const auto& target_id : inst.targetIds) {
      if (target_id == -1) continue;
      auto&& q = queues[target_id];
      in_degrees[inst_index] += int(!q.empty());
      q.push(inst_index);
    }

    if (in_degrees[inst_index] == 0) {
      states[inst_index] = Ready;
      insert(inst_index);
    }
  }

  // Returns an iterator that follows the erased instruction.
  std::set<int>::iterator process_instruction(int inst_index) {
    assert(0 <= inst_index && inst_index < int(instructions.size()));
    assert(states[inst_index] == Ready);

    finish_count++;
    states[inst_index] = Finished;
    const Instruction& inst = instructions[inst_index];
    for (const auto& target_id : inst.targetIds) {
      if (target_id == -1) continue;
      auto&& q = queues[target_id];
      assert(q.front() == inst_index);
      q.pop();
      if (!q.empty()) {
        int next_inst_index = q.front();
        in_degrees[next_inst_index] -= 1;
        if (in_degrees[next_inst_index] == 0) {
          states[next_inst_index] = Ready;
          insert(next_inst_index);
        }
      }
    }
    return erase(find(inst_index));
  }

  Instruction get_instruction(int inst_index) {
    assert(0 <= inst_index && inst_index < int(instructions.size()));
    return instructions[inst_index];
  }

  State get_state(int inst_index) {
    assert(0 <= inst_index && inst_index < int(instructions.size()));
    return states[inst_index];
  }

  bool all_finished() { return finish_count == int(instructions.size()); }

  std::set<int> get_ready_indices() { return *this; }
};

template <typename KeyType = int>
struct PrioritizedInstructionDependencyManager {
  enum State { Ready, Unready, Finished };

  using KeyCalculator = std::function<KeyType(const Instruction&, int)>;

  int data_count;
  std::vector<std::queue<int>> queues;
  int finish_count = 0;

  std::vector<Instruction> instructions;
  std::vector<int> in_degrees;
  std::vector<State> states;

  std::vector<KeyType> cached_keys;

  std::set<std::pair<KeyType, int>> ready_set;
  KeyCalculator key_calc;

  PrioritizedInstructionDependencyManager(
      int data_count, const std::vector<Instruction>& instructions,
      KeyCalculator calc = [](const Instruction&,
                              int i) { return static_cast<KeyType>(i); })
      : data_count(data_count), queues(data_count), key_calc(calc) {
    int inst_size = instructions.size();
    this->instructions.reserve(inst_size);
    in_degrees.reserve(inst_size);
    states.reserve(inst_size);
    cached_keys.assign(inst_size, std::numeric_limits<KeyType>::max());

    for (auto&& inst : instructions) {
      push_back_instruction(inst);
    }
  }

  void push_back_instruction(const Instruction& inst) {
    int inst_index = instructions.size();

    instructions.push_back(inst);
    in_degrees.push_back(0);
    states.push_back(Unready);

    for (const auto& target_id : inst.targetIds) {
      if (target_id == -1) continue;
      auto&& q = queues[target_id];
      in_degrees[inst_index] += int(!q.empty());
      q.push(inst_index);
    }

    if (in_degrees[inst_index] == 0) {
      activate_instruction(inst_index);
    }
  }

  void activate_instruction(int inst_index) {
    states[inst_index] = Ready;
    KeyType key = key_calc(instructions[inst_index], inst_index);
    cached_keys[inst_index] = key;
    ready_set.insert({key, inst_index});
  }

  int get_best_ready_index() const {
    assert(!ready_set.empty());
    return ready_set.begin()->second;
  }

  void process_instruction(int inst_index) {
    assert(0 <= inst_index && inst_index < int(instructions.size()));
    assert(states[inst_index] == Ready);

    ready_set.erase({cached_keys[inst_index], inst_index});

    finish_count++;
    states[inst_index] = Finished;

    Instruction inst = instructions[inst_index];
    for (const auto& target_id : inst.targetIds) {
      if (target_id == -1) continue;
      auto&& q = queues[target_id];
      assert(q.front() == inst_index);
      q.pop();
      if (!q.empty()) {
        int next_inst_index = q.front();
        in_degrees[next_inst_index] -= 1;
        if (in_degrees[next_inst_index] == 0) {
          activate_instruction(next_inst_index);
        }
      }
    }
  }

  bool all_finished() const { return finish_count == int(instructions.size()); }
};
