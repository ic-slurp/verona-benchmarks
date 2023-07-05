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
    parser.add_argument('-o', default='out.csv', help='outfile location')
    args = parser.parse_args()
    return args


def run_test(args, num, csv, file):
    start = time.time()
    subprocess.run(args, check=True)
    end = time.time()
    csv.writerow((num, end - start))
    file.flush()


def make_csv(file):
    csv_file = csv.writer(file)
    csv_file.writerow(['cores', 'time'])
    return csv_file


if __name__ == '__main__':
    args = getopts()
    # Dump it as a csv file so we can use it for pgfplots
    with open('verona_dining_opt.csv', 'w') as vdo,\
         open('verona_dining_seq.csv', 'w') as vds,\
         open('pthread_dining_seq.csv', 'w') as pds,\
         open('pthread_dining_opt.csv', 'w') as pdo,\
         open('verona_dining_opt_200.csv', 'w') as vdo200:
        csv_writer_vdo = make_csv(vdo)
        csv_writer_vds = make_csv(vds)
        csv_writer_pds = make_csv(pds)
        csv_writer_pdo = make_csv(pdo)
        csv_writer_vdo200 = make_csv(vdo200)
        philosophers = 100
        hunger = 500
        for exp in range(args.repeats):
            cores = range(1, os.cpu_count() + 1)
            min_cores = [1, 2, 3, 4, 5, 10, 20, 40, 60, 72]
            for num in cores:
                print(f'{num} cpus', end='', flush=True)
                run_test(['./perf-con-dining_phil', '--cores', f'{num}',
                          '--hunger', f'{hunger}', '--num_tables', '1', '--num_philosophers', f'{philosophers}', '--optimal_order', '1'], num, csv_writer_vdo, vdo)
                run_test(['./perf-con-dining_phil', '--cores', f'{num}',
                          '--hunger', f'{hunger/2}', '--num_tables', '1', '--num_philosophers', f'{philosophers*2}', '--optimal_order', '1'], num, csv_writer_vdo200, vdo200)
                run_test(['taskset', '--cpu-list', f'0-{num-1}', './perf-con-dining_phil', '--cores', f'{num}', '--pthread',
                          '--hunger', f'{hunger}', '--num_tables', '1', '--num_philosophers', f'{philosophers}', '1'], num, csv_writer_pds, pds)
                run_test(['taskset', '--cpu-list', f'0-{num-1}', './perf-con-dining_phil', '--cores', f'{num}', '--pthread',
                          '--hunger', f'{hunger}', '--num_tables', '1', '--num_philosophers', f'{philosophers}', '1', '--optimal_order'], num, csv_writer_pdo, pdo)
            for num in min_cores:
                print(f'{num} cpus', end='', flush=True)
                run_test(['./perf-con-dining_phil', '--cores', f'{num}', '--test_no', '1',
                          '--hunger', f'{hunger}', '--num_tables', '1', '--num_philosophers', f'{philosophers}', '1'], num, csv_writer_vds, vds)
                print('.', end='', flush=True)
            print('done repeat')
