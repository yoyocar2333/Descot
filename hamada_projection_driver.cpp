// Full-source adapter; native headers below are byte-identical to fixed release.
#include <cstdint>
#include <numeric>
#include "third_party/hamada_projection_2026-11-24/src/cpp/scheduler/projective.hpp"
struct SourceOp {std::string name;std::vector<int> qs,preds;};
int main(int argc,char** argv){
 if(argc!=2)return 2;
 std::string policy=argv[1];if(policy!="source_order" && policy!="height_priority")return 2;
 int n,m,spacing;if(!(std::cin>>n>>m>>spacing)||n<2||n>6||spacing<3||spacing>5)return 2;
 Problem p;p.width=p.height=spacing*(n-1)+1;p.layer_count=1;p.chip_size=p.width*p.height;p.magic_prep_time=0;
 for(int q=0;q<n;q++){int pos=p.xyz_to_position(q*spacing,q*spacing,0);p.data_qubits.push_back(pos);p.position2qubit_index[pos]=q;}
 std::vector<SourceOp> ops;
 for(int id=0;id<m;id++){
  std::string name;int nq,np;std::cin>>name>>nq;if(nq<0||nq>n)return 2;
  SourceOp op;op.name=name;for(int j=0;j<nq;j++){int q;std::cin>>q;if(q<0||q>=n)return 2;op.qs.push_back(q);}
  std::cin>>np;for(int j=0;j<np;j++){int pred;std::cin>>pred;if(pred<0||pred>=id)return 2;op.preds.push_back(pred);}
  if(name!="h"&&name!="x"&&name!="cx"&&name!="measure"&&name!="barrier")return 3;
  if(name=="cx"&&nq!=2)return 3;
  Instruction inst("CX",0,1,id);inst.targetIds=op.qs;p.instructions.push_back(inst);ops.push_back(op);
 }
 ProjectiveScheduler scheduler(p);scheduler.initialize();std::vector<int> orientation(n,0);std::set<int> done;
 auto key=[&](const Instruction& inst,int index){if(policy=="source_order")return index;int h=0;for(int q:inst.targetIds)h=std::max(h,scheduler.heights[p.data_qubits[q]]);return h;};
 PrioritizedInstructionDependencyManager<int> manager(n,p.instructions,key);
 while(!manager.all_finished()){
  // Independently check full source predecessors, including barrier operands.
  std::set<int> expected,actual;for(int i=0;i<m;i++)if(!done.count(i)){
   bool ready=true;for(int pred:ops[i].preds)ready&=done.count(pred)>0;if(ready)expected.insert(i);
  }
  for(auto entry:manager.ready_set)actual.insert(entry.second);
  if(expected!=actual)return 4;
  int id=manager.get_best_ready_index();auto op=ops[id];int start=0;for(int q:op.qs)start=std::max(start,scheduler.heights[p.data_qubits[q]]);
  std::vector<int> before=scheduler.heights;std::vector<std::pair<int,int>> path;
  if(op.name=="cx"){
   Instruction inst=p.instructions[id];int c=op.qs[0],t=op.qs[1];
   inst.directions={{orientation[c]?Direction::H:Direction::V},{orientation[t]?Direction::V:Direction::H}};
   path=scheduler.find_path<CareKinkParity>(inst);
   if(path.empty()||p.count_kink(path)%2!=1)return 5;
   for(auto [time,pos]:path)if(scheduler.heights[pos]>time)return 6;
   for(auto [time,pos]:path){scheduler.heights[pos]=std::max(scheduler.heights[pos],time+1);scheduler.elapsed_code_beat=std::max(scheduler.elapsed_code_beat,time+1);}
  }else if(op.name=="h"){
   if(op.qs.size()!=1)return 3;
   int q=op.qs[0];scheduler.heights[p.data_qubits[q]]=start+3;orientation[q]^=1;
   scheduler.elapsed_code_beat=std::max(scheduler.elapsed_code_beat,start+3);
  }
  std::cout<<"OP "<<id<<' '<<start<<' '<<path.size()<<' '<<(op.name=="cx"?p.count_kink(path):0)<<'\n';
  for(auto [time,pos]:path){auto [x,y,z]=p.position_to_xyz(pos);std::cout<<x<<' '<<y<<' '<<time<<'\n';}
  std::cout<<"BEFORE";for(int h:before)std::cout<<' '<<h;std::cout<<'\n';
  std::cout<<"AFTER";for(int h:scheduler.heights)std::cout<<' '<<h;std::cout<<'\n';
  // Paper Alg4/section3.5.4 updates the height map before activating children.
  // Native new release's look_ahead_schedule activates earlier; do not silently
  // claim bit-for-bit equivalence of that full loop.
  done.insert(id);manager.process_instruction(id);
 }
 std::cout<<"END "<<scheduler.elapsed_code_beat<<'\n';
}
