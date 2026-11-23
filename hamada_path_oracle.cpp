// Adapter only. The fixed author's headers are unmodified, MIT licensed.
#include <cstdint>
#include "third_party/hamada_path_2026-11-23/src/cpp/util/problem.hpp"
#include "third_party/hamada_path_2026-11-23/src/cpp/scheduler/singleTimeSlice.hpp"
int main() {
  int width, height, n, c, t, blocked_count;
  if (!(std::cin >> width >> height >> n >> c >> t >> blocked_count)) return 2;
  if (width < 1 || height < 1 || n < 2 || c < 0 || t < 0 || c >= n || t >= n || c == t) return 2;
  Problem p; p.width=width; p.height=height; p.layer_count=2;
  p.chip_size=width*height*2; p.magic_prep_time=0;
  std::vector<int> orientation;
  for (int q=0; q<n; q++) {
    int x,y,o; std::cin >> x >> y >> o;
    if (!p.is_inside(x,y,0) || (o!=0 && o!=1)) return 2;
    orientation.push_back(o);
    // Other live data copies are obstacles, including the unused endpoint slices.
    for(int z=0;z<2;z++) p.position2qubit_index[p.xyz_to_position(x,y,z)]=q;
    p.data_qubits.push_back(p.xyz_to_position(x,y,q==t?1:0));
  }
  SingleTimeSliceScheduler router(p); router.initialize();
  for(int b=0;b<blocked_count;b++) {
    int x,y;std::cin >> x >> y;
    if(!p.is_inside(x,y,0)) return 2;
    for(int z=0;z<2;z++) router.lifetime.set_lifetime(p.xyz_to_position(x,y,z),1);
  }
  Instruction inst("CX",c,t,0);
  // TQEC wall conventions, including the source H orientation changes.
  inst.directions={{orientation[c]?Direction::H:Direction::V},
                   {orientation[t]?Direction::V:Direction::H}};
  auto path=router.find_path<MeetInTheMiddle>(inst);
  std::cout << path.size() << ' ' << p.count_kink(path) << '\n';
  for(int pos:path) {auto[x,y,z]=p.position_to_xyz(pos);std::cout<<x<<' '<<y<<' '<<z<<'\n';}
}
