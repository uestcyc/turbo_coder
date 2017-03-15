from __future__ import division
from itertools import chain, islice, izip, izip_longest
from types import GeneratorType
import collections
import math
import random


def nested_to_string(iterable):
    """Converts a nested iterable to a string.
    """
    if isinstance(iterable, collections.Iterable):
        return "".join([nested_to_string(item) for item in iterable])
    else:
        return str(iterable)


def modulate(i):
    """Converts a binary value to voltage value: 1 to +1, 0 to -1,
    None and everything else to 0.
    """
    if i == 0:
        return -1
    elif i == 1:
        return 1
    else:
        return 0


def modulaten(data):
    """Converts a binary sequence to voltage values: 1 to +1, 0 to -1,
    None and everything else to 0.
    Returns a generator.
    """
    for i in data:
        yield modulate(i)


def demodulaten(data):
    """Converts a voltage value to binary: +1 to 1, -1 to 0,
    None and everything else to 0.
    Returns a generator.
    """
    mapping = {-1: 0, +1: 1}
    for i in data:
        yield mapping.get(math.copysign(1, i), 0)


def modulate_table(lookup_table):
    modulated_table = {}
    for state in lookup_table:
        modulated_table[state] = {}
        for i in (0, 1):
            output = tuple(modulaten(lookup_table[state][i][0]))
            next_state = lookup_table[state][i][1]
            modulated_table[state][i] = (output, next_state)

    return modulated_table

def to_hard_values(data):
    """Applies a hard decision on the real value, e.g. -0.5 to -1,
    +0.2 to +1, 0 to 0.
    Returns a generator.
    """
    for value in data:
        if value == 0:
            yield 0
        else:
            yield int(math.copysign(1, value))


def invert_lookup_table(lookup_table):
    """Inverts the lookup table in a manner to tell from what states it can be
    transitioned to a given state.

    Returns a dict of lists.
    """
    state_count = len(lookup_table)

    inverted = [None] * state_count

    for state in xrange(state_count):
        inverted[state] = list(_invert_state(lookup_table, state))

    return inverted


def _invert_state(lookup_table, goal_state):
    """Given a lookup table, returns a generator of states that transition to
    the given state.
    """
    for state in lookup_table:
        for input_bit in lookup_table[state]:
            if lookup_table[state][input_bit][1] == goal_state:
                yield state


def hamming_distance(list_a, list_b):
    """Calculates the Hamming distance between two sequences.
    Hamming distance between two strings of equal length is the number of
    positions at which the corresponding symbols are different.
    """
    if type(list_a) == GeneratorType or type(list_b) == GeneratorType:
        raise TypeError("Generators not supported.")    # An empty generator causes zero Hamming distance
    if not list_a or not list_b:
        raise ValueError("Empty sequence.")

    diff_count = 0
    for a, b in izip(list_a, list_b):
        if a != b:
            diff_count += 1

    return diff_count


def generate_random(length):    # pragma: no cover
    """Generates a list of random values of ones and zeroes.
    """
    values = (0, 1)
    return (random.choice(values) for i in xrange(length))


def normalize(iterable):
    """Returns a list of normalized values.
    """
    n = sum(iterable)
    return [i / n for i in iterable]


def normalizen(iterables):
    """Returns a generator of normalized iterables.
    """
    for iterable in iterables:
        yield normalize(iterable)


def normalize_dicts(dicts):
    """Normalizes a list of dicts.
    """
    total = sum([sum(d.values()) for d in dicts])

    normalized_dicts = []
    for d in dicts:
        new_d = {}
        for key, value in d.items():
            new_d[key] = value / total

        normalized_dicts.append(new_d)

    return normalized_dicts


def multiplexed(*sequences):
    """Returns a list of multiplexed iterables. If iterables are of uneven
    length, missing values are filled in with None.
    """
    return list(chain(*izip_longest(*sequences, fillvalue=None)))


def nth(iterable, n, default=None):
    "Returns the nth item or a default value"
    return next(islice(iterable, n, None), default)
