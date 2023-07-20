import subprocess
import os
import time
import csv
import argparse

# This will measure setup and teardown time


def getopts():
    parser = argparse.ArgumentParser(description='Run throughput test.')
    parser.add_argument('--repeats', type=int, default=30,
                        help='number of times to repeat the runs')
    parser.add_argument('-o', default='output', help='outfile location')
    parser.add_argument("--verona-path", default=".", help="path containing verona dining philosophers binary")
    parser.add_argument("--fast", action='store_true', help="run the fast version of the benchmark")
    args = parser.parse_args()
    return args


def run_test(args, num, csv, file):
    start = time.time()
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)
    end = time.time()
    csv.writerow((num, end - start))
    file.flush()


def make_csv(file):
    csv_file = csv.writer(file)
    csv_file.writerow(['cores', 'time'])
    return csv_file


if __name__ == '__main__':
    args = getopts()
    output_directory = args.o
    if not os.path.exists(output_directory):
        os.mkdir(output_directory)

    print("Running dining philosophers")
    if not args.fast:
        print("This will take a while... There is 50 seconds of busy work per run.")
        print("Consider adding --fast if you are in a rush.")

    verona_path = args.verona_path
    # Dump it as a csv file so we can use it for pgfplots
    with open(output_directory + '/verona_dining_opt.csv', 'w') as vdo,\
         open(output_directory + '/verona_dining_seq.csv', 'w') as vds,\
         open(output_directory + '/pthread_dining_seq.csv', 'w') as pds,\
         open(output_directory + '/pthread_dining_opt.csv', 'w') as pdo,\
         open(output_directory + '/verona_dining_opt_200.csv', 'w') as vdo200:
        csv_writer_vdo = make_csv(vdo)
        csv_writer_vds = make_csv(vds)
        csv_writer_pds = make_csv(pds)
        csv_writer_pdo = make_csv(pdo)
        csv_writer_vdo200 = make_csv(vdo200)
        philosophers = 100
        if args.fast:
            hunger = 50
        else:
            hunger = 500
        exe = verona_path + '/perf-con-dining_phil'
        for exp in range(args.repeats):
            cores = range(1, os.cpu_count() + 1)
            min_cores = [1, 2, 3, 4, 5, 10, 20, 40, 60, 72]
            for num in cores:
                run_test([exe, '--cores', f'{num}',
                          '--hunger', f'{hunger}', '--num_tables', '1', '--num_philosophers', f'{philosophers}', '--optimal_order', '1'], num, csv_writer_vdo, vdo)
                run_test([exe, '--cores', f'{num}',
                          '--hunger', f'{hunger/2}', '--num_tables', '1', '--num_philosophers', f'{philosophers*2}', '--optimal_order', '1'], num, csv_writer_vdo200, vdo200)
                run_test(['taskset', '--cpu-list', f'0-{num-1}', exe, '--cores', f'{num}', '--pthread',
                          '--hunger', f'{hunger}', '--num_tables', '1', '--num_philosophers', f'{philosophers}', '1'], num, csv_writer_pds, pds)
                run_test(['taskset', '--cpu-list', f'0-{num-1}', exe, '--cores', f'{num}', '--pthread',
                          '--hunger', f'{hunger}', '--num_tables', '1', '--num_philosophers', f'{philosophers}', '1', '--optimal_order'], num, csv_writer_pdo, pdo)
                print('.', end='', flush=True)
            for num in min_cores:
                if num > os.cpu_count():
                    break
                run_test([exe, '--cores', f'{num}', '--test_no', '1',
                          '--hunger', f'{hunger}', '--num_tables', '1', '--num_philosophers', f'{philosophers}', '1'], num, csv_writer_vds, vds)
                print('.', end='', flush=True)
            print()