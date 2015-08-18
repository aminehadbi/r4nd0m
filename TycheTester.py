
import os
import csv
import numpy
import pandas

from SourceCode.Generators import Generators
from SourceCode.BinaryFrame import BinaryFrame
from SourceCode.RandomnessTests import RandomnessTester
from SourceCode.DataDownloader import QuandlInterface, Argument


# TODO: Add better comments to this file
# TODO: Identify more markets to include in study
# TODO: Move Random Number Generators into Separate Class


def setup_environment():
    token = ""
    try:
        with open(os.path.join("MetaData", ".private.csv"), "r") as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in reader:
                if row[0] == "HTTP" and row[1] != "None":
                    os.environ['HTTP_PROXY'] = row[1]
                if row[0] == "HTTPS" and row[1] != "None":
                    os.environ['HTTPS_PROXY'] = row[1]
                if row[0] == "Token" and row[1] != "None":
                    token = row[1]
    except FileNotFoundError:
        print("No private settings found")
    return token


def construct_binary_frame(data_sets, method, token, start, end, years_per_block):
    downloader = QuandlInterface(token)
    data_file = pandas.read_csv(data_sets)
    data_sets = list(data_file["ID"])
    drop_columns = list(data_file["DROP"])
    data_prefix = ""
    transform = "rdiff"
    start_date = str(start) + "-01-01"
    end_date = str(end) + "-01-01"
    my_arguments = []
    for i in range(len(data_sets)):
        drop = drop_columns[i].split('#')
        if drop == "":
            drop = []
        my_arguments.append(Argument(data_sets[i], start_date, end_date, data_prefix, drop, transform))
    data_frame_full = downloader.get_data_sets(my_arguments)
    binary_frame = BinaryFrame(data_frame_full, start, end, years_per_block)
    binary_frame.convert(method)
    return binary_frame


def run_experiments(data_sets, block_sizes, q_sizes, methods, start, end, years_per_block):
    breaker = "".zfill(200)
    breaker = breaker.replace('0', '*')
    for method in methods:
        print("\n" + breaker)
        print("METHOD =", method.upper())

        length = 256 * (end - start)
        gen = Generators(length)
        prng = gen.crypto_integer()

        prng_data = pandas.DataFrame(numpy.array(prng))
        prng_data.columns = ["Mersenne"]
        prng_binary_frame = BinaryFrame(prng_data, start, end, years_per_block)
        prng_binary_frame.convert(method, convert=False)
        # method, real_data, start_year, end_year, block_size
        rng_tester = RandomnessTester(prng_binary_frame, method, False, 00, 00)
        rng_tester.run_test_suite(block_sizes, q_sizes)

        nrand = numpy.empty(length)
        for i in range(length):
            nrand[i] = (i % 10) / 10
        nrand -= numpy.mean(nrand)
        nrand_data = pandas.DataFrame(numpy.array(nrand))
        nrand_data.columns = ["Deterministic"]
        nrand_binary_frame = BinaryFrame(nrand_data, start, end, years_per_block)
        nrand_binary_frame.convert(method, convert=True)
        rng_tester = RandomnessTester(nrand_binary_frame, method, False, 00, 00)
        rng_tester.run_test_suite(block_sizes, q_sizes)

        t = setup_environment()
        my_binary_frame = construct_binary_frame(data_sets, method, t, start, end, years_per_block)
        rng_tester = RandomnessTester(my_binary_frame, method, True, start, end)
        # my_binary_frame = construct_long_binary_frame(method, stream_length)
        rng_tester.run_test_suite(block_sizes, q_sizes)
    print("\n" + breaker)


def clean_up():
    try:
        os.remove("authtoken.p")
    except FileNotFoundError:
        pass


if __name__ == '__main__':
    m = ["discretize"]
    # , "convert basis point", "convert floating point"]
    run_experiments(os.path.join("MetaData", ".1900 plus.csv"), 128, 16, m, 1900, 2015, 10.0)
    run_experiments(os.path.join("MetaData", ".1950 plus.csv"), 128, 16, m, 1950, 2015, 10.0)
    run_experiments(os.path.join("MetaData", ".1960 plus.csv"), 128, 16, m, 1960, 2015, 10.0)
    run_experiments(os.path.join("MetaData", ".1970 plus.csv"), 128, 16, m, 1970, 2015, 10.0)
    run_experiments(os.path.join("MetaData", ".1990 plus.csv"), 128, 16, m, 1990, 2015, 10.0)
    clean_up()