import subprocess
import os
import time
import csv
import argparse
import psutil

# This will measure setup and teardown time

verona_path = "."
pony_path = "."

def getopts():
    parser = argparse.ArgumentParser(description='Run throughput test.')
    parser.add_argument('--repeats', type=int, default=30,
                        help='number of times to repeat the runs')
    parser.add_argument('-o', default='output', help='output directory location')
    parser.add_argument('--verona-path', default='.', help='path containing verona executables')
    parser.add_argument('--pony-path', default='.', help='path containing pony executables')
    args = parser.parse_args()
    return args

def run_test(args, filename):
    with open(filename, 'w') as file:
        # set stdout to file
        try:
            subprocess.run(args, check=True, stdout=file, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            print("Failed to run Benchmark. Output:")
            with open(filename, 'r') as f:
                print(f.read())
            print("Error:")
            print(e)
            exit(1)

def run_boc_actor(cores, output_directory, repeats):
    print(f"Running boc (actor) on {cores} core")
    # run the boc actor benchmark
    run_test([verona_path + f"/savina", "--actor", "--csv", "--cores", f'{cores}', "--reps", f'{repeats}'], output_directory + f"/boc_actor{cores}.csv")

def run_boc_full(cores, output_directory, repeats):
    print(f"Running boc (full) on {cores} core")
    run_test([verona_path + "/savina", "--full", "--csv", "--cores", f'{cores}', "--reps", f'{repeats}'], output_directory + f"/boc_full{cores}.csv")

def run_pony(cores, output_directory, repeats):
    # Only run if we jave enough cores
    physical_cores = psutil.cpu_count(logical=False)
    if physical_cores < cores:
        print(f"Skipping Pony on {cores} cores as we only have {physical_cores} physicals cores")
        return
    print(f"Running Pony on {cores} core")
    # run the pony benchmark
    run_test([pony_path + "/savina-pony", "--parseable", "--ponymaxthreads", f"{cores}", "--reps", f'{repeats}'], output_directory + f"/pony{cores}.csv")

if __name__ == '__main__':
    args = getopts()

    verona_path = args.verona_path
    pony_path = args.pony_path

    output_directory = args.o
    if not os.path.exists(output_directory):
        os.mkdir(output_directory)

    # Calculate stats of the benchmarks (cown/behaviour counts)
    print("Calculating stats")
    run_test([verona_path + "/savina-stats", "--cores", "1", "--reps", "1", "--actor"], output_directory + f"/actor_stats.csv")
    run_test([verona_path + "/savina-stats", "--cores", "1", "--reps", "1", "--full"], output_directory + f"/boc_stats.csv")

    # Run the banking scale benchmark
    print("Running banking scale")
    run_test([verona_path + "/savina", "--scale", "--csv", "--cores", f"{os.cpu_count()}", "--reps", "50"], output_directory + f"/banking_scale.csv")

    run_pony(1, output_directory, args.repeats)
    run_pony(8, output_directory, args.repeats)

    run_boc_full(1, output_directory, args.repeats)
    run_boc_full(8, output_directory, args.repeats)

    run_boc_actor(1, output_directory, args.repeats)
    run_boc_actor(8, output_directory, args.repeats)
