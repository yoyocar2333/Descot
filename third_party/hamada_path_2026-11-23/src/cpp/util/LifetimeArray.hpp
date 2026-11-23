#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

class LifetimeArray {
 private:
  int now;
  std::vector<int> end_time;
  int end_time_max;

 public:
  LifetimeArray() = default;

  LifetimeArray(int length) : now(0), end_time(length, 0), end_time_max(0) {}

  void initialize() { initialize(end_time.size()); }

  void initialize(int length) {
    now = 0;
    end_time.assign(length, 0);
    end_time_max = 0;
  }

  void set_lifetime(size_t index, int lifetime = 1) {
    end_time[index] = std::max(end_time[index], now + lifetime);
    end_time_max = std::max(end_time_max, now + lifetime);
  }

  void elapse_time() { now++; }

  int current_time() const { return now; }

  bool available(size_t index) const { return end_time[index] <= now; }
  bool unavailable(size_t index) const { return !available(index); }

  bool all_available() const { return end_time_max <= now; }
};
