#pragma once

#include <exception>
#include <string>

class RoutingError : public std::exception {
 public:
  std::string message;

  RoutingError(const std::string& message) : message(message) {}

  const char* what() const noexcept override { return message.c_str(); }
};
