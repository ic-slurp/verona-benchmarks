#pragma once

#include <cpp/when.h>
#include <debug/harness.h>
#include <float.h>
#include "stats.h"

using namespace verona::cpp;

template<class... Ts> struct overloaded : Ts... { using Ts::operator()...; };
template<class... Ts> overloaded(Ts...) -> overloaded<Ts...>;

struct AsyncBenchmark {
  virtual void run()=0;
  virtual std::string paradigm()=0;
  virtual ~AsyncBenchmark() {}
};

struct AsyncBenchmarkBase: AsyncBenchmark {
public:
  static const inline std::string name;
};

struct BocBenchmark: public AsyncBenchmarkBase {
  std::string paradigm() { return "boc"; }
};

struct ActorBenchmark: public AsyncBenchmarkBase {
  std::string paradigm() { return "actor"; }
};

struct Writer {
  virtual void writeHeader()=0;
  virtual void writeEntry(std::string benchmark, double mean, double median, double error, double stddev)=0;
  virtual ~Writer() {}
};

struct CSVWriter: public Writer {
  void writeHeader() override {
    std::cout << "benchmark,mean,median,error" << std::endl;
  }

  void writeEntry(std::string benchmark, double mean, double median, double error, double stddev) override {
    std::cout << benchmark << "," << mean << "," << median << "," << error << std::endl;
  }

  ~CSVWriter() override {}
};

struct ConsoleWriter: public Writer {
  void writeHeader() override { }

  void writeEntry(std::string benchmark, double mean, double median, double error, double stddev) override {
    std::cout << benchmark << "   "
              << mean << " ms   "
              << median << " ms   "
              << "+/- " << error << " %   "
              << stddev
              << std::endl;
  }

  ~ConsoleWriter() override {}
};

struct BenchmarkHarness {
  opt::Opt opt;

  size_t cores;
  size_t repetitions = 1;
  bool detect_leaks;
  std::unique_ptr<Writer> writer;

  static uint64_t& get_seed() {
    static uint64_t seed = 123456;
    return seed;
  }

  BenchmarkHarness(const int argc, const char** argv) : opt(argc, argv) {
    
#ifdef USE_SYSTEMATIC_TESTING
      if (opt.has("--seed"))
      {
        get_seed() = opt.is<size_t>("--seed", 0);
      }
      else
      {
        get_seed() = ((snmalloc::Aal::tick()) & 0xffffffff) * 1000;
      }
#else
      get_seed() = opt.is<size_t>("--seed", 123456);
#endif

#ifndef USE_SCHED_STATS
    if(!opt.has("--csv"))
    {
      std::cout << "BenchmarkHarness starting." << std::endl;

      for (int i = 0; i < argc; i++)
      {
        std::cout << " " << argv[i];
      }

      if (!opt.has("--seed"))
      {
        std::cout << " --seed " << get_seed();
      }

      std::cout << std::endl;
    }
#endif

    cores = opt.is<size_t>("--cores", 4);

#ifdef USE_SYSTEMATIC_TESTING
    repetitions = opt.is<size_t>("--seed_count", 1);
    if (opt.has("--reps"))
    {
      std::cout << "WARNING: --reps is ignored when using systematic testing" << std::endl;
    }

    if (opt.has("--log-all") || (repetitions == 1))
      Logging::enable_logging();
#else
    repetitions = opt.is<size_t>("--reps", 100);
    if (opt.has("--seed_count"))
    {
      std::cout << "WARNING: --seed_count is ignored when not using systematic testing" << std::endl;
    }
#endif

    // snmalloc is the default allocator, and libc has some things it doesn't
    // deallocate.
    detect_leaks = false;
//    detect_leaks = !opt.has("--allow_leaks");
    Scheduler::set_detect_leaks(detect_leaks);

#ifndef USE_SCHED_STATS
    if (!opt.has("--scale"))
    {
      writer = opt.has("--csv") ? std::unique_ptr<Writer>{std::make_unique<CSVWriter>()} : std::make_unique<ConsoleWriter>();
      writer->writeHeader();
    }
#endif
  }

  template<typename T, typename...Args>
  void run(Args&&... args) {
    SampleStats samples;

    T benchmark(std::forward<Args>(args)...);

    size_t min_cores = opt.has("--scale") ? 1 : cores;
    for (size_t c = min_cores; c <= cores; c++) {
      for (size_t i = 0; i < repetitions; ++i) {
        Scheduler& sched = Scheduler::get();

        sched.init(c);

        high_resolution_clock::time_point start = high_resolution_clock::now();

        SchedulerStats::get_tag() = benchmark.name.c_str();

        benchmark.run();

        sched.run();

        double duration = (double)(duration_cast<microseconds>((high_resolution_clock::now() - start)).count()) / 1000;
        samples.add(duration);

        if (opt.has("--scale"))
          std::cout << benchmark.paradigm() << "," << c << "," << benchmark.name << ", " << duration << std::endl;

        if (detect_leaks)
          snmalloc::debug_check_empty<snmalloc::Alloc::Config>();

#ifdef USE_SYSTEMATIC_TESTING
        get_seed()++;
        printf("Seed: %zu\n", get_seed());
#endif
      }
    }
    if (opt.has("--scale"))
      return;
#ifndef USE_SCHED_STATS 
    writer->writeEntry(benchmark.name, samples.mean(), samples.median(), samples.ref_err(), samples.stddev());
#endif
  }
};