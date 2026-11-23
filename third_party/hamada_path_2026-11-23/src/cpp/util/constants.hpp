#pragma once

#include <array>

constexpr int INF = 1'000'000'000;
constexpr int64_t INFLL = 1'000'000'000'000'000'000;

enum class Direction { H = 0, V = 1, X = 0, Y = 1, Z = 2 };

enum RoutingAlgorithm {
  IgnoreTopologyInfiniteMagic,
  IgnoreTopology,
  IgnoreMagicTopology,
  IgnoreKinkParity,
  CareKinkParity,
  MeetInTheMiddle,
  InvertPath,
  InvertTwoCells,
  ModifyHeights
};
