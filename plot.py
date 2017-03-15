import itertools
import json
import os
import sys

import matplotlib.pyplot as plt


def parse_json(json_string):
    """
    """
    data = json.loads(json_string)
    return data


def plot_ber(ber_curve_list):
    """Plots given BER curves.

    Parameters:
    ber_curve_list -- a list of tuples (snr_list, ber_list, labels) where
        snr_list is a list of SNR points (horizontal axis) and
        ber_list is a list of BER points (vertical axis).
    """
    marker = itertools.cycle("sd^ovD")
    style = lambda: "-" + marker.next()

    for snr_list, ber_list, label in ber_curve_list:
        plt.semilogy(snr_list, ber_list, style(), label=label)

    plt.xlabel('Eb/N0 (dB)')
    plt.ylabel('BER')
    plt.grid(True, which="both")
    plt.legend()

    plt.show()


def parse_file(path):
    with open(path, "r") as source:
        json_string = source.read()
    return parse_json(json_string)


def find_file(id):
    out_folder = os.path.abspath("out")
    file_names = os.listdir(out_folder)
    file_names = filter(lambda x: x.startswith(id), file_names)
    if file_names:
        return os.path.join(os.path.abspath("out"), file_names[0])

    return id

if __name__ == '__main__':
    path = find_file(sys.argv[1])

    data = parse_file(path)

    ber_curves = []
    for result in data["results"]:
        ber_curves.append((result["ebn0s"], result["bers"], result["description"]))

    try:
        plot_ber(ber_curves)
    except KeyboardInterrupt:
        pass
