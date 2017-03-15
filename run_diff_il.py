from itertools import permutations
import json

import channel
import decode
import encode
import helpers
import interleave
import lookup_tables
import simcore

EBN0S = [-4, -3, -2, -1, 0]
make_permutation = lambda n, k=9999: helpers.nth(permutations(range(n)), k)
LENGTH = 1000

with open(r"D:\Programavimas\turbo\runs\perm1k.txt", "r") as f:
    better_permutation = json.load(f)


def pass_decode(sequence, ebn0):
    return list(helpers.demodulaten(sequence))


def map_decode(sequence, ebn0):
    rel = channel._decibel_to_ratio(ebn0) * 2
    return decode.binary_maximum_a_posteriori(lookup_tables.abrantes_convo213, sequence, rel, True)


def make_turbo_decode(k, table, interleaver):
    def turbo_decode(sequence, ebn0):
        rel = channel._decibel_to_ratio(ebn0) * 2
        # rel = ebn0 * 2
        return decode.turbo_decode(sequence, table, interleaver, k, rel)
    return turbo_decode


if __name__ == '__main__':
    configurations = [
        {
            "description": "gzl_rsc (almost none)",
            "frame_length": LENGTH,
            "encoder": encode.TurboEncoder(
                interleave.Interleaver(make_permutation(LENGTH)),
                encode.RscEncoder(lookup_tables.gzl_rsc)),
            "decoder_func": make_turbo_decode(
                2,
                lookup_tables.gzl_rsc,
                interleave.Interleaver(make_permutation(LENGTH))),
            "ebn0s": EBN0S,
            "repeat_count": [10, 10, 10, 10, 100],
        },
        {
            "description": "gzl_rsc (random)",
            "frame_length": LENGTH,
            "encoder": encode.TurboEncoder(
                interleave.Interleaver(better_permutation),
                encode.RscEncoder(lookup_tables.gzl_rsc)),
            "decoder_func": make_turbo_decode(
                2,
                lookup_tables.gzl_rsc,
                interleave.Interleaver(better_permutation)),
            "ebn0s": EBN0S,
            "repeat_count": [10, 10, 500, 5000, 5000],
        },
        {
            "description": "gzl_rsc (block)",
            "frame_length": LENGTH,
            "encoder": encode.TurboEncoder(
                interleave.BlockInterleaver(50, 20),
                encode.RscEncoder(lookup_tables.gzl_rsc)),
            "decoder_func": make_turbo_decode(
                2,
                lookup_tables.gzl_rsc,
                interleave.BlockInterleaver(50, 20)),
            "ebn0s": EBN0S,
            "repeat_count": [10, 10, 500, 5000, 5000],
        },
    ]

    simcore.verbose_exec(configurations, 4)
