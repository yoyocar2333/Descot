#pragma once

#include <cassert>
#include <exception>
#include <fstream>
#include <functional>
#include <iomanip>
#include <map>
#include <queue>
#include <set>
#include <sstream>
#include <string>
#include <tuple>
#include <vector>

#include "constants.hpp"
#include "instruction.hpp"

class Problem {
 public:
  int width, height, layer_count;  // data chip size
  int chip_size;                   // width * height * layer_count
  std::vector<Instruction> instructions;

  // These variables will be set in Allocator::allocate
  std::vector<int> data_qubits;   // data qubit
  std::vector<int> ms_factories;  // magic state factory

  // idx<=data_qubits.size() -> data qubit
  // idx> data_qubits.size() -> magic state factory
  std::map<int, int> position2qubit_index;

  std::string file_path;

  int magic_prep_time;  // Code beats needed to prepare a magic state.

  Problem()
      : width(-1),
        height(-1),
        layer_count(-1),
        chip_size(-1),
        file_path("no_file") {}

  Problem(std::string file_path, int magic_prep_time = 2)
      : file_path(file_path), magic_prep_time(magic_prep_time) {
    reset();
    read_file(file_path);
  }

 private:
  void read_file(const std::string& file_path) {
    assert(instructions.empty());

    std::ifstream is(file_path);
    if (!is) {
      throw std::runtime_error("Cannot open file: " + file_path);
    }
    int operand, instId = 0;
    std::string line, gate;
    std::set<int> qubit_ids;

    while (std::getline(is, line)) {
      if (line.empty()) continue;
      std::stringstream ss(line);
      ss >> gate;
      std::vector<int> operands;
      while (ss >> operand) operands.push_back(operand);

      if (gate == "CX") {
        assert(operands.size() == 2);
        int control = operands[0], target = operands[1];
        instructions.emplace_back(gate, control, target, instId);
      } else if (gate == "MAGIC_MOVE" || gate == "MAGIC_MZZ") {
        assert(operands.size() == 1);
        int source = -1, target = operands[0];
        instructions.emplace_back(gate, source, target, instId);
      } else {
        throw std::runtime_error("Unknown gate: " + gate);
      }
      instId++;

      qubit_ids.insert(operands.begin(), operands.end());
    }
    // There should be no missing qubit id
    assert(int(qubit_ids.size()) ==
           *max_element(qubit_ids.begin(), qubit_ids.end()) + 1);
    data_qubits.assign(qubit_ids.size(), -1);
  }

 public:
  void reset() {
    width = -1, height = -1, layer_count = -1, chip_size = -1;
    data_qubits.assign(data_qubits.size(), -1);
    ms_factories.clear();
    position2qubit_index.clear();
  }

  std::vector<std::vector<int>> make_adj_ancillary() const {
    std::vector<std::vector<int>> adj_ancillary(chip_size);
    for (int position = 0; position < chip_size; position++) {
      auto [x, y, z] = position_to_xyz(position);
      auto nXYZs = std::vector<std::tuple<int, int, int>>{
          {x - 1, y, z}, {x + 1, y, z}, {x, y - 1, z},
          {x, y + 1, z}, {x, y, z - 1}, {x, y, z + 1}};
      for (auto [nx, ny, nz] : nXYZs) {
        if (!is_inside(nx, ny, nz)) continue;
        int next_pos = xyz_to_position(nx, ny, nz);
        if (is_data_qubit(next_pos)) continue;
        adj_ancillary[position].push_back(next_pos);
      }
    }
    return adj_ancillary;
  }

  bool is_inside(int x, int y, int z) const {
    return (0 <= x && x < width) && (0 <= y && y < height) &&
           (0 <= z && z < layer_count);
  }

  bool is_data_qubit(int position) const {
    return position2qubit_index.count(position);
  }
  bool is_magic_factory(int position) const {
    return position2qubit_index.count(position) &&
           position2qubit_index.at(position) >= int(data_qubits.size());
  }

  int xyz_to_position(int x, int y, int z) const {
    assert(is_inside(x, y, z));
    return (x + (y + z * height) * width);
  }
  int xyz_to_position(const std::tuple<int, int, int>& xyz) const {
    auto [x, y, z] = xyz;
    return xyz_to_position(x, y, z);
  }

  std::tuple<int, int, int> position_to_xyz(int position) const {
    assert(0 <= position && position < height * width * layer_count);
    int x = position % width;
    int q = position / width;
    int y = q % height;
    int z = q / height;
    return {x, y, z};
  }

  bool is_adjacent(int position1, int position2) const {
    auto [x1, y1, z1] = position_to_xyz(position1);
    auto [x2, y2, z2] = position_to_xyz(position2);
    int diff_sum = abs(x1 - x2) + abs(y1 - y2) + abs(z1 - z2);
    return diff_sum == 1;
  }

  Direction adjacent_direction(int position1, int position2) const {
    auto [x1, y1, z1] = position_to_xyz(position1);
    auto [x2, y2, z2] = position_to_xyz(position2);
    int x_diff = abs(x1 - x2);
    int y_diff = abs(y1 - y2);
    int z_diff = abs(z1 - z2);
    if (x_diff + y_diff + z_diff != 1) {
      throw std::runtime_error("Not adjacent");
    }
    if (x_diff) {
      return Direction::X;
    } else if (y_diff) {
      return Direction::Y;
    } else if (z_diff) {
      return Direction::Z;
    } else {
      throw std::runtime_error("Unreachable: the code has bug.");
    }
  }

  std::vector<Direction> run_compressed_adjacent_directions(
      const std::vector<int>& path_positions) const {
    std::vector<Direction> run_compressed_directions;
    for (int path_idx = 0; path_idx < int(path_positions.size()) - 1;
         path_idx++) {
      int pos0 = path_positions[path_idx];
      int pos1 = path_positions[path_idx + 1];
      Direction dir = adjacent_direction(pos0, pos1);
      if (run_compressed_directions.empty() ||
          run_compressed_directions.back() != dir) {
        run_compressed_directions.push_back(dir);
      }
    }
    return run_compressed_directions;
  }

  std::vector<Direction> run_compressed_adjacent_directions(
      const std::vector<std::pair<int, int>>& path) const {
    std::vector<Direction> run_compressed_directions;
    for (int path_idx = 0; path_idx < int(path.size()) - 1; path_idx++) {
      auto [t0, pos0] = path[path_idx];
      auto [t1, pos1] = path[path_idx + 1];
      Direction dir;
      if (t0 != t1) {
        // We can regard time axis and Z axis as the same direction
        // when counting kinks.
        dir = Direction::Z;
      } else {
        dir = adjacent_direction(pos0, pos1);
      }
      if (run_compressed_directions.empty() ||
          run_compressed_directions.back() != dir) {
        run_compressed_directions.push_back(dir);
      }
    }
    return run_compressed_directions;
  }

  int count_kink(
      const std::vector<Direction>& run_compressed_directions) const {
    int kink_count = 0;
    for (int dir_idx = 1; dir_idx < int(run_compressed_directions.size()) - 1;
         dir_idx++) {
      if (run_compressed_directions[dir_idx] == Direction::Z &&
          run_compressed_directions[dir_idx - 1] !=
              run_compressed_directions[dir_idx + 1]) {
        kink_count++;
      }
    }
    return kink_count;
  }

  // Count kinks of a path in a single time slice.
  int count_kink(const std::vector<int>& path) const {
    if (path.size() <= 3) return 0;
    return count_kink(run_compressed_adjacent_directions(path));
  }

  // Count kinks of a path that crosses multiple time slices.
  int count_kink(const std::vector<std::pair<int, int>>& path) const {
    if (path.size() <= 3) return 0;
    return count_kink(run_compressed_adjacent_directions(path));
  }
};
