from __future__ import division
import math
from itertools import izip

import channel
import encode
import helpers
import interleave


def calc_transition_metrics(
        lookup_table,
        noisy_sequence,
        channel_reliability,
        normalize=False,
        extrinsic=None):
    """Calculates transition (gamma) metrics.

    Parameters:
    lookup_table -- a dict of dicts of tuples in the following structure:
        table[current_state][input] -> (output, next_state).
    noisy_sequence -- sequence that is being decoded.
    channel_reliability -- L_c = 4 * R * (E_b / N_0), where R is code rate.
    normalize -- specifies whether the metrics should be normalized.
    extrinsic -- extrinsic information, a list of floats

    Returns a list of lists of dicts in the following structure:
        gamma[trellis_position][state][next_state] -> float
    """
    output_len = len(lookup_table[0][0][0])
    trellis_len = len(noisy_sequence) // output_len
    state_count = len(lookup_table)

    modulated_table = helpers.modulate_table(lookup_table)

    if not extrinsic:
        extrinsic = [0] * trellis_len
    else:
        extrinsic += [0] * (trellis_len - len(extrinsic))

    transition_metrics = [None] * trellis_len

    for k in xrange(trellis_len):
        transition_metrics[k] = [None] * state_count
        noisy_output = noisy_sequence[k * output_len:(k + 1) * output_len]

        for s in xrange(state_count):
            transition_metrics[k][s] = {}

            for i in (0, 1):
                exp1 = math.exp(helpers.modulate(i) * extrinsic[k] / 2)

                state_output, next_state = modulated_table[s][i]

                a = (channel_reliability / 2)
                b = sum(c * y for c, y in izip(state_output, noisy_output))    # FIXME got a MemoryError here once
                exp2 = math.exp(a * b)

                transition_metrics[k][s][next_state] = exp1 * exp2

        # if normalize:     # Commented out for performance
        #     transition_metrics[k] = helpers.normalize_dicts(transition_metrics[k])

    return transition_metrics


def calc_forward_metrics(lookup_table, transition_metrics, normalize=False):
    """Calculates forward (alpha) metrics.

    Parameters:
    lookup_table -- a dict of dicts of tuples in the following structure:
        table[current_state][input] -> (output, next_state).
    transition_metrics -- a list of list of lists in the following structure:
        gamma[trellis_position][state][input] -> float
    normalize -- specifies whether the metrics should be normalized.

    Returns a list of lists in the following structure:
        alpha[trellis_position][state] -> float
    """
    trellis_len = len(transition_metrics)
    state_count = len(lookup_table)

    forward_metrics = [None] * (trellis_len + 1)

    inverted_table = helpers.invert_lookup_table(lookup_table)

    # Coding always starts in zero state:
    forward_metrics[0] = [0] * state_count
    forward_metrics[0][0] = 1

    for k in xrange(1, len(forward_metrics)):
        forward_metrics[k] = [None] * state_count

        for state in xrange(state_count):
            prev_states = inverted_table[state]

            alpha = 0
            for prev_state in prev_states:
                alpha += forward_metrics[k - 1][prev_state] * \
                    transition_metrics[k - 1][prev_state][state]

            forward_metrics[k][state] = alpha

        if normalize:
            forward_metrics[k] = helpers.normalize(forward_metrics[k])

    return forward_metrics


def calc_backward_metrics(lookup_table, transition_metrics, normalize=False):
    """Calculates backward (beta) metrics.

    Parameters:
    lookup_table -- a dict of dicts of tuples in the following structure:
        table[current_state][input] -> (output, next_state).
    transition_metrics -- a list of list of lists in the following structure:
        gamma[trellis_position][state][input] -> float
    normalize -- specifies whether the metrics should be normalized.

    Returns a list of lists in the following structure:
        beta[trellis_position][state] -> float
    """
    trellis_len = len(transition_metrics)
    state_count = len(lookup_table)

    backward_metrics = [None] * (trellis_len + 1)

    # Coding always ends in zero state:
    backward_metrics[-1] = [0] * state_count
    backward_metrics[-1][0] = 1

    for k in xrange(len(backward_metrics) - 2, -1, -1):
        backward_metrics[k] = [None] * state_count

        for state in xrange(state_count):
            next_states = tuple(lookup_table[state][i][1] for i in (0, 1))          # FIXME MemoryError

            beta = 0
            for next_state in next_states:
                beta += backward_metrics[k + 1][next_state] * \
                    transition_metrics[k][state][next_state]

            backward_metrics[k][state] = beta

        if normalize:
            backward_metrics[k] = helpers.normalize(backward_metrics[k])

    return backward_metrics


def maximum_a_posteriori(
        lookup_table,
        noisy_sequence,
        channel_reliability,
        normalize=False,
        extrinsic=None):
    """Calculates log-likelihood ratios using
    maximum a posteriori (MAP) algorithm.

    Parameters:
    lookup_table -- a dict of dicts of tuples in the following structure:
        table[current_state][input] -> (output, next_state).
    noisy_sequence -- sequence that is being decoded.
    channel_reliability -- L_c = 4 * R * (E_b / N_0), where R is code rate.
    normalize -- specifies whether the metrics should be normalized.
    extrinsic -- extrinsic information, a list of floats

    Returns a list of floats.
    """
    gammas = calc_transition_metrics(lookup_table, noisy_sequence,
                                     channel_reliability, normalize, extrinsic)
    alphas = calc_forward_metrics(lookup_table, gammas, normalize)
    betas = calc_backward_metrics(lookup_table, gammas, normalize)

    llrs = [0] * len(gammas)

    for k in range(len(llrs)):
        sums = [0, 0]

        for state in lookup_table:
            for i in (0, 1):
                next_state = lookup_table[state][i][1]

                sums[i] += alphas[k][state] * \
                    gammas[k][state][next_state] * \
                    betas[k+1][next_state]

        llrs[k] = math.log(sums[1] / sums[0]) if sums[0] != 0 and sums[1] != 0 else -float("inf")  # TODO cover the case where sums[0] == 0

    return llrs


def binary_maximum_a_posteriori(
        lookup_table,
        noisy_sequence,
        channel_reliability,
        normalize=False):
    """Calculates hard decoded values (0 or 1) using
    maximum a posteriori (MAP) algorithm.

    Parameters:
    lookup_table -- a dict of dicts of tuples in the following structure:
        table[current_state][input] -> (output, next_state).
    noisy_sequence -- sequence that is being decoded.
    channel_reliability -- L_c = 4 * R * (E_b / N_0), where R is code rate.
    normalize -- specifies whether the metrics should be normalized.

    Returns a list of integers 0 or 1.
    """
    llrs = maximum_a_posteriori(lookup_table, noisy_sequence,
                                channel_reliability, normalize)
    return list(helpers.demodulaten(helpers.to_hard_values(llrs)))


def decompose(sequence, r, encoder_count):
    """Demultiplexes the sequence to one systematic and two code sequences,
    e.g. ABCABCABC -> AAA, [BBB, CCC]

    Parameters:
    sequence -- the "flat" input sequence of bit values
    r -- length of code output
    coder_count -- number of constituent encoders
    """
    output_len = encoder_count * r + 1
    if len(sequence) % output_len != 0:
        raise ValueError("Sequence is of improper length.")

    systematic = []
    codes = [[] for i in range(encoder_count)]

    for chunk in range(len(sequence) // output_len):
        systematic.append(sequence[chunk * output_len])
        for i in range(encoder_count):
            start = chunk * output_len + i * r + 1
            end = chunk * output_len + (i + 1) * r + 1
            codes[i] += sequence[start:end]

    return systematic, codes


def turbo_decode(noisy_sequence, lookup_table, interleaver,
                 iteration_count, channel_reliability):
    frame_length = len(interleaver)
    output_len = len(lookup_table[0][0][0])

    systematic, codes = decompose(noisy_sequence, output_len - 1, 2)
    isystematic = interleaver.interleave(systematic[:frame_length])
    isystematic += [0] * (len(systematic) - len(isystematic))

    extrinsic = [0] * frame_length

    for i in xrange(iteration_count):
        llrs, extrinsic = turbo_constituent_decode(lookup_table, systematic, codes[0], channel_reliability, extrinsic)
        extrinsic = interleaver.interleave(extrinsic[:frame_length])

        llrs, extrinsic = turbo_constituent_decode(lookup_table, isystematic, codes[1], channel_reliability, extrinsic)
        extrinsic = interleaver.deinterleave(extrinsic[:frame_length])

    return list(helpers.demodulaten(interleaver.deinterleave(llrs[:frame_length])))


def turbo_constituent_decode(
        lookup_table,
        systematic,
        code,
        channel_reliability,
        extrinsic):
    noisy_seq = helpers.multiplexed(systematic, code)

    llrs = maximum_a_posteriori(lookup_table, noisy_seq, channel_reliability,
                                True, extrinsic)
    extrinsic_out = [llr - extr - channel_reliability * syst for llr, extr, syst in izip(llrs, extrinsic, systematic)]

    return llrs, extrinsic_out


if __name__ == '__main__':    # pragma: no cover
    rsc_table = {
        0: {0: ((0, 0), 0), 1: ((1, 1), 2)},
        1: {0: ((0, 0), 2), 1: ((1, 1), 0)},
        2: {0: ((0, 1), 3), 1: ((1, 0), 1)},
        3: {0: ((0, 1), 1), 1: ((1, 0), 3)},
    }
    permutation = range(9, -1, -1)
    il = interleave.Interleaver(permutation)
    ie = encode.RscEncoder(rsc_table)
    turbo_encoder = encode.TurboEncoder(il, ie)

    data = map(int, "0000000001")
    encoded = turbo_encoder.encode_sequence(data)
    modulated = list(helpers.modulaten(encoded))
    noisy = list(channel.transmit_awgn(modulated, 0.3))
    decoded = turbo_decode(noisy, rsc_table, il, 10, 2)

    print data
    print decoded
