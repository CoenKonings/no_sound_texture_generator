import math
from copy import copy


TIMESTEP = 0.125


class Pitch:
    NOTE_NAMES = ["c", "des", "d", "es", "e", "f", "ges", "g", "as", "a",
                      "bes", "b", "r"]

    def __init__(self, note, octave):
        self.note = note
        self.octave = octave

    def __str__(self):
        return f'[Pitch: {self.to_lilypond()}]'

    def __copy__(self):
        return type(self)(self.note, self.octave)

    def __eq__(self, other):
        return self.note == other.note and self.octave == other.octave

    def __ne__(self, other):
        return self.note != other.note or self.octave != other.octave

    def octave_to_lilypond(self):
        octave = self.octave - 5

        if octave == 0 or self.note == -1:
            return ""
        elif octave < 0:
            return -octave * ","
        else:
            return octave * "\'"

    def to_lilypond(self):
        return Pitch.NOTE_NAMES[self.note] + self.octave_to_lilypond()



class LilyPondNote:
    def __init__(self, pitch, events=[], duration=TIMESTEP):
        self.pitch = pitch
        self.duration = duration
        self.events = events

    def __str__(self):
        return f'[Note {self.pitch} for {self.duration} measures]'

    def can_merge(self, note_after):
        """
        Check if the note can merge with the given note, assuming the given
        note comes directly after this note.

        # TODO: check if events can be merged
        """
        return (
            note_after is not None and
            self.pitch == note_after.pitch and
            self.duration == note_after.duration
        )

    def merge(self, note):
        self.duration += note.duration
        self.events += note.events


class LilyPondMeasure:
    def __init__(self):
        self.notes = []

    def add_note(self, pitch, events=[], duration=TIMESTEP):
        self.notes.append(LilyPondNote(copy(pitch), events, duration))

    def lilypond_encode(self):
        done = False
        i = 0
        timescale = TIMESTEP * 2
        time_in_measure = 0
        merged_this_round = False

        while not done:
            current_note = self.notes[i]
            next_note = None if i + 1 == len(self.notes) else self.notes[i + 1]
            should_merge_notes = (time_in_measure % timescale == 0 and i < len(self.notes) and
                current_note.can_merge(next_note))

            if should_merge_notes:
                current_note.merge(next_note)
                self.notes.pop(i + 1)
                merged_this_round = True

            time_in_measure += current_note.duration
            i += 1

            if i >= len(self.notes):
                i = 0

                if not merged_this_round:
                    timescale *= 2
                else:
                    merged_this_round = False

                if timescale >= 1:
                    done = True

        for note in self.notes:
            print(note)


class LilyPondScore:
    def __init__(self):
        self.measures = []

    def new_measure(self):
        self.measures.append(LilyPondMeasure())

    def last_measure(self):
        return self.measures[-1]

    def encode_lilypond(self):
        for measure in self.measures:
            measure.lilypond_encode()


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

    def typeof_change(self):
        if self.is_changing:
            if self.target_dynamic > self.start_dynamic:
                return Dynamic.CRESC
            else:
                return Dynamic.DECRESC

        return None


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
        self.score = LilyPondScore()
        self.pitch = Pitch(-1, 0)

    def __str__(self):
        return f'[Instrument: {self.name}]'

    def start_playing(self):
        self.is_playing = True
        self.play_time = 0
        self.instrument_group.num_playing += 1
        self.pitch = self.instrument_group.texture.get_pitch()

        if not self.dynamic:
            self.dynamic = Dynamic(Dynamic.PPP, self)

        self.dynamic.start_change(
            self.instrument_group.texture.dynamic.value,
            self.instrument_group.texture.fade_time
        )

        print(
            self,
            f'starts playing {self.pitch} on',
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
            self.pitch.note = -1
            print(self, "has stopped", end="")

        self.instrument_group.num_playing -= 1

    def should_stop(self):
        max_play_time = self.max_note_length - self.instrument_group.texture.fade_time
        return (
            self.is_playing and
            self.play_time > max_play_time and
            not self.is_stopping
        )

    def step(self, start_new_measure):
        if self.play_time is not None:
            self.play_time += TIMESTEP

        if self.is_stopping and self.play_time > self.instrument_group.texture.fade_time:
            self.is_stopping = False
            self.is_playing = False
            self.play_time = 0
            self.pitch.note = -1
            print(self, "has stopped", end="")

        if self.should_stop():
            self.stop_playing()

        # Dynamic is none if instrument has not started playing yet.
        if self.dynamic is not None:
            self.dynamic.step()

        if start_new_measure:
            self.score.new_measure()

        self.score.last_measure().add_note(self.pitch)


    def can_start_playing(self):
        # If the instrument is not playing, play_time tracks the length of the
        # rest.
        if self.play_time is None:
            return True

        ready_to_start = self.play_time > self.instrument_group.texture.rest_time

        return not self.is_playing and ready_to_start

    def counts_as_playing(self):
        return self.is_playing

    def encode_lilypond(self):
        print("encode lilypond for", self)
        self.score.encode_lilypond()


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

    def step(self, start_new_measure):
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

            instrument.step(start_new_measure)

        self.time_since_start += TIMESTEP

    def set_texture(self, texture):
        self.texture = texture

    def encode_lilypond(self):
        for instrument in self.instruments:
            instrument.encode_lilypond()


class Texture:
    def __init__(
            self,
            pitches,
            dynamic,
            instrument_groups,
            max_playing=1
        ):
        self.pitches = pitches
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

    def step(self, *_):
        raise Exception("Texture step not implemented.")

    def get_pitch(self, *_):
        raise Exception("Texture get_pitch not implemented.")

    def encode_lilypond(self):
        for instrument_group in self.instrument_groups:
            instrument_group.encode_lilypond()


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
            pitches,
            dynamic,
            instrument_groups,
            max_playing=1,
            change_rate=0,
            rest_time=1,
            fade_time=0.5
        ):

        super().__init__(pitches, dynamic, instrument_groups, max_playing)
        self.change_rate = change_rate
        self.rest_time = rest_time
        self.fade_time = fade_time

    def __str__(self):
        return f'[Line with pitch {self.pitch}]'

    def step(self, start_new_measure):
        for instrument_group in self.instrument_groups:
            instrument_group.step(start_new_measure)

    def get_pitch(self):
        pitch = self.pitches.pop(0)
        self.pitches.append(pitch)
        return Pitch(pitch.note, pitch.octave)


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
    def __init__(self, tempo, time_signature, num_measures, events, textures):
        self.time = 0  # The time in measures
        self.tempo = tempo
        self.time_signature = time_signature
        self.num_measures = num_measures
        self.events = events
        self.textures = textures

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
        start_new_measure = self.time.is_integer()

        if len(self.events) != 0 and self.time >= self.events[0].time:
            self.events.pop(0).execute()

        for texture in self.textures:
            texture.step(start_new_measure)

    def encode_lilypond(self):
        for texture in self.textures:
            texture.encode_lilypond()
