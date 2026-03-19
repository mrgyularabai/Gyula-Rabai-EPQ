#include <windows.h>
#include <cstdio>
#include <cstdint>
#include <thread>
#include <vector>
#include <ittnotify.h>

extern "C" void IntAddLoop(uint64_t iterations);
extern "C" void FloatAddLoop(uint64_t iterations);

static constexpr int      NUM_THREADS = 20;
static constexpr uint64_t ITER = 500'000'000'000ULL;
static constexpr uint64_t ITER_PER_THREAD = ITER / NUM_THREADS;


static void intWorker() { IntAddLoop(ITER_PER_THREAD); }
static void floatWorker() { FloatAddLoop(ITER_PER_THREAD); }


static void runParallel(void (*fn)())
{
    std::vector<std::thread> threads;
    threads.reserve(NUM_THREADS);
    for (int i = 0; i < NUM_THREADS; ++i)
        threads.emplace_back(fn);
    for (auto& t : threads)
        t.join();
}


int main()
{
    __itt_domain* domain = __itt_domain_create(L"PowerTest");
    __itt_string_handle* intTask = __itt_string_handle_create(L"INT_ADD");
    __itt_string_handle* floatTask = __itt_string_handle_create(L"FLOAT_ADD");

    printf("Threads : %d\n", NUM_THREADS);
    printf("Iters/thread: %llu\n", ITER_PER_THREAD);

    printf("Starting INT ADD benchmark (%d threads)...\n", NUM_THREADS);
    Sleep(2000);

    __itt_task_begin(domain, __itt_null, __itt_null, intTask);
    runParallel(intWorker);
    __itt_task_end(domain);

    printf("INT ADD done.\n");
    Sleep(500);

    printf("Starting FLOAT ADD benchmark (%d threads)...\n", NUM_THREADS);

    __itt_task_begin(domain, __itt_null, __itt_null, floatTask);
    runParallel(floatWorker);
    __itt_task_end(domain);

    printf("FLOAT ADD done.\n");
    Sleep(500);

    printf("Done.\n");
    return 0;
}