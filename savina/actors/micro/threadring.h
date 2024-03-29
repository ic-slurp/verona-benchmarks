#include <cpp/when.h>
#include "util/bench.h"
#include "util/random.h"

namespace actor_benchmark {

namespace threadring {

using namespace std;

struct RingActor {
  cown_ptr<RingActor> _next;

  RingActor() {}

  RingActor(const cown_ptr<RingActor>& next): _next(next) {}

  static void next(const cown_ptr<RingActor>& self, cown_ptr<RingActor> neighbor) {
    when(self) << [neighbor=move(neighbor)](acquired_cown<RingActor> self)  mutable{
      self->_next = move(neighbor);
    };
  }

  static void pass(const cown_ptr<RingActor>& self, uint64_t left) {
    when(self) << [left](acquired_cown<RingActor> self)  mutable{
      if (left > 0) {
        // assert(self->_next != nullptr); FIXME
        RingActor::pass(self->_next, left - 1);
      } else {
        self->_next = nullptr;
        /* done */
      }
    };
  }
};

};

struct ThreadRing: public ActorBenchmark {
  uint64_t actors;
  uint64_t pass;

  ThreadRing(uint64_t actors, uint64_t pass): actors(actors), pass(pass) {}

  void run() {
    using namespace threadring;

    auto first = make_cown<RingActor>();
    auto next = first;

    for (uint64_t k = 0; k < actors - 1; ++k) {
      auto current = make_cown<RingActor>(move(next));
      next = current;
    }

    RingActor::next(first, move(next));

    if (pass > 0) {
      RingActor::pass(first, pass);
    }
  }

  inline static const std::string name = "Thread Ring";
};

};

