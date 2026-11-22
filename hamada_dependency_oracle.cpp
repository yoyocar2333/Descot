// Adapter harness only. Original MIT headers remain unmodified.
#include <numeric>
#include <iostream>
#include "third_party/hamada_dependency_2026-11-22/src/cpp/util/problem.hpp"
#include "third_party/hamada_dependency_2026-11-22/src/cpp/util/instructionDependencyManager.hpp"
int main() {
  int n, m; std::cin >> n >> m;
  std::vector<Instruction> ops;
  for (int i=0; i<m; ++i) {
    int k; std::cin >> k;
    Instruction inst("CX",0,1,i);  // constructor needs two operands; DAG uses targets only
    inst.targetIds.clear();
    while(k--) { int q; std::cin >> q; inst.targetIds.push_back(q); }
    ops.push_back(inst);
  }
  InstructionDependencyManager manager(n,ops);
  char command; int queries=0, processed=0;
  while(std::cin >> command) {
    if(command=='R') {
      int k; std::cin >> k; std::set<int> expected;
      while(k--) { int i; std::cin >> i; expected.insert(i); }
      if(manager.get_ready_indices()!=expected) return 2;
      ++queries;
    } else if(command=='P') {
      int i; std::cin >> i;
      if(manager.get_state(i)!=InstructionDependencyManager::Ready) return 3;
      manager.process_instruction(i); ++processed;
    } else if(command=='F') {
      if(!manager.all_finished()) return 4;
      std::cout << queries << " " << processed << "\n"; return 0;
    } else return 5;
  }
  return 6;
}
