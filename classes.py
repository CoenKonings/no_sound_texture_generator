import math


TIMESTEP = 0.125


class Dynamic:
    """
    The dynamic event class is used only to organize a set of constants for
    readability.

    Dynamics from ppp to fff are stored as numbers 0 through 7. "Special"
    dynamics instructions, such as fp, are stored as negative numbers.

    Changes in dynamic are stored as -1, 0 or 1, where 0 denotes no movement,
    -1 denotes a decrescendo and 1 denotes a crescendo.
    """
    PPP, PP, P, MP, MF, F, FF, FFF = 0, 1, 2, 3, 4, 5, 6, 7
    CRESC, DECRESC, STATIC = 1, -1, 0

    def __init__(self, value, parent):
        self.value = value
        self.is_changing = False
        self.target_dynamic = None
        self.start_dynamic = None
        self.parent = parent
        self.time_to_reach_target = 0

    def __str__(self):
        dynamic_dict = {
            0: "ppp",
            1: "pp",
            2: "p",
            3: "mp",
            4: "mf",
            5: "f",
            6: "ff",
            7: "fff"
        }
        return f'[Dynamic {dynamic_dict[self.value]} {
            "moving towards " + dynamic_dict[self.target_dynamic] if self.is_changing else "static"
        }]'

    def start_change(self, target, time):
        self.is_changing = True
        self.target_dynamic = target
        self.start_dynamic = self.value
        self.time_to_reach_target = time

    def stop_change(self):
        self.is_changing = False
        self.target_dynamic = None
        self.start_dynamic = None
        self.time_to_reach_target = 0
        print(self.parent, "reached target dynamic", end="")

    def step(self):
        if self.value == self.target_dynamic:
            self.stop_change()
            return

        if self.is_changing:
            num_steps = self.time_to_reach_target / TIMESTEP
            dynamic_step = (self.target_dynamic - self.start_dynamic) / num_steps
            self.value += dynamic_step


class Instrument:
    """
    The instrument class is used to track what each player can do and is doing.
    """
    def __init__(
            self,
            name,
            pitch_range,
            instrument_group=None,
            max_note_length=1.5,
            can_solo=False
        ):
        self.name = name
        self.pitch_range = pitch_range
        self.max_note_length = max_note_length
        self.can_solo = can_solo
        self.is_playing = False
        self.is_stopping = False
        self.instrument_group = instrument_group
        self.play_time = None
        self.dynamic = None

    def __str__(self):
        return f'[Instrument: {self.name}]'

    def start_playing(self):
        self.is_playing = True
        self.play_time = 0
        self.instrument_group.num_playing += 1

        if not self.dynamic:
            self.dynamic = Dynamic(Dynamic.PPP, self)

        self.dynamic.start_change(
            self.instrument_group.texture.dynamic.value,
            self.instrument_group.texture.fade_time
        )

        print(
            self,
            "starts playing on",
            self.dynamic,
            end=""
        )

    def stop_playing(self, skip_stopping_process=False):
        if not skip_stopping_process:
            self.is_stopping = True
            self.dynamic.start_change(
                Dynamic.PPP,
                self.instrument_group.texture.fade_time
            )

            print(self, "is stopping with", self.dynamic, end="")
        else:
            self.is_stopping = False
            self.is_playing = False
            print(self, "has stopped", end="")

        self.instrument_group.num_playing -= 1

    def should_stop(self):
        max_play_time = self.max_note_length - self.instrument_group.texture.fade_time
        return (
            self.is_playing and
            self.play_time > max_play_time and
            not self.is_stopping
        )

    def step(self):
        if self.play_time is not None:
            self.play_time += TIMESTEP

        if self.is_stopping and self.play_time > self.max_note_length:
            self.is_stopping = False
            self.is_playing = False
            self.play_time = 0
            print(self, "has stopped", end="")

        if self.should_stop():
            self.stop_playing()

        # Dynamic is none if instrument has not started playing yet.
        if self.dynamic is not None:
            self.dynamic.step()


    def can_start_playing(self):
        # If the instrument is not playing, play_time tracks the length of the
        # rest.
        if self.play_time is None:
            return True

        ready_to_start = self.play_time > self.instrument_group.texture.rest_time

        return not self.is_playing and ready_to_start

    def counts_as_playing(self):
        return self.is_playing


class InstrumentGroup:
    def __init__(
            self,
            groupname,
            instrument_name,
            pitch_range,
            max_note_length,
            size,
            texture = None,
            number_start = 1
        ):
        self.name = groupname
        self.texture = texture
        self.instruments = [
            Instrument(
                instrument_name + " " + str(i + number_start),
                pitch_range,
                self,
                max_note_length,
                False
            ) for i in range(size)
        ]

        self.num_playing = 0
        self.time_since_start = 10000
        self.max_playing = 0

    def __str__(self):
        return f'[Instrument group: {self.name}]'

    def print_instruments(self):
        for instrument in self.instruments:
            print(instrument)

    def step(self):
        should_start_playing = (
            self.num_playing < self.max_playing and
            self.time_since_start >= self.texture.fade_time and
            self.texture.allows_start_playing()
        )

        for instrument in self.instruments:
            if should_start_playing and instrument.can_start_playing():
                instrument.start_playing()
                should_start_playing = False
                self.time_since_start = 0

            instrument.step()

        self.time_since_start += TIMESTEP

    def set_texture(self, texture):
        self.texture = texture


class Texture:
    def __init__(
            self,
            pitch,
            dynamic,
            instrument_groups,
            max_playing=1
        ):
        self.pitch = pitch
        self.dynamic = Dynamic(dynamic, self)
        self.instrument_groups = instrument_groups
        self.max_playing = max_playing

        self.instrument_group_index = 0
        self.instrument_groups[0].max_playing = self.max_playing

        for instrument_group in self.instrument_groups:
            instrument_group.set_texture(self)

    def get_active_instrument_groups(self):
        if self.instrument_group_index % 1 == 0:
            return [self.instrument_groups[self.instrument_group_index]]

        index_a = math.floor(self.instrument_group_index)
        index_b = math.ceil(self.instrument_group_index)

        return self.instrument_groups[index_a:index_b]

    def set_instrument_group_index(self, new_value):
        if new_value == self.instrument_group_index:
            return

        for group in self.get_active_instrument_groups():
            group.max_playing = 0

        self.instrument_group_index = new_value
        decimal = self.instrument_group_index % 1

        if decimal == 0:
            self.instrument_groups[self.instrument_group_index].max_playing = self.max_playing
            return

        index = math.floor(self.instrument_group_index)
        self.instrument_groups[index].max_playing = math.ceil(self.max_playing * decimal)
        self.instrument_groups[index + 1].max_playing = math.floor(self.max_playing * (1 - decimal))

    def update_groups_max_playing(self):
        decimal = self.instrument_group_index % 1

        if decimal == 0:
            self.instrument_groups[self.instrument_group_index].max_playing = self.max_playing
            return

        index = math.floor(self.instrument_group_index)
        self.instrument_groups[index].max_playing = math.ceil(self.max_playing * decimal)
        self.instrument_groups[index + 1].max_playing = math.floor(self.max_playing * (1 - decimal))

    def allows_start_playing(self):
        num_playing = 0

        for instrument_group in self.instrument_groups:
            num_playing += instrument_group.num_playing

        return num_playing < self.max_playing

    def set_max_playing(self, new_value):
        self.max_playing = new_value
        self.update_groups_max_playing()


class Line(Texture):
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
            rest_time=1,
            fade_time=0.5
        ):

        super().__init__(pitch, dynamic, instrument_groups, max_playing)
        self.change_rate = change_rate
        self.rest_time = rest_time
        self.fade_time = fade_time

    def __str__(self):
        return f'[Line with pitch {self.pitch}]'

    def step(self):
        for instrument_group in self.instrument_groups:
            instrument_group.step()


class MusicEvent:
    """
    An event that occurs at a given time. Things like pitch changes, dynamics
    changes, etc. Action is a function to be executed at the given time.
    """
    def __init__(self, time, action, args):
        self.time = time
        self.action = action
        self.args = args

    def execute(self):
        self.action(*self.args)


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

    def show(self):
        if self.time.is_integer():
            print("---------", end="")
        elif self.time % 0.25 == 0:
            print("-", end="")
        else:
            print(".", end="")

    def start(self):
        self.events.sort(key=lambda x: x.time)

        while self.time < self.num_measures:
            self.show()
            self.step()
            print("")
            self.time += TIMESTEP

    def step(self):
        if len(self.events) != 0 and self.time >= self.events[0].time:
            self.events.pop(0).execute()

        for line in self.lines:
            line.step()
