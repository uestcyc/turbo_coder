from itertools import permutations

import channel
import decode
import encode
import helpers
import interleave
import lookup_tables
import simcore

EBN0S = [0.01, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0]
make_permutation = lambda n, k=101: helpers.nth(permutations(range(n)), k)
LENGTH = 1000
R = [1, 10, 50, 50, 50, 50, 50]
I = 2


def pass_decode(sequence, ebn0):
    return list(helpers.demodulaten(sequence))


def map_decode(sequence, ebn0):
    rel = channel._decibel_to_ratio(ebn0) * 2
    return decode.binary_maximum_a_posteriori(lookup_tables.abrantes_convo213, sequence, rel, True)


def make_turbo_decode(k, table, interleaver):
    def turbo_decode(sequence, ebn0):
        # rel = channel._decibel_to_ratio(ebn0) * 2
        rel = ebn0 * 2
        return decode.turbo_decode(sequence, table, interleaver, k, rel)
    return turbo_decode


if __name__ == '__main__':
    configurations = [
        {
            "description": "Uncoded (10k frame)",
            "frame_length": LENGTH,
            "encoder": encode.PassEncoder(),
            "decoder_func": pass_decode,
            "ebn0s": EBN0S,
            "repeat_count": [10] * len(EBN0S),
        },
        {
            "description": "gzl212 (block; 4)",
            "frame_length": LENGTH,
            "encoder": encode.TurboEncoder(
                interleave.BlockInterleaver(50, 20),
                encode.RscEncoder(lookup_tables.gzl_rsc212)),
            "decoder_func": make_turbo_decode(
                4,
                lookup_tables.gzl_rsc,
                interleave.BlockInterleaver(50, 20)),
            "ebn0s": EBN0S,
            "repeat_count": R,
        },
        {
            "description": "gzl213 (block; 4)",
            "frame_length": LENGTH,
            "encoder": encode.TurboEncoder(
                interleave.BlockInterleaver(50, 20),
                encode.RscEncoder(lookup_tables.gzl_rsc213)),
            "decoder_func": make_turbo_decode(
                4,
                lookup_tables.gzl_rsc,
                interleave.BlockInterleaver(50, 20)),
            "ebn0s": EBN0S,
            "repeat_count": R,
        },
        {
            "description": "jordan_nichols (block; 4)",
            "frame_length": LENGTH,
            "encoder": encode.TurboEncoder(
                interleave.BlockInterleaver(50, 20),
                encode.RscEncoder(lookup_tables.jordan_nichols_rsc)),
            "decoder_func": make_turbo_decode(
                4,
                lookup_tables.jordan_nichols_rsc,
                interleave.BlockInterleaver(50, 20)),
            "ebn0s": EBN0S,
            "repeat_count": R,
        },
        # {
        #     "description": "jordan_nichols (block; 6)",
        #     "frame_length": LENGTH,
        #     "encoder": encode.TurboEncoder(
        #         interleave.BlockInterleaver(500, 20),
        #         encode.RscEncoder(lookup_tables.jordan_nichols_rsc)),
        #     "decoder_func": make_turbo_decode(
        #         6,
        #         lookup_tables.jordan_nichols_rsc,
        #         interleave.BlockInterleaver(500, 20)),
        #     "ebn0s": EBN0S,
        #     "repeat_count": R,
        # },
        # {
        #     "description": "jordan_nichols (block; 12)",
        #     "frame_length": LENGTH,
        #     "encoder": encode.TurboEncoder(
        #         interleave.BlockInterleaver(500, 20),
        #         encode.RscEncoder(lookup_tables.jordan_nichols_rsc)),
        #     "decoder_func": make_turbo_decode(
        #         12,
        #         lookup_tables.jordan_nichols_rsc,
        #         interleave.BlockInterleaver(500, 20)),
        #     "ebn0s": EBN0S,
        #     "repeat_count": R,
        # },
    ]

    simcore.verbose_exec(configurations)
