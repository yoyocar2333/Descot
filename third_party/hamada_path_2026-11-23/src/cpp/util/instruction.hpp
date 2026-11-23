#pragma once

#include <algorithm>
#include <cassert>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "constants.hpp"

struct Instruction {
  int instId;
  std::string gate;

  // targetIds: which logical qubits are involved
  //            if the id==-1, it means we will use the magic state factory.
  //            However, notice that we should connect to an idx larger than
  //            or equal to prob.data_qubits.size().
  std::vector<int> targetIds;

  std::vector<std::vector<Direction>> directions;
  std::array<bool, 2> kink_parity_allowed;

  Instruction(std::string gate, int control, int target, int instId)
      : instId(instId), gate(gate) {
    if (gate == "CX") {
      targetIds = {control, target};
      directions = {{Direction::H}, {Direction::V}};
      kink_parity_allowed = {false, true};
    } else if (gate == "MAGIC_MZZ") {
      targetIds = {-1, target};
      directions = {{Direction::H}, {Direction::H}};
      kink_parity_allowed = {true, false};
    } else if (gate == "MAGIC_MOVE") {
      targetIds = {-1, target};
      directions = {{Direction::H, Direction::V}, {Direction::H, Direction::V}};
      kink_parity_allowed = {true, true};
    } else {
      throw std::runtime_error("Unknown gate: " + gate);
    }
  }

  friend std::ostream& operator<<(std::ostream& os, const Instruction& inst) {
    int t = inst.targetIds.size();
    os << t << '\n';
    for (int i = 0; i < t; i++) os << inst.targetIds[i] << ' ';
    os << '\n';
    return os;
  }
};
