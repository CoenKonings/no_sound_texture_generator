class Instrument:
    """
    The instrument class is used to track what each player can do and is doing.
    """
    def __init__(self, name, pitch_range, max_note_length=1.5, can_solo=False):
        self.name = name
        self.pitch_range = pitch_range
        self.max_note_length = max_note_length
        self.can_solo = can_solo

    def __str__(self):
        return f'[Instrument: {self.name}]'


class InstrumentGroup:
    def __init__(self, groupname, instrumentname, pitch_range, max_note_length, size, number_start = 1):
        self.name = groupname
        self.instruments = [
            Instrument(
                instrumentname + " " + str(i + number_start),
                pitch_range,
                max_note_length,
                False
            ) for i in range(size)
        ]

    def __str__(self):
        return f'[Instrument group: {self.name}]'

    def print_instruments(self):
        for instrument in self.instruments:
            print(instrument)


class Dynamic:
    """
    The dynamic class is used to track the dynamics of a note, from ppp to fff,
    and gradual and sudden changes to dynamics.

    Dynamics from ppp to fff are stored as numbers 0 through 7. "Special"
    dynamics instructions, such as fp, are stored as negative numbers.

    Changes in dynamic are stored as -1, 0 or 1, where 0 denotes unchanging
    dynamics, -1 denotes a decrescendo and 1 denotes a crescendo.
    """
    PPP, PP, P, MP, MF, F, FF, FFF, FP = 0, 1, 2, 3, 4, 5, 6, 7, -1
    CRESC, DECRESC, STATIC = 1, -1, 0

    def __init__(self, dynamic, movementdir):
        self.dynamic = dynamic
        self.movementdir = movementdir


class Note:
    """
    A note has a pitch, a dynamic, and a group of instrument types. The change
    variable is used to morph the note between instrument groups.
    """
    def __init__(self, pitch, dynamic, instrument_groups):
        self.pitch = pitch
        self.dynamic = dynamic
        self.instrument_groups = instrument_groups
