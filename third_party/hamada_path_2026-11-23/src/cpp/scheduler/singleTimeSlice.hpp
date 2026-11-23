#pragma once

#include <algorithm>
#include <exception>
#include <functional>
#include <iomanip>
#include <map>
#include <numeric>
#include <queue>
#include <set>
#include <sstream>
#include <tuple>
#include <vector>

#include "../util/LifetimeArray.hpp"
#include "../util/constants.hpp"
#include "../util/instruction.hpp"
#include "../util/instructionDependencyManager.hpp"
#include "../util/problem.hpp"
#include "routingError.hpp"
#include "scheduleResult.hpp"

class SingleTimeSliceScheduler {
 private:
  // variables for 'find_path_meet_in_the_middle'
  std::vector<std::vector<int>> dist_history, parent_history, parity_history;
  std::vector<std::vector<Direction>> last_h_or_v_history;

 public:
  Problem prob;
  std::vector<std::vector<int>> adj_ancillary;

  LifetimeArray lifetime;

  SingleTimeSliceScheduler(const Problem& prob)
      : dist_history(2),
        parent_history(2),
        parity_history(2),
        last_h_or_v_history(2),
        prob(prob),
        adj_ancillary(prob.make_adj_ancillary()) {}

  const std::vector<int>& next_ancillary_qubits(int position) const {
    assert(0 <= position && position < prob.chip_size);
    return adj_ancillary[position];
  }

  std::vector<int> next_ancillary_qubits(int position,
                                         Direction direction) const {
    assert(0 <= position && position < prob.chip_size);

    std::vector<int> ret;
    for (auto&& next_position : adj_ancillary[position]) {
      if (prob.adjacent_direction(position, next_position) == direction) {
        ret.push_back(next_position);
      }
    }

    return ret;
  }

  void initialize() {
    lifetime.initialize(prob.chip_size);
    for (auto&& magic_pos : prob.ms_factories) {
      lifetime.set_lifetime(magic_pos, prob.magic_prep_time);
    }
  }

  void wait_code_beat() { lifetime.elapse_time(); }

  std::vector<int> available_magic_positions() const {
    std::vector<int> magic_positions;
    for (auto&& magic_pos : prob.ms_factories) {
      if (lifetime.available(magic_pos)) {
        magic_positions.push_back(magic_pos);
      }
    }
    return magic_positions;
  }

  std::vector<int> get_available_target_positions(int target_id) const {
    if (target_id == -1) {
      return available_magic_positions();
    } else {
      int target_pos = prob.data_qubits[target_id];
      return lifetime.available(target_pos) ? std::vector<int>{target_pos}
                                            : std::vector<int>{};
    }
  }

  std::vector<int> find_path_ignore_topology_infinite_magic(
      const Instruction& inst) const {
    std::vector<int> path;
    for (int target_id : inst.targetIds) {
      if (target_id == -1) continue;
      path.push_back(prob.data_qubits[target_id]);
      if (lifetime.unavailable(path.back())) return {};
    }

    return path;
  }

  std::vector<int> find_path_ignore_topology(const Instruction& inst) const {
    std::vector<int> path;
    if (inst.gate == "CX") {
      for (int target_id : inst.targetIds) {
        path.push_back(prob.data_qubits[target_id]);
        if (lifetime.unavailable(path.back())) return {};
      }
    } else if (inst.gate == "MAGIC_MOVE" || inst.gate == "MAGIC_MZZ") {
      for (int target_id : inst.targetIds) {
        if (target_id == -1) {
          bool magic_found = false;
          for (auto&& magic_pos : prob.ms_factories) {
            if (lifetime.available(magic_pos)) {
              path.push_back(magic_pos);
              magic_found = true;
              break;
            }
          }
          if (!magic_found) {
            return {};
          }
        } else {
          path.push_back(prob.data_qubits[target_id]);
          if (lifetime.unavailable(path.back())) return {};
        }
      }
    } else {
      throw std::runtime_error("Unknown gate: " + inst.gate);
    }

    return path;
  }

  std::vector<int> find_path_ignore_kink_parity(const Instruction& inst) const {
    assert(inst.targetIds.size() == 2);

    for (auto&& target_id : inst.targetIds) {
      if (target_id >= 0 && lifetime.unavailable(prob.data_qubits[target_id])) {
        return {};
      }
    }

    std::vector<int> starts = get_available_target_positions(inst.targetIds[0]);
    if (starts.empty()) return {};
    int goal = prob.data_qubits[inst.targetIds[1]];

    std::vector<int> dist(prob.chip_size, INF);
    std::vector<int> parent(prob.chip_size, -1);
    std::queue<int> q;
    for (auto&& start : starts) {
      for (auto&& direction : inst.directions[0]) {
        for (auto&& start_next : next_ancillary_qubits(start, direction)) {
          if (lifetime.available(start_next) && dist[start_next] == INF) {
            dist[start_next] = 1;
            parent[start_next] = start;
            q.push(start_next);
          }
        }
      }
    }

    std::vector<int> goal_nexts;
    for (auto&& direction : inst.directions[1]) {
      for (auto&& goal_next : next_ancillary_qubits(goal, direction)) {
        if (lifetime.available(goal_next)) {
          goal_nexts.push_back(goal_next);
        }
      }
    }

    int goal_next = -1;
    while (!q.empty()) {
      int p = q.front();
      q.pop();
      if (std::count(goal_nexts.begin(), goal_nexts.end(), p)) {
        goal_next = p;
        break;
      }
      for (auto&& np : next_ancillary_qubits(p)) {
        if (lifetime.unavailable(np)) continue;
        if (dist[np] > dist[p] + 1) {
          dist[np] = dist[p] + 1;
          parent[np] = p;
          q.push(np);
        }
      }
    }

    if (goal_next == -1) {
      return {};
    }

    std::vector<int> path = {goal, goal_next};
    while (parent[path.back()] != -1) {
      path.push_back(parent[path.back()]);
    }
    std::reverse(path.begin(), path.end());

    return path;
  }

  std::vector<int> search_path_meet_in_the_middle(
      const std::vector<std::vector<int>>& target_positions,
      const std::vector<std::vector<Direction>>& target_directions,
      int expected_path_parity) {
    for (int i = 0; i < 2; i++) {
      auto& dist = dist_history[i];
      auto& parent = parent_history[i];
      auto& parity = parity_history[i];
      auto& last_h_or_v = last_h_or_v_history[i];
      dist.assign(prob.chip_size, INF);
      parent.assign(prob.chip_size, -1);
      parity.assign(prob.chip_size, 0);
      last_h_or_v.assign(prob.chip_size, Direction::Z);

      std::queue<int> q;
      for (auto&& target_position : target_positions[i]) {
        dist[target_position] = 0;
        for (auto&& direction : target_directions[i]) {
          for (auto&& next_position :
               next_ancillary_qubits(target_position, direction)) {
            if (lifetime.available(next_position) &&
                dist[next_position] == INF) {
              dist[next_position] = 1;
              parent[next_position] = target_position;
              parity[next_position] = 0;
              last_h_or_v[next_position] = direction;
              q.push(next_position);
            }
          }
        }
      }

      while (!q.empty()) {
        int p = q.front();
        q.pop();
        for (auto&& np : next_ancillary_qubits(p)) {
          if (lifetime.unavailable(np)) continue;
          if (dist[np] > dist[p] + 1) {
            dist[np] = dist[p] + 1;
            parent[np] = p;

            Direction nd = prob.adjacent_direction(np, p);
            if (nd == Direction::Z) {
              last_h_or_v[np] = last_h_or_v[p];
              parity[np] = parity[p];
            } else {
              int pp = parent[p];
              Direction ld = prob.adjacent_direction(p, pp);
              last_h_or_v[np] = nd;
              parity[np] =
                  parity[p] ^ (ld == Direction::Z && nd != last_h_or_v[p]);
            }

            q.push(np);
          }
        }
      }
    }

    int shortest_path_length = INF;
    std::vector<int> shortest_path;

    auto backtrack = [&](int target_id, int end) {
      std::vector<int> path = {end};
      while (parent_history[target_id][end] != -1) {
        end = parent_history[target_id][end];
        path.push_back(end);
      }
      return path;
    };

    auto meet_in_the_middle = [&](int end1, int end2) -> bool {
      if (dist_history[0][end1] + dist_history[1][end2] >= shortest_path_length)
        return false;

      const int end1_parent = parent_history[0][end1];
      const int end2_parent = parent_history[1][end2];
      if (end1_parent == end2 || end2_parent == end1) return false;

      const Direction ends_dir = prob.adjacent_direction(end1, end2);
      int path_parity = parity_history[0][end1] ^ parity_history[1][end2];
      if (ends_dir == Direction::Z) {
        // When the vertical segment of a new kink overlaps both of the
        // subpaths.
        path_parity ^=
            (last_h_or_v_history[0][end1] != last_h_or_v_history[1][end2]);
      } else {
        // When the vertical segment of a new kink is in one of the subpaths.
        if (end1_parent != -1 &&
            prob.adjacent_direction(end1, end1_parent) == Direction::Z) {
          path_parity ^= (last_h_or_v_history[0][end1] != ends_dir);
        }
        if (end2_parent != -1 &&
            prob.adjacent_direction(end2, end2_parent) == Direction::Z) {
          path_parity ^= (last_h_or_v_history[1][end2] != ends_dir);
        }
      }

      if (path_parity != expected_path_parity) {
        return false;
      }

      std::vector<int> path1 = backtrack(0, end1), path2 = backtrack(1, end2);
      {
        std::vector<int> sp1 = path1, sp2 = path2;
        std::sort(sp1.begin(), sp1.end());
        std::sort(sp2.begin(), sp2.end());
        std::vector<int> intersection;
        std::set_intersection(sp1.begin(), sp1.end(), sp2.begin(), sp2.end(),
                              std::back_inserter(intersection));

        if (intersection.size()) return false;
      }

      std::vector<int> path = std::move(path1);
      std::reverse(path.begin(), path.end());
      path.insert(path.end(), path2.begin(), path2.end());

      // The following assertion is quite costly so it is commented out.
      // assert(path.empty() || prob.count_kink(path) % 2 ==
      // expected_path_parity);

      shortest_path_length = dist_history[0][end1] + dist_history[1][end2];
      shortest_path = std::move(path);

      return true;
    };

    // If the path has length 3.
    {
      assert(target_positions[1].size() == 1 &&
             target_directions[1].size() == 1);

      int target_position = target_positions[1][0];
      for (auto&& next_target :
           next_ancillary_qubits(target_position, target_directions[1][0])) {
        meet_in_the_middle(next_target, target_position);
      }
    }

    for (int end1 = 0; end1 < prob.chip_size; end1++) {
      if (prob.is_data_qubit(end1)) continue;
      if (dist_history[0][end1] == INF) continue;
      for (auto&& end2 : next_ancillary_qubits(end1)) {
        meet_in_the_middle(end1, end2);
      }
    }

    return shortest_path;
  }

  std::vector<int> find_path_meet_in_the_middle(const Instruction& inst) {
    assert(inst.targetIds.size() == 2);

    for (int target_id : inst.targetIds) {
      if (target_id >= 0 && lifetime.unavailable(prob.data_qubits[target_id])) {
        return {};
      }
    }

    if (inst.gate == "MAGIC_MOVE") {
      return find_path_ignore_kink_parity(inst);
    }

    std::vector<std::vector<int>> target_positions;
    for (auto&& target_id : inst.targetIds) {
      target_positions.push_back(get_available_target_positions(target_id));
      if (target_positions.back().empty()) return {};
    }

    int expected_path_parity;

    if (inst.gate == "CX") {
      // If a path consisting of only the two operand qubits satisfy the parity
      // condition, return the path as the shortest path.
      const int start = target_positions[0][0];
      const int goal = target_positions[1][0];
      if (prob.is_adjacent(start, goal) &&
          prob.adjacent_direction(start, goal) == Direction::Z) {
        return {start, goal};
      }

      expected_path_parity = 1;
    } else if (inst.gate == "MAGIC_MZZ") {
      expected_path_parity = 0;
      const int goal = target_positions[1][0];
      auto [gx, gy, gz] = prob.position_to_xyz(goal);
      std::vector<std::tuple<int, int, int>> next_goal = {{gx - 1, gy, gz},
                                                          {gx + 1, gy, gz}};
      for (auto&& [nx, ny, nz] : next_goal) {
        if (prob.is_inside(nx, ny, nz)) {
          int pos = prob.xyz_to_position(nx, ny, nz);
          if (prob.is_magic_factory(pos) && lifetime.available(pos)) {
            return {pos, goal};
          }
        }
      }

    } else {
      throw std::runtime_error("Unknown gate: " + inst.gate);
    }

    return search_path_meet_in_the_middle(target_positions, inst.directions,
                                          expected_path_parity);
  }

  template <RoutingAlgorithm routing_algo>
  std::vector<int> find_path(const Instruction& inst) {
    if constexpr (routing_algo == IgnoreTopologyInfiniteMagic) {
      return find_path_ignore_topology_infinite_magic(inst);
    } else if constexpr (routing_algo == IgnoreTopology) {
      return find_path_ignore_topology(inst);
    } else if constexpr (routing_algo == IgnoreKinkParity) {
      return find_path_ignore_kink_parity(inst);
    } else if constexpr (routing_algo == IgnoreMagicTopology) {
      if (inst.targetIds[0] == -1) {
        return find_path_ignore_topology_infinite_magic(inst);
      } else {
        return find_path_ignore_kink_parity(inst);
      }
    } else if constexpr (routing_algo == CareKinkParity ||
                         routing_algo == MeetInTheMiddle) {
      return find_path_meet_in_the_middle(inst);
    } else {
      assert(false);
    }
  }

  template <RoutingAlgorithm routing_algo = CareKinkParity>
  SingleTimeSliceScheduleResult naive_schedule() {
    initialize();

    std::vector<SingleTimeSliceSurgeryPath> surgery_paths;
    surgery_paths.reserve(prob.instructions.size());

    for (auto&& inst : prob.instructions) {
      std::vector<int> encoded_path;

      while (true) {
        encoded_path = find_path<routing_algo>(inst);
        if (!encoded_path.empty()) {
          break;
        } else if (lifetime.all_available()) {
          std::stringstream ss;
          ss << "Routing Failed\n"
             << "Inst: " << inst << '\n';
          SingleTimeSliceScheduleResult(prob, surgery_paths).output_index(ss);
          throw RoutingError(ss.str());
        } else {
          wait_code_beat();
        }
      }

      for (auto&& pos : encoded_path) {
        assert(lifetime.available(pos));
        lifetime.set_lifetime(pos, 1);
      }
      // Cool time for magic state preparation
      if constexpr (routing_algo != IgnoreTopologyInfiniteMagic &&
                    routing_algo != IgnoreMagicTopology) {
        if (inst.targetIds[0] == -1) {
          assert(prob.is_magic_factory(encoded_path[0]));
          lifetime.set_lifetime(encoded_path[0], 1 + prob.magic_prep_time);
        }
      }

      surgery_paths.emplace_back(lifetime.current_time(),
                                 std::move(encoded_path));
    }

    return SingleTimeSliceScheduleResult(prob, surgery_paths);
  }

  template <RoutingAlgorithm routing_algo = CareKinkParity>
  SingleTimeSliceScheduleResult look_ahead_schedule() {
    initialize();

    std::vector<SingleTimeSliceSurgeryPath> surgery_paths(
        prob.instructions.size());

    auto reordered_instructions = reorder_instructions(prob);
    InstructionDependencyManager manager(prob.data_qubits.size(),
                                         reordered_instructions);

    while (!manager.all_finished()) {
      auto ready_indices = manager.get_ready_indices();

      for (auto&& inst_index : ready_indices) {
        Instruction inst = reordered_instructions[inst_index];
        std::vector<int> encoded_path;

        encoded_path = find_path<routing_algo>(inst);

        if (lifetime.all_available() && encoded_path.empty()) {
          std::stringstream ss;
          ss << "Routing Failed\n"
             << "Inst: " << inst << '\n';
          SingleTimeSliceScheduleResult(prob, surgery_paths).output_index(ss);
          throw RoutingError(ss.str());
        }

        if (!encoded_path.empty()) {
          manager.process_instruction(inst_index);

          for (auto&& pos : encoded_path) {
            assert(lifetime.available(pos));
            lifetime.set_lifetime(pos, 1);
          }
          // Cool time for magic state preparation
          if constexpr (routing_algo != IgnoreTopologyInfiniteMagic &&
                        routing_algo != IgnoreMagicTopology) {
            if (inst.targetIds[0] == -1) {
              assert(prob.is_magic_factory(encoded_path[0]));
              lifetime.set_lifetime(encoded_path[0], 1 + prob.magic_prep_time);
            }
          }

          surgery_paths[inst.instId] = {lifetime.current_time(),
                                        std::move(encoded_path)};
        }
      }

      wait_code_beat();
    }

    return SingleTimeSliceScheduleResult(prob, surgery_paths);
  }
};
