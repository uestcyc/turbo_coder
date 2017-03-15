class Interleaver(object):
    """A generic interleaver class that uses a permutation table to
    interleave a sequence of bits.
    """

    def interleave(self, sequence):
        return self._interleave(self.permutation, sequence)

    def deinterleave(self, sequence):
        return self._interleave(self.inverted_permutation, sequence)

    def _interleave(self, permutation, sequence):
        """Returns a list representing the interleaved sequence.

        Parameters:
        permutation -- the permutation describing interleaving method.
        sequence -- an iterable to interleave.
        """
        if len(sequence) != len(permutation):
            raise ValueError("Sequence length is not equal to frame length.")

        interleaved_sequence = [None] * len(sequence)
        for i, value in zip(permutation, sequence):
            interleaved_sequence[i] = value

        return interleaved_sequence

    @classmethod
    def _is_permutation(self, iterable):
        """Checks if a given iterable is a permutation of numbers from 0 to N+1.
        Returns boolean.
        """
        return sorted(iterable) == range(len(iterable))

    @classmethod
    def _invert_permutation(self, permutation):
        inverted_permutation = [None] * len(permutation)
        for i, position in enumerate(permutation):
            inverted_permutation[position] = i

        return inverted_permutation

    def __init__(self, permutation):
        """Initializes the interleaver.

        Parameters:
        permutation -- an iterable of number from 0 to N where N+1 is the size
            of frame and the interleaver.
        """
        if not self._is_permutation(permutation):
            raise ValueError("Parameter permutation is not valid.")

        self.permutation = permutation
        self.inverted_permutation = self._invert_permutation(permutation)

    def __len__(self):
        return len(self.permutation)


class BlockInterleaver(Interleaver):
    @classmethod
    def _create_block_permutation(self, w, h):
        positions = xrange(w * h)
        permutation = [None] * len(positions)
        for i, value in enumerate(positions):
            permutation[i // h + w * (i % h)] = value

        return permutation

    def __init__(self, width, height):
        self.width = width
        self.height = height

        block_permutation = self._create_block_permutation(self.width, self.height)
        super(BlockInterleaver, self).__init__(block_permutation)

    def __len__(self):
        return self.width * self.height
