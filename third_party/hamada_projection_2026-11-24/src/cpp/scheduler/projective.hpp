#pragma once

#include <exception>
#include <functional>
#include <iomanip>
#include <map>
#include <queue>
#include <set>
#include <sstream>
#include <stack>
#include <tuple>

#include "../util/constants.hpp"
#include "../util/instruction.hpp"
#include "../util/problem.hpp"
#include "../util/instructionDependencyManager.hpp"
#include "routingError.hpp"
#include "scheduleResult.hpp"

enum class PositionWeighting { Constant, PowerOfTwo };

class ProjectiveScheduler {
 public:
  Problem prob;
  std::vector<std::vector<int>> adj_ancillary;

  int elapsed_code_beat;
  std::vector<int> heights;

  ProjectiveScheduler(const Problem& prob)
      : prob(prob), adj_ancillary(prob.make_adj_ancillary()) {}

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

  template <PositionWeighting weighting>
  int64_t weight_position(int pos) const {
    if constexpr (weighting == PositionWeighting::Constant) {
      return 1LL;
    } else if constexpr (weighting == PositionWeighting::PowerOfTwo) {
      return 1LL << std::max(0, 32 - (elapsed_code_beat - heights[pos]));
    } else {
      assert(false);
    }
  };

  void initialize() {
    heights.assign(prob.chip_size, 0);
    for (auto&& magic_pos : prob.ms_factories) {
      heights[magic_pos] = prob.magic_prep_time;
    }
    elapsed_code_beat = prob.magic_prep_time;
  }

  std::vector<int> get_target_positions(int target_id) const {
    if (target_id == -1) {
      return prob.ms_factories;
    } else {
      return {prob.data_qubits[target_id]};
    }
  }

  std::vector<std::pair<int, int>> find_3d_path_ignore_topology_infinite_magic(
      const Instruction& inst) const {
    std::vector<std::pair<int, int>> path;
    for (int target_id : inst.targetIds) {
      int pos, t;
      if (target_id != -1) {
        pos = prob.data_qubits[target_id];
        t = heights[pos];
        path.emplace_back(t, pos);
      }
    }
    return path;
  }

  std::vector<std::pair<int, int>> find_3d_path_ignore_topology(
      const Instruction& inst) const {
    std::vector<std::pair<int, int>> path;
    for (int target_id : inst.targetIds) {
      int pos, t;
      if (target_id == -1) {
        t = INF;
        for (auto&& pos_tmp : prob.ms_factories) {
          int t_tmp = heights[pos_tmp];
          if (t > t_tmp) {
            t = t_tmp;
            pos = pos_tmp;
          }
        }
        assert(t < INF);
      } else {
        pos = prob.data_qubits[target_id];
        t = heights[pos];
      }
      path.emplace_back(t, pos);
    }

    return path;
  }

  template <PositionWeighting weighting = PositionWeighting::PowerOfTwo>
  std::vector<int> find_2d_minimum_weight_path(const Instruction& inst) const {
    assert(inst.targetIds.size() == 2);

    const std::vector<int> start_positions =
        get_target_positions(inst.targetIds[0]);
    const int goal_pos = prob.data_qubits[inst.targetIds[1]];

    struct Q {
      int64_t key;
      int pos;
      bool operator<(Q r) const { return key > r.key; }
    };
    std::priority_queue<Q> pq;
    std::vector<int64_t> dist(prob.chip_size, INFLL);
    std::vector<int> parent(prob.chip_size, -1);
    for (auto&& start_pos : start_positions) {
      for (auto&& start_dir : inst.directions[0]) {
        for (auto&& init_pos : next_ancillary_qubits(start_pos, start_dir)) {
          dist[init_pos] = weight_position<weighting>(init_pos);
          parent[init_pos] = start_pos;
          pq.push({dist[init_pos], init_pos});
        }
      }
    }

    std::set<int> goal_next_positions;
    for (auto&& goal_dir : inst.directions[1]) {
      for (auto&& goal_next : next_ancillary_qubits(goal_pos, goal_dir)) {
        goal_next_positions.insert(goal_next);
      }
    }

    while (!pq.empty()) {
      auto [key, p] = pq.top();
      pq.pop();
      if (dist[p] < key) {
        continue;
      }
      if (goal_next_positions.count(p)) {
        break;
      }
      for (auto&& np : next_ancillary_qubits(p)) {
        auto new_weight = dist[p] + weight_position<weighting>(np);
        if (dist[np] > new_weight) {
          dist[np] = new_weight;
          parent[np] = p;
          pq.push({new_weight, np});
        }
      }
    }

    int64_t path_minimum_weight = INFLL;
    int minimum_weight_path_adj = -1;

    auto goal_weight = weight_position<weighting>(goal_pos);
    for (auto&& end_pos : goal_next_positions) {
      int64_t path_weight = dist[end_pos] + goal_weight;
      if (path_minimum_weight > path_weight) {
        path_minimum_weight = path_weight;
        minimum_weight_path_adj = end_pos;
      }
    }

    assert(path_minimum_weight < INFLL);

    std::vector<int> path = {goal_pos, minimum_weight_path_adj};
    while (!prob.is_data_qubit(path.back())) {
      path.push_back(parent[path.back()]);
    }
    std::reverse(path.begin(), path.end());

    return path;
  }

  std::vector<int> get_path_move_heights(const std::vector<int>& path) const {
    std::vector<int> move_heights(path.size() - 1);
    for (int i = 0; i < int(path.size()) - 1; i++) {
      move_heights[i] = std::max(heights[path[i]], heights[path[i + 1]]);
    }
    return move_heights;
  }

  std::vector<std::pair<int, int>> interpolate_3d_path(
      const std::vector<int>& path,
      const std::vector<int>& move_heights) const {
    std::vector<std::pair<int, int>> lifted_3d_path;
    int n = path.size();

    for (int i = 0; i < n; i++) {
      int pos = path[i];
      int h_prev = (i == 0) ? move_heights[0] : move_heights[i - 1];
      int h_next = (i == n - 1) ? move_heights[n - 2] : move_heights[i];

      auto [bottom_height, top_height] = std::minmax({h_prev, h_next});

      std::vector<int> segment_heights(top_height - bottom_height + 1);
      std::iota(segment_heights.begin(), segment_heights.end(), bottom_height);

      if (h_prev > h_next) {
        std::reverse(segment_heights.begin(), segment_heights.end());
      }

      for (auto&& timing : segment_heights) {
        lifted_3d_path.emplace_back(timing, pos);
      }
    }
    return lifted_3d_path;
  }

  int count_kink(const std::vector<int>& path,
                 const std::vector<int>& move_heights) const {
    std::vector<Direction> run_compressed_directions;
    auto push = [&](Direction dir) -> void {
      if (run_compressed_directions.empty() ||
          run_compressed_directions.back() != dir) {
        run_compressed_directions.push_back(dir);
      }
    };

    for (int i = 0; i < int(path.size()) - 1; i++) {
      push(prob.adjacent_direction(path[i], path[i + 1]));
      if (i < int(move_heights.size()) - 1 &&
          move_heights[i] != move_heights[i + 1])
        push(Direction::Z);
    }
    return prob.count_kink(run_compressed_directions);
  }

  bool modify_heights_to_flip_kink_parity(
      const std::vector<int>& path, std::vector<int>& move_heights) const {
    // We only care a kink generated by time axis moves (e.g. X (*T) Y)
    // and ignore a kink generated by Z moves (e.g. X (*T) Z (*T) Y),
    // because the latter case cannot be eliminated by modifying heights.

    int n = path.size();
    std::vector<bool> is_bending_point(n, false);
    for (int i = 1; i < n - 1; i++) {
      Direction prev_dir = prob.adjacent_direction(path[i - 1], path[i]);
      Direction next_dir = prob.adjacent_direction(path[i], path[i + 1]);
      if (prev_dir != Direction::Z && next_dir != Direction::Z &&
          prev_dir != next_dir) {
        // X Y or Y X
        is_bending_point[i] = true;
      }
    }

    std::vector<bool> is_time_kink(path.size(), false);
    for (int i = 1; i < int(path.size()) - 1; i++) {
      if (is_bending_point[i]) {
        if (move_heights[i - 1] != move_heights[i]) {
          is_time_kink[i] = true;
        }
      }
    }

    // - Referring to the modified `move_heights` and the recomputation range,
    //   it recomputes if the kink parity flips.
    // - The recomputation range means the affected segment where
    //   kinks may appear or disappear.
    auto check_current_flip = [&](int recompute_first,
                                  int recompute_last) -> bool {
      recompute_first = std::max(recompute_first, 1);
      recompute_last = std::min(recompute_last, int(move_heights.size()) - 1);

      bool flipped = false;
      for (int i = recompute_first; i < recompute_last + 1; i++) {
        if (is_bending_point[i]) {
          flipped ^= is_time_kink[i];
          bool new_kink = (move_heights[i - 1] != move_heights[i]);
          flipped ^= new_kink;
        }
      }
      return flipped;
    };

    int first_corner = -1;
    for (int i = 1; i < int(path.size()) - 1; i++) {
      if (is_bending_point[i]) {
        first_corner = i;
        break;
      }
    }

    int last_corner = -1;
    for (int i = int(path.size()) - 2; i >= 1; i--) {
      if (is_bending_point[i]) {
        last_corner = i;
        break;
      }
    }

    // If no bending point exists, parity cannot be flipped.
    if (first_corner == -1) return false;

    // 1. Modify a non-kink corner to create a kink (Flips parity)
    std::vector<std::pair<int, int>> extreme_corners = {
        {first_corner - 1, first_corner},
        {last_corner, last_corner - 1},
    };

    // Work on the lower corner to minimize impact
    int first_corner_height =
        std::max(move_heights[first_corner - 1], move_heights[first_corner]);
    int last_corner_height =
        std::max(move_heights[last_corner - 1], move_heights[last_corner]);

    if (first_corner_height > last_corner_height) {
      std::swap(extreme_corners[0], extreme_corners[1]);
    }

    for (auto&& [outer_move, inner_move] : extreme_corners) {
      auto corner = std::max(outer_move, inner_move);
      if (!is_time_kink[corner]) {
        move_heights[outer_move]++;
        assert(check_current_flip(outer_move - 1, outer_move + 1));
        return true;
      }
    }

    // 2. Both are kinks. Try aligning one to remove it.

    // Lift neighbors to match the corner height (eliminates the kink)
    auto [outer_move, inner_move] = extreme_corners[0];
    auto& outer_height = move_heights[outer_move];
    auto& inner_height = move_heights[inner_move];
    outer_height = inner_height = std::max(outer_height, inner_height);
    if (check_current_flip(outer_move - 2, outer_move + 2)) {
      return true;
    }

    // 3. Twist the resulting non-kink corner if parity is still not flipped
    outer_height++;
    assert(check_current_flip(outer_move - 2, outer_move + 2));
    return true;
  }

  std::vector<std::pair<int, int>> find_3d_path_ignore_kink(
      const Instruction& inst) const {
    const auto path = find_2d_minimum_weight_path(inst);
    const auto move_heights = get_path_move_heights(path);
    return interpolate_3d_path(path, move_heights);
  }

  std::vector<std::pair<int, int>> find_3d_path_modify_kink(
      const Instruction& inst) const {
    const auto path = find_2d_minimum_weight_path(inst);
    auto move_heights = get_path_move_heights(path);
    const int parity = count_kink(path, move_heights) % 2;
    if (inst.kink_parity_allowed[parity]) {
      return interpolate_3d_path(path, move_heights);
    } else {
      assert(modify_heights_to_flip_kink_parity(path, move_heights));
      auto path_3d = interpolate_3d_path(path, move_heights);
      assert(prob.count_kink(path_3d) % 2 != parity);
      return path_3d;
    }
  }
  template <RoutingAlgorithm routing_algo>
  std::vector<std::pair<int, int>> find_path(const Instruction& inst) const {
    if constexpr (routing_algo == IgnoreTopologyInfiniteMagic) {
      return find_3d_path_ignore_topology_infinite_magic(inst);
    } else if constexpr (routing_algo == IgnoreTopology) {
      return find_3d_path_ignore_topology(inst);
    } else if constexpr (routing_algo == IgnoreKinkParity) {
      return find_3d_path_ignore_kink(inst);
    } else if constexpr (routing_algo == IgnoreMagicTopology) {
      if (inst.targetIds[0] == -1) {
        return find_3d_path_ignore_topology_infinite_magic(inst);
      } else {
        return find_3d_path_ignore_kink(inst);
      }
    } else if constexpr (routing_algo == CareKinkParity ||
                         routing_algo == ModifyHeights) {
      return find_3d_path_modify_kink(inst);
    } else {
      assert(false);
    }
  }

  template <RoutingAlgorithm routing_algo = CareKinkParity>
  MultiTimeSliceScheduleResult schedule() {
    initialize();

    std::vector<MultiTimeSliceSurgeryPath> surgery_paths;
    surgery_paths.reserve(prob.instructions.size());

    for (auto&& inst : prob.instructions) {
      std::vector<std::pair<int, int>> encoded_path;

      encoded_path = find_path<routing_algo>(inst);
      if (encoded_path.empty()) {
        std::stringstream ss;
        ss << "Routing Failed\n"
           << "Inst: " << inst << '\n';
        MultiTimeSliceScheduleResult(prob, surgery_paths).output_index(ss);
        throw RoutingError(ss.str());
      }

      for (auto&& [t, pos] : encoded_path) {
        assert(heights[pos] <= t);
      }
      for (auto&& [t, pos] : encoded_path) {
        heights[pos] = std::max(heights[pos], t + 1);
        elapsed_code_beat = std::max(elapsed_code_beat, t + 1);
      }
      // Cool time for magic state preparation
      if constexpr (routing_algo != IgnoreTopologyInfiniteMagic &&
                    routing_algo != IgnoreMagicTopology) {
        if (inst.targetIds[0] == -1) {
          const auto [t, pos] = encoded_path[0];
          assert(prob.is_magic_factory(pos));
          heights[pos] += prob.magic_prep_time;
          elapsed_code_beat = std::max(elapsed_code_beat, heights[pos]);
        }
      }

      surgery_paths.emplace_back(encoded_path);
    }
    return MultiTimeSliceScheduleResult(prob, surgery_paths);
  }

  template <RoutingAlgorithm routing_algo = CareKinkParity>
  MultiTimeSliceScheduleResult look_ahead_schedule() {
    initialize();

    std::vector<MultiTimeSliceSurgeryPath> surgery_paths(
        prob.instructions.size());

    auto inst_height = [&](Instruction inst, int inst_index) -> int {
      int height = 0;
      for (int target_id : inst.targetIds) {
        int pos;
        if (target_id != -1) {
          pos = prob.data_qubits[target_id];
          height = std::max(height, heights[pos]);
        }
      }
      return height;
    };

    PrioritizedInstructionDependencyManager<int> manager(
        prob.data_qubits.size(), prob.instructions, inst_height);

    while (!manager.all_finished()) {
      auto inst_index = manager.get_best_ready_index();
      manager.process_instruction(inst_index);
      auto inst = prob.instructions[inst_index];

      std::vector<std::pair<int, int>> encoded_path;

      encoded_path = find_path<routing_algo>(inst);
      if (encoded_path.empty()) {
        std::stringstream ss;
        ss << "Routing Failed\n"
           << "Inst: " << inst << '\n';
        MultiTimeSliceScheduleResult(prob, surgery_paths).output_index(ss);
        throw RoutingError(ss.str());
      }

      for (auto&& [t, pos] : encoded_path) {
        assert(heights[pos] <= t);
      }
      for (auto&& [t, pos] : encoded_path) {
        heights[pos] = std::max(heights[pos], t + 1);
        elapsed_code_beat = std::max(elapsed_code_beat, t + 1);
      }
      // Cool time for magic state preparation
      if constexpr (routing_algo != IgnoreTopologyInfiniteMagic &&
                    routing_algo != IgnoreMagicTopology) {
        if (inst.targetIds[0] == -1) {
          const auto [t, pos] = encoded_path[0];
          assert(prob.is_magic_factory(pos));
          heights[pos] += prob.magic_prep_time;
          elapsed_code_beat = std::max(elapsed_code_beat, heights[pos]);
        }
      }

      surgery_paths[inst_index] = encoded_path;
    }
    return MultiTimeSliceScheduleResult(prob, surgery_paths);
  }
};
