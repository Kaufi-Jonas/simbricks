#include <algorithm>
#include <csignal>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>
#include <thread>

#include <simbricks/base/cxxatomicfix.h>
extern "C" {
#include <simbricks/pcie/if.h>
}

namespace {
bool exiting = false;
uint64_t main_time = 0;

bool simbricks_connect(struct SimbricksPcieIf *pcieif, char *socket,
                       uint64_t link_latency, uint64_t sync_period, bool sync) {
  struct SimbricksProtoPcieDevIntro dev_intro;
  struct SimbricksProtoPcieHostIntro host_intro;
  struct SimbricksBaseIfParams params;

  SimbricksPcieIfDefaultParams(&params);
  params.link_latency = link_latency * 1000;
  params.sync_interval = sync_period * 1000;
  params.blocking_conn = true;
  params.sock_path = socket;
  params.sync_mode =
      (sync ? kSimbricksBaseIfSyncRequired : kSimbricksBaseIfSyncDisabled);

  if (SimbricksBaseIfInit(&pcieif->base, &params)) {
    std::cerr << "SimbricksBaseIfInit failed\n";
    return false;
  }

  if (SimbricksBaseIfConnect(&pcieif->base)) {
    std::cerr << "SimbricksBaseIfConnect failed\n";
    return false;
  }

  if (SimbricksBaseIfConnected(&pcieif->base)) {
    std::cerr << "SimbricksBaseIfConnected indicates unconnected\n";
    return false;
  }

  /* prepare & send host intro */
  std::memset(&host_intro, 0, sizeof(host_intro));
  if (SimbricksBaseIfIntroSend(&pcieif->base, &host_intro,
                               sizeof(host_intro))) {
    std::cerr << "SimbricksBaseIfIntroSend failed\n";
    return false;
  }

  /* receive device intro */
  size_t len = sizeof(dev_intro);
  if (SimbricksBaseIfIntroRecv(&pcieif->base, &dev_intro, &len)) {
    std::cerr << "SimbricksBaseIfIntroRecv failed\n";
    return false;
  }
  if (len != sizeof(dev_intro)) {
    std::cerr << "rx dev intro: length is not as expected\n";
    return false;
  }

  return true;
}

void sigint_handler(int _) {
  exiting = true;
}

void sigusr1_handler(int _) {
  std::cout << "main_time=" << main_time << std::endl;
}
}  // namespace

int main(int argc, char **argv) {
  if (argc != 4) {
    std::cerr << "Usage: dummy_host socket sync_period simulate_until_ps\n";
    return 1;
  }
  uint64_t sync_period = std::stoull(argv[2]);
  uint64_t sim_until = std::stoull(argv[3]);

  signal(SIGINT, sigint_handler);
  signal(SIGUSR1, sigusr1_handler);

  struct SimbricksPcieIf pcieif;
  if (!simbricks_connect(&pcieif, argv[1], sync_period, sync_period, true)) {
    std::cerr << "simbricks_connect() failed\n";
    return 1;
  }

  std::cout << "Starting simulation loop ..." << std::endl;
  uint64_t iterations = 0;
  while (!exiting && main_time < sim_until) {
    iterations++;
    while (SimbricksPcieIfH2DOutSync(&pcieif, main_time)) {
      std::this_thread::yield();
    }

    volatile union SimbricksProtoPcieD2H *msg = nullptr;
    while (!exiting &&
           (msg = SimbricksPcieIfD2HInPoll(&pcieif, main_time)) == nullptr &&
           SimbricksPcieIfD2HInTimestamp(&pcieif) <= main_time) {
    }

    if (msg) {
      switch (msg->base.header.own_type) {
        case SIMBRICKS_PROTO_MSG_TYPE_TERMINATE:
          exiting = true;
          break;
        default:
          /*noop*/
          break;
      }
      SimbricksPcieIfD2HInDone(&pcieif, msg);
    }

    main_time = std::min(SimbricksPcieIfH2DOutNextSync(&pcieif),
                         SimbricksPcieIfD2HInTimestamp(&pcieif));
  }

  std::cout << "iterations=" << iterations << "\n";
  return 0;
}