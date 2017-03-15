from itertools import permutations
import json

import channel
import decode
import encode
import helpers
import interleave
import lookup_tables
import simcore

EBN0S = [0.5, 1]
make_permutation = lambda n, k=9999: helpers.nth(permutations(range(n)), k)
LENGTH = 10000
R = [1000, 1000]


with open(r"D:\Programavimas\turbo\runs\perm10k.txt", "r") as f:
    permutation = json.load(f)


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
            "description": "jordan_nichols (2, slightly random)",
            "frame_length": LENGTH,
            "encoder": encode.TurboEncoder(
                interleave.Interleaver(make_permutation(LENGTH)),
                encode.RscEncoder(lookup_tables.jordan_nichols_rsc)),
            "decoder_func": make_turbo_decode(
                2,
                lookup_tables.jordan_nichols_rsc,
                interleave.Interleaver(make_permutation(LENGTH))),
            "ebn0s": EBN0S,
            "repeat_count": [10, 10],
        },
        {
            "description": "jordan_nichols_rsc (2, random)",
            "frame_length": LENGTH,
            "encoder": encode.TurboEncoder(
                interleave.Interleaver(permutation),
                encode.RscEncoder(lookup_tables.jordan_nichols_rsc)),
            "decoder_func": make_turbo_decode(
                2,
                lookup_tables.jordan_nichols_rsc,
                interleave.Interleaver(permutation)),
            "ebn0s": EBN0S,
            "repeat_count": R,
        },
        # {
        #     "description": "jordan_nichols_rsc (4, random)",
        #     "frame_length": LENGTH,
        #     "encoder": encode.TurboEncoder(
        #         interleave.Interleaver(permutation),
        #         encode.RscEncoder(lookup_tables.jordan_nichols_rsc)),
        #     "decoder_func": make_turbo_decode(
        #         4,
        #         lookup_tables.jordan_nichols_rsc,
        #         interleave.Interleaver(permutation)),
        #     "ebn0s": EBN0S,
        #     "repeat_count": R,
        # },
        # {
        #     "description": "jordan_nichols_rsc (8)",
        #     "frame_length": LENGTH,
        #     "encoder": encode.TurboEncoder(
        #         interleave.Interleaver(permutation),
        #         encode.RscEncoder(lookup_tables.jordan_nichols_rsc)),
        #     "decoder_func": make_turbo_decode(
        #         8,
        #         lookup_tables.jordan_nichols_rsc,
        #         interleave.Interleaver(make_permutation(LENGTH))),
        #     "ebn0s": EBN0S,
        #     "repeat_count": R,
        # },
        # {
        #     "description": "jordan_nichols_rsc (16)",
        #     "frame_length": LENGTH,
        #     "encoder": encode.TurboEncoder(
        #         interleave.Interleaver(make_permutation(LENGTH)),
        #         encode.RscEncoder(lookup_tables.jordan_nichols_rsc)),
        #     "decoder_func": make_turbo_decode(
        #         16,
        #         lookup_tables.jordan_nichols_rsc,
        #         interleave.Interleaver(make_permutation(LENGTH))),
        #     "ebn0s": EBN0S,
        #     "repeat_count": R,
        # },
    ]

    simcore.verbose_exec(configurations, 4)
