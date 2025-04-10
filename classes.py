TIMESTEP = 0.125

class Instrument:
    """
    The instrument class is used to track what each player can do and is doing.
    """
    def __init__(self, name, pitch_range, max_note_length=1.5, can_solo=False):
        self.name = name
        self.pitch_range = pitch_range
        self.max_note_length = max_note_length
        self.can_solo = can_solo
        self.is_playing = False
        self.play_time = 0

    def __str__(self):
        return f'[Instrument: {self.name}]'

    def start_playing(self):
        self.is_playing = True
        print(self, "starts playing")

    def stop_playing(self):
        self.play_time = 0
        self.is_playing = False
        print(self, "stops playing")

    def step(self):
        self.play_time += TIMESTEP

        if self.is_playing and self.play_time > self.max_note_length:
            self.stop_playing()

    def can_start_playing(self, rest_time):
        return not self.is_playing and self.play_time > rest_time



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

        self.num_playing = 0

    def __str__(self):
        return f'[Instrument group: {self.name}]'

    def print_instruments(self):
        for instrument in self.instruments:
            print(instrument)

    def step(self, rest_time, max_playing):
        should_start_playing = self.num_playing < max_playing

        for instrument in self.instruments:
            if should_start_playing and instrument.can_start_playing(rest_time):
                instrument.start_playing()
                should_start_playing = False
                self.num_playing += 1

            instrument.step()



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


class Line:
    """
    A line is a note that is being sustained by multiple instrument(group)s.
    Its timbre morphs by individual instruments playing louder, quieter, or the
    note being passed between instrument(group)s.

    A line has a pitch, a dynamic, and a group of instrument types. The change
    rate variable is used to morph the line between instrument groups.
    """
    def __init__(
            self,
            pitch,
            dynamic,
            instrument_groups,
            max_playing=1,
            change_rate=0,
            rest_time=1
        ):
        self.pitch = pitch
        self.dynamic = dynamic
        self.instrument_groups = instrument_groups
        self.max_playing = max_playing
        self.change_rate = change_rate
        self.rest_time = rest_time

        self.instrument_group_index = 0

    def __str__(self):
        return f'[Line with pitch {self.pitch}]'

    def step(self):
        self.instrument_groups[
            self.instrument_group_index
        ].step(self.rest_time, self.max_playing)


class MusicEvent:
    """
    An event that occurs at a given time. Things like pitch changes, dynamics
    changes, etc. Action is a function to be executed at the given time.
    """
    def __init__(self, time, action, args):
        self.time = time
        self.action = action
        self.args = args


class Piece:
    """
    This class is used to generate the piece. It manages the timeline and
    ensures the music is executed correctly.
    """
    def __init__(self, tempo, time_signature, num_measures, events, lines):
        self.time = 0  # The time in measures
        self.tempo = tempo
        self.time_signature = time_signature
        self.num_measures = num_measures
        self.events = events
        self.lines = lines

    def start(self):

        while self.time < self.num_measures:
            self.time += TIMESTEP
            self.step()

            if self.time.is_integer():
                print("---------")

    def step(self):
        for line in self.lines:
            line.step()
