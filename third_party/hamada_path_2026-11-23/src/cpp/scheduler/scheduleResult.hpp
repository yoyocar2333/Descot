#pragma once

#include "../util/problem.hpp"

typedef std::vector<std::vector<std::vector<std::vector<int>>>> vector4D;

class SurgeryPathBase {
 public:
  virtual ~SurgeryPathBase() = default;
  virtual int length() const = 0;
  virtual std::pair<int, int> at(size_t) const = 0;
  virtual std::vector<std::pair<int, int>> getTimingPositions() const = 0;
};

class SingleTimeSliceSurgeryPath : public SurgeryPathBase {
 public:
  // 0-indexed the time when the surgery path is executed
  int timing;

  // 0-indexed positions in the path.
  std::vector<int> positions;

  SingleTimeSliceSurgeryPath() : timing(-1) {}
  SingleTimeSliceSurgeryPath(int timing, const std::vector<int>& positions)
      : timing(timing), positions(positions) {}

  int length() const override { return positions.size(); }

  std::pair<int, int> at(size_t index) const override {
    return std::make_pair(timing, positions.at(index));
  }

  std::vector<std::pair<int, int>> getTimingPositions() const override {
    std::vector<std::pair<int, int>> result;
    for (auto&& pos : positions) result.emplace_back(timing, pos);
    return result;
  }
};

class MultiTimeSliceSurgeryPath : public SurgeryPathBase {
 public:
  int required_time = 0;
  std::vector<std::pair<int, int>> timing_positions;

  MultiTimeSliceSurgeryPath() = default;
  MultiTimeSliceSurgeryPath(const std::vector<std::pair<int, int>>& tpos)
      : timing_positions(tpos) {
    for (auto& tp : tpos) required_time = std::max(required_time, tp.first + 1);
  }

  std::vector<SingleTimeSliceSurgeryPath> fragment() const {
    std::vector<int> split_indices = {0};
    for (int i = 1; i < int(timing_positions.size()); i++) {
      if (timing_positions[i - 1].first != timing_positions[i].first) {
        split_indices.push_back(i);
      }
    }
    split_indices.push_back(timing_positions.size());

    const int run_count = int(split_indices.size()) - 1;
    std::vector<SingleTimeSliceSurgeryPath> fragments;
    fragments.reserve(run_count);
    for (int run_idx = 0; run_idx < run_count; run_idx++) {
      const int run_start = split_indices[run_idx];
      const int run_end = split_indices[run_idx + 1];
      const int timing = timing_positions[run_start].first;
      std::vector<int> positions;
      positions.reserve(run_end - run_start);
      for (int i = run_start; i < run_end; i++) {
        positions.push_back(timing_positions[i].second);
      }
      fragments.push_back(SingleTimeSliceSurgeryPath(timing, positions));
    }

    return fragments;
  }

  int length() const override { return timing_positions.size(); }

  std::pair<int, int> at(size_t index) const override {
    return timing_positions[index];
  }

  std::vector<std::pair<int, int>> getTimingPositions() const override {
    return timing_positions;
  }
};

// Base class template
template <typename PathType>
class ScheduleResultBase {
 public:
  Problem prob;
  int total_time;
  std::vector<PathType> surgery_paths;

  ScheduleResultBase(const Problem& p, const std::vector<PathType>& paths)
      : prob(p), total_time(0), surgery_paths(paths) {}

  virtual vector4D construct_lattice() const = 0;
  virtual void to_visualizer(std::ostream& os, int maxSz) const = 0;
  virtual void output_index(std::ostream& os) {
    auto schedule_result = construct_lattice();
    auto marker = [](int a) -> std::string { return std::to_string(a); };
    output_schedule(os, prob, schedule_result, marker, 4);
  }

  int64_t compute_circuit_volume() const {
    // Initialize with the pillars' volume
    int64_t circuit_volume = total_time * prob.data_qubits.size();

    for (int index = 0; index < int(prob.instructions.size()); index++) {
      const auto& path = surgery_paths[index];

      if (path.length() >= 2) {  // General case
        // Add routing volume of the ancillary qubits
        circuit_volume += path.length() - 2;
      } else if (path.length() == 1) {  // Magic ops. when #MSFs are infinite
        // Consider the MSF volume
        circuit_volume += 1;
      } else {  // Paths cannot be empty.
        assert(false);
      }

      auto gate = prob.instructions[index].gate;
      if (gate == "MAGIC_MZZ" || gate == "MAGIC_MOVE") {
        circuit_volume += prob.magic_prep_time;
      }
    }

    return circuit_volume;
  }

 protected:
  template <typename Marker>
  static void output_schedule(std::ostream& os, const Problem& prob,
                              const vector4D& schedule_result, Marker marker,
                              int display_width) {
    int bg;
    std::string bg_l, bg_r;

    for (auto&& time_slice : schedule_result) {
      for (int y = 0; y < prob.height; y++) {
        for (int z = 0; z < prob.layer_count; z++) {
          for (int x = 0; x < prob.width; x++) {
            std::string val;
            int position = prob.xyz_to_position(x, y, z);
            if (prob.is_data_qubit(position)) {
              int index = prob.position2qubit_index.at(position);
              val = marker(index + 1);
            } else {
              val = ".";
            }
            if (time_slice[z][y][x]) {
              bg = (time_slice[z][y][x]) % 7 + 1;
              bg_l = "\e[4" + std::to_string(bg) + "m";
              bg_r = "\e[0m";
            } else {
              bg_l = "";
              bg_r = "";
            }
            os << bg_l << std::setw(display_width) << val << bg_r;
          }
          os << ((z == prob.layer_count - 1) ? "\n"
                                             : std::string(display_width, ' '));
        }
      }
      os << '\n';
    }
  }

  void _to_visualizer(std::ostream& os, const Problem& prob,
                      const std::vector<PathType>& paths,
                      const int maxSz) const {
    // chip info
    os << prob.width << " " << prob.height << " " << prob.layer_count << "\n";

    // data qubits and magic factories positions
    os << prob.data_qubits.size() << " " << prob.ms_factories.size() << "\n";
    for (const auto& positions : {prob.data_qubits, prob.ms_factories})
      for (auto pos : positions) {
        auto [x, y, z] = prob.position_to_xyz(pos);
        os << x << " " << y << " " << z << "\n";
      }

    assert(prob.instructions.size() == paths.size());
    assert(std::is_sorted(
        prob.instructions.begin(), prob.instructions.end(),
        [](const auto& a, const auto& b) { return a.instId < b.instId; }));

    if (int(paths.size()) > maxSz)
      std::cerr << "WARNING: Too many paths to visualize. "
                   "We only visualize the first "
                << maxSz << " paths." << std::endl;
    int maxPathSz = std::min(maxSz, int(paths.size()));
    int maxTiming = 0;
    for (int j = 0; j < maxPathSz; j++) {
      const auto& path = paths[j];
      for (auto&& [timing, _] : path.getTimingPositions())
        maxTiming = std::max(maxTiming, timing);
    }
    os << maxPathSz << " " << maxTiming << "\n";
    for (int j = 0; j < maxPathSz; j++) {
      const auto& inst = prob.instructions[j];
      const auto& path = paths[j];

      // instruction infos
      assert(int(inst.targetIds.size()) == 2);
      auto targetIds = inst.targetIds;
      auto first_pos = path.at(0).second;
      if (targetIds[0] == -1 && prob.position2qubit_index.count(first_pos))
        targetIds[0] = prob.position2qubit_index.at(first_pos);

      os << targetIds.size() << "\n";
      for (int tId : targetIds) os << tId << " ";
      os << "\n";

      // path positions
      auto timingPositions = path.getTimingPositions();
      os << timingPositions.size() << "\n";
      for (auto&& [timing, pos] : timingPositions) {
        const auto& [x, y, z] = prob.position_to_xyz(pos);
        os << timing << " " << x << " " << y << " " << z << "\n";
      }
    }
  }

  static vector4D _construct_lattice(const Problem& prob, int total_time,
                                     const std::vector<PathType>& paths) {
    vector4D lattice(total_time,
                     std::vector<std::vector<std::vector<int>>>(
                         prob.layer_count,
                         std::vector<std::vector<int>>(
                             prob.height, std::vector<int>(prob.width, 0))));

    for (int path_idx = 0; path_idx < int(paths.size()); path_idx++) {
      const auto& path = paths[path_idx];
      for (auto&& [timing, position] : path.getTimingPositions()) {
        auto [x, y, z] = prob.position_to_xyz(position);
        lattice[timing][z][y][x] = path_idx + 1;
      }
    }

    return lattice;
  }
};

class SingleTimeSliceScheduleResult
    : public ScheduleResultBase<SingleTimeSliceSurgeryPath> {
 public:
  using Base = ScheduleResultBase<SingleTimeSliceSurgeryPath>;
  SingleTimeSliceScheduleResult(
      const Problem& prob,
      const std::vector<SingleTimeSliceSurgeryPath>& surgery_paths)
      : Base(prob, surgery_paths) {
    for (auto&& surgery_path : surgery_paths) {
      total_time = std::max(total_time, surgery_path.timing + 1);
    }
  }

  vector4D construct_lattice() const override {
    return Base::_construct_lattice(prob, total_time, surgery_paths);
  }

  void to_visualizer(std::ostream& os, int maxSz) const override {
    _to_visualizer(os, prob, surgery_paths, maxSz);
  }
};

class MultiTimeSliceScheduleResult
    : public ScheduleResultBase<MultiTimeSliceSurgeryPath> {
 public:
  using Base = ScheduleResultBase<MultiTimeSliceSurgeryPath>;
  MultiTimeSliceScheduleResult(
      const Problem& prob,
      const std::vector<MultiTimeSliceSurgeryPath>& surgery_paths)
      : Base(prob, surgery_paths) {
    for (auto&& surgery_path : surgery_paths) {
      total_time = std::max(total_time, surgery_path.required_time);
    }
  }

  MultiTimeSliceScheduleResult(SingleTimeSliceScheduleResult single_result)
      : Base(single_result.prob, {}) {
    surgery_paths.reserve(single_result.surgery_paths.size());
    for (auto&& single_path : single_result.surgery_paths) {
      std::vector<std::pair<int, int>> timing_positions;
      timing_positions.reserve(single_path.positions.size());
      for (auto&& pos : single_path.positions) {
        timing_positions.emplace_back(single_path.timing, pos);
      }
      surgery_paths.emplace_back(timing_positions);
    }
    total_time = single_result.total_time;
  }

  vector4D construct_lattice() const override {
    return Base::_construct_lattice(prob, total_time, surgery_paths);
  }

  void to_visualizer(std::ostream& os, int maxSz) const override {
    _to_visualizer(os, prob, surgery_paths, maxSz);
  }
};
