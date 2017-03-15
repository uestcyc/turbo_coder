from pprint import pprint
from itertools import permutations
import json
import math
import os
import time

import channel
import decode
import encode
import helpers
import interleave
import lookup_tables
import simcore

FRAME_LEN = 1000
EBN0S = [0.1, 0.2, 0.3, 0.6, 1.0, 2.0]
COUNT = 10

permutation = helpers.nth(permutations(range(FRAME_LEN)), 101)
make_permutation = lambda  len: helpers.nth(permutations(range(len)), 101)
interleaver = interleave.Interleaver(permutation)


def pass_decode(sequence, ebn0):
    return list(helpers.demodulaten(sequence))


def map_decode(sequence, ebn0):
    rel = channel._decibel_to_ratio(ebn0) * 2
    return decode.binary_maximum_a_posteriori(lookup_tables.abrantes_convo213, sequence, rel, True)


def make_turbo_decode(k):
    def turbo_decode(sequence, ebn0):
        rel = channel._decibel_to_ratio(ebn0) * 2
        return decode.turbo_decode(sequence, lookup_tables.gzl_rsc, interleaver, k, rel)
    return turbo_decode


def turbo_decode1(sequence, ebn0):
    rel = channel._decibel_to_ratio(ebn0) * 2
    return decode.turbo_decode(sequence, lookup_tables.gzl_rsc, interleaver, 1, rel)


if __name__ == '__main__':
    configurations = [
        {
            "description": "Uncoded",
            "frame_length": FRAME_LEN,
            "encoder": encode.PassEncoder(),
            "decoder_func": pass_decode,
            "ebn0s": EBN0S,
            "repeat_count": COUNT,
        },
        {
            "description": "MAP",
            "frame_length": FRAME_LEN,
            "encoder": encode.ConvoEncoder(lookup_tables.abrantes_convo213),
            "decoder_func": map_decode,
            "ebn0s": EBN0S,
            "repeat_count": COUNT,
        },
        {
            "description": "Turbo (1 iteration)",
            "frame_length": FRAME_LEN,
            "encoder": encode.TurboEncoder(interleaver, encode.RscEncoder(lookup_tables.gzl_rsc)),
            "decoder_func": turbo_decode1,
            "ebn0s": EBN0S,
            "repeat_count": COUNT,
        },
        {
            "description": "Turbo (2 iterations)",
            "frame_length": FRAME_LEN,
            "encoder": encode.TurboEncoder(interleaver, encode.RscEncoder(lookup_tables.gzl_rsc)),
            "decoder_func": make_turbo_decode(2),
            "ebn0s": EBN0S,
            "repeat_count": COUNT,
        },
        {
            "description": "Turbo (4 iterations)",
            "frame_length": FRAME_LEN,
            "encoder": encode.TurboEncoder(interleaver, encode.RscEncoder(lookup_tables.gzl_rsc)),
            "decoder_func": make_turbo_decode(4),
            "ebn0s": EBN0S,
            "repeat_count": COUNT,
        },
    ]

    simcore.verbose_exec(configurations)
