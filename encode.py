from itertools import chain

from helpers import multiplexed


class PassEncoder(object):
    def encoden(self, input_sequence):
        return list(input_sequence)


class ConvoEncoder(object):
    """A generic convolutional encoder class which encodes its input using a
    look-up table.
    """

    def encoden(self, input_sequence):
        return chain(*self.encode_sequence(input_sequence))

    def encode_sequence(self, input_sequence):
        """Encodes a sequence of input bits. Also brings encoder to its zero
        state by inputing 0 bits.Returns an iterator of output values
        (i.e. numbers or tuples of values 0 or 1).
        """
        for bit in input_sequence:
            yield self.encode(bit)

        while self.state != self._zero_state:
            yield self.encode(self._to_zero_state())

    def encode(self, input):
        """Encodes a single bit and returns the encoder's
        output (either a number or a tuple of values 0 or 1).

        Parameters:
        input -- either 0 or 1.
        """
        output, self.state = self.lookup_table[self.state][input]
        return output

    def _to_zero_state(self):
        """Returns the input required to bring the encoder to zero state.
        """
        return 0

    def __init__(self, lookup_table):
        """Initializes the encoder.

        Parameters:
        lookup_table -- a dict of dicts of tuples in the following structure:
            table[current_state][input] -> (output, next_state)
            input must be a number, output  must be a tuple of values 1 or 0.
            lookup_table can use any type of representation for its state
            (e.g. 0/1/2/3 or '00'/'01'/'10'/'11', etc.)
        """
        self.lookup_table = lookup_table
        # The first state in lookup_table is considered zero state:
        self._zero_state = lookup_table.keys()[0]
        self.state = self._zero_state


class RscEncoder(ConvoEncoder):
    """A basic Recursive Convolutional Encoder. It brings itself to zero state
    by summing the values of its state registers. State values are expected to
    be numeric values.
    """

    def _to_zero_state(self):
        """Returns the input required to bring the encoder to zero state. It is
        determined by converting state value (a number) to binary system and
        modulo 2 summing its binary digits.
        """
        return sum(map(int, bin(self.state)[2:])) % 2


class TurboEncoder(object):
    """A turbo encoder, which uses two inner convolutional encoders
    separated with an interleaver.
    """

    def encoden(self, input_sequence):
        return self.encode_sequence(input_sequence)

    def encode_sequence(self, input_sequence):
        """Encodes the input sequence as described below:
        1. Encode the input with self.inner_encoder[0]
        2. Interleave the input with self.interleaver
        3. Encode the interleaved sequence with self.inner_encoder[1]
        4. Return multiplexed input and both of the encoders output.
        """
        input_sequence = list(input_sequence)
        output0 = self._consituent_encode(self.inner_encoders[0], input_sequence)

        interleaved_sequence = self.interleaver.interleave(input_sequence)
        output1 = self._consituent_encode(self.inner_encoders[1], interleaved_sequence)

        return multiplexed(input_sequence, output0, output1)

    def _consituent_encode(self, encoder, input_sequence):
        output = encoder.encode_sequence(input_sequence)

        output = [i[1:] for i in output]    # Assumes first output bit is systematic
        output = list(chain(*output))

        return output

    def __init__(self, interleaver, inner_encoder, inner_encoder2=None):
        """Initializes the turbo encoder.

        Parameters:
            interleaver -- an interleave.Interleaver object. Its frame size must
                be (and is) equal to the turbo encoder's frame size.
            inner_encoder -- the constituent inner encoder of the turbo code. If
                inner_encoder2 parameter is omitted, both of the
                encoders are used the same.
        """
        self.interleaver = interleaver
        self.inner_encoders = [inner_encoder] * 2
        if inner_encoder2:
            self.inner_encoders[1] = inner_encoder2
