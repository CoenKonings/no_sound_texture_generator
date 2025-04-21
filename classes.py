"""
Contains all classes needed to generate the LilyPond notation of the textures
in No Sound, a WIP piece for fanfare orchestra.

TODO
- Cleanup (refer to TODOs dotted throughout this file)
- Implement semitone cluster texture.
"""

import math
from copy import copy
from pathlib import Path


# Globals to easily edit some parameters.
TIMESTEP = 0.125  # TODO: move to Piece class
FOLDER_NAME = '../no_sound_lilypond/notes/movement-1'  # TODO: move to Piece.encode_lilypond parameter
DEBUG_MODE = False


def to_roman_numeral(num):
    """
    Rewrite an integer as a roman numeral.

    @param num:   An integer.
    @returns:     A string containing the roman numeral representation of num.
    """
    lookup = [
        (1000, 'M'),
        (900, 'CM'),
        (500, 'D'),
        (400, 'CD'),
        (100, 'C'),
        (90, 'XC'),
        (50, 'L'),
        (40, 'XL'),
        (10, 'X'),
        (9, 'IX'),
        (5, 'V'),
        (4, 'IV'),
        (1, 'I'),
    ]
    res = ''
    for (n, roman) in lookup:
        (d, num) = divmod(num, n)
        res += roman * d
    return res


class Pitch:
    """
    A pitch represented as a note and an octave. Notes are represented as a
    number from 0 to 11, representing notes C, C#, D, etc, ignoring enharmonic
    spellings. Note number -1 represents a rest. The octave is represented as a
    number, where 0 is the sub-contra octave. For example, Pitch(0, 5) is
    middle C.
    """
    NOTE_NAMES = ["c", "des", "d", "es", "e", "f", "ges", "g", "as", "a",
                      "bes", "b", "r"]
    C, DES, D, ES, E, F, GES, G, AS, A, BES, B, REST = 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, -1

    def __init__(self, note, octave):
        """
        Initialize a new Pitch.

        @param note:    A number from 0 to 11 for C, C#, etc, or -1 for a rest.
        @param octave:  The octave number, where 0 is the sub-contra octave.
        """
        self.note = note
        self.octave = octave

    def new_from_lilypond_notation(lilypond_note):
        octave = 4  # Octave number for small octave
        note_name = ""

        for character in lilypond_note:
            match character:
                case "\'":
                    octave += 1
                case ",":
                    octave -= 1
                case _:
                    note_name += character

        if note_name not in Pitch.NOTE_NAMES:
            raise Exception("Pitch from lilypond note: incorrect note name.")

        return Pitch(Pitch.NOTE_NAMES.index(note_name), octave)



    def __str__(self):
        return self.to_lilypond()

    def __copy__(self):
        return type(self)(self.note, self.octave)

    def __eq__(self, other):
        return self.note == other.note and self.octave == other.octave

    def __ne__(self, other):
        return self.note != other.note or self.octave != other.octave

    def octave_to_lilypond(self):
        """
        Returns a string containing this Pitch's octave in lilypond notation,
        where the small octave is represented with the empty string, a
        comma is added for each octave below the small octave and an apostrophe
        is added for each octave above the small octave. For example, the
        octave containing middle c would be represented by "\'", and the
        contra octave is represented by ",,".

        @returns:   A string containing this Pitch's octave in lilypond
                    notation.
        """
        octave = self.octave - 4

        if octave == 0 or self.note == -1:
            return ""
        elif octave < 0:
            return -octave * ","
        else:
            return octave * "\'"

    def to_lilypond(self):
        """
        Write this Pitch in LilyPond notation. For example, middle C is
        represented as "c\'", and the D in the sub-contra octave is represented
        as "d,,,".

        @returns:   A string representing this Pitch in LilyPond notation.
        """
        return Pitch.NOTE_NAMES[self.note] + self.octave_to_lilypond()

    def is_rest(self):
        return self.note == Pitch.REST


class LilyPondNote:
    """
    This class is used to track notes' pitch, duration and events such as ties
    and changes in dynamics.
    """
    def __init__(self, pitch, events_before=[], events=[], duration=TIMESTEP):
        self.pitch = pitch
        self.duration = duration
        self.events_before = events_before
        self.events = events
        self.delayed_events = []

    def __str__(self):
        note = str(self.pitch) + str(self.duration_as_lilypond())
        return " ".join(self.events_before) + " " + self.delayed_events_string() + note + " " + " ".join(self.events)

    def has_tie(self):
        return "~" in self.events

    def remove_tie(self):
        self.events.remove("~")

    def can_merge(self, note_after):
        """
        Check if the note can merge with the given note, assuming the given
        note comes directly after this note.
        """
        return (
            note_after is not None and
            self.pitch == note_after.pitch and
            self.duration == note_after.duration and
            (len(note_after.events) == 0 or note_after.events == ["~"]) and
            len(note_after.events_before) == 0 and
            (self.has_tie() or self.pitch.is_rest())
        )

    def merge(self, note):
        """
        Merge this and the given note by adding the given note's duration to
        this note, and merging their events.
        """
        self.duration += note.duration

        if self.has_tie():
            self.remove_tie()

        self.events += note.events
        self.delayed_events += note.delayed_events
        self.events_before += note.events_before

    def duration_as_lilypond(self):
        """
        Return an integer representing this note's duration (tracked in
        fractions of a measure, e.g. 0.25 for a quarter note) in LilyPond
        notation (where a quarter note is written as 4, an eighth note as 8,
        a sixteenth note as 16, etc.).

        @returns:   An integer representing this note's duration in LilyPond
                    notation.
        """
        return int(1 / self.duration)

    def delayed_events_string(self):
        """
        Delayed events happen at the end of a note, instead of the beginning.
        This is done by using LilyPond's after command, with a duration of 3/4
        of this note's duration. Example use case: a "fade out" at the end of
        a note. Using a delayed event instead of adding the dynamic to the next
        note prevents a rest having a dynamic.

        @returns    The event formatted using LilyPond's "after" command.
        """
        events_string = ""
        delay_time = str(self.duration_as_lilypond() * 2) + "."

        for event in self.delayed_events:
            events_string += f'\\after {delay_time} {event} '

        return events_string

    def add_tie(self):
        """
        Add a tie to the next note.
        """
        if "~" not in self.events:
            self.events.append("~")

    def remove_hairpin(self):
        """
        Remove any hairpin dynamics markings if they exist.
        """

        if ("\\>" in self.events):
            self.events.remove("\\>")

        if ("\\<" in self.events):
            self.events.remove("\\<")


class LilyPondMeasure:
    """
    This class tracks the music at meso level.
    """
    def __init__(self):
        self.notes = []

    def add_note(self, pitch, events=[], events_before=[], duration=TIMESTEP):
        """
        Add a new note to this measure.
        """
        self.notes.append(LilyPondNote(copy(pitch), events_before, events, duration))

    def get_length(self):
        return len(self.notes)

    def get_note(self, index):
        return self.notes[index]

    def lilypond_encode(self):
        """
        First merge the notes in this measure, then convert it to readable
        lilypond code.

        TODO    This should be split into a number of separate functions, but
                more important features will get priority.
        """
        done = False
        i = 0
        timescale = TIMESTEP * 2 # Scale at which notes will be merged.
        time_in_measure = 0
        merged_this_round = False

        # Merge notes if possible. Ensure eighth note groupings and the center
        # of the measure remain visible.
        while not done:
            current_note = self.notes[i]
            next_note = None if i + 1 == len(self.notes) else self.notes[i + 1]
            # Notes should be merged if they can be merged and merging them
            # will not obfuscate the count groupings and center of a measure.
            should_merge_notes = (
                time_in_measure % timescale == 0 and
                i < len(self.notes) and
                current_note.duration < timescale and
                current_note.can_merge(next_note)
            )

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

                if timescale > 1:
                    done = True

        # This is where the actual encoding begins.
        # TODO: everything above this point should be a separate function.
        lilypond_string = ""

        for note in self.notes:
            lilypond_string += f'{note} '

        return lilypond_string + "| "  # Add barline at the end of the measure.


class LilyPondScore:
    """
    This class is used to track all music played by one instrument.
    """
    def __init__(self):
        self.measures = []

    def new_measure(self):
        """
        Add a new, empty measure to this score.
        """
        self.measures.append(LilyPondMeasure())

    def get_last_measure(self):
        """
        Helper function for legibility. Returns the last measure in this score.
        """
        return self.measures[-1]

    def encode_lilypond(self):
        """
        Get a string representing this score in LilyPond notation.

        @returns:   A string containing this score in LilyPond notation.
        """
        lilypond_string = ""

        for index, measure in enumerate(self.measures):
            lilypond_string += measure.lilypond_encode()

            # Add a newline on every fourth bar for legibility.
            if index % 4 == 3:
                lilypond_string += "\n"

        return lilypond_string

    def get_num_measures(self):
        """
        Get the number of measures in this score.
        """
        return len(self.measures)

    def get_last_note(self):
        if len(self.measures[-1].notes) != 0:
            return self.measures[-1].notes[-1]
        elif self.get_num_measures() > 1:
            return self.measures[-2].notes[-1]
        else:
            return None

    def get_measure(self, index):
        return self.measures[index]

    def remove_hairpin(self, time_since_start, current_time):
        """
        Remove a hairpin dynamic mark that was started time measures ago.

        @param time:    How long ago the hairpin started. Time in measures.
        """
        num_measures = math.floor(time_since_start)
        num_notes = round((time_since_start % 1) / TIMESTEP)
        current_measure_length = self.get_last_measure().get_length()

        if current_measure_length < num_notes:
            num_notes -= current_measure_length

        if current_measure_length == 8 and current_time % 1 == 0:
            num_measures -= 1
            num_notes += 8

        self.get_measure(-1 - num_measures).get_note(-num_notes).remove_hairpin()


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
        self.time_spent_changing = None

    def __str__(self):
        movement_string = "static"

        if self.is_changing:
            movement_string = f"moving towards {Dynamic.value_as_string(self.target_dynamic)}"

        return f'[Dynamic {Dynamic.value_as_string(self.value)} {movement_string}]'

    def value_as_string(value):
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

        return f'\\{dynamic_dict[round(value)]}'

    def start_change(self, target, time):
        """
        Start a dynamic change, going from the current dynamic to the target
        dynamic, either by gradual (de)crescendo (time > 0) or sudden change
        (time == 0).

        @param target:  The target dynamic value, represented as one of the
                        Dynamic class's constants.
        @param time:    The time the change should take in measures (e.g. a
                        quarter note is 0.25, a dotted whole note is 1.5.)
        """
        if self.is_changing:
            self.stop_change()

        self.is_changing = True
        self.target_dynamic = target
        self.start_dynamic = self.value
        self.time_to_reach_target = time
        self.time_spent_changing = 0
        self.parent.handle_dynamics()

    def stop_change(self):
        """
        Stop any dynamic change. This can be used both when a change's target
        dynamic was reached or when a new change in dynamics was started before
        the target was reached.
        """
        self.value = round(self.value)
        self.is_changing = False
        self.parent.handle_dynamics()
        self.target_dynamic = None
        self.start_dynamic = None
        self.time_to_reach_target = 0
        self.time_spent_changing = None
        print(self.parent, "reached target dynamic", end="")

    def reached_target(self):
        if not self.is_changing:
            return False

        if abs(self.value - self.target_dynamic) < 0.1:
            return True

        return False

    def step(self):
        """
        Perform a simulation step by continuing a change that was started
        before, or by stopping change if the target dynamic was reached.
        """
        if self.reached_target():
            self.stop_change()
            return

        if self.is_changing:
            num_steps = self.time_to_reach_target / TIMESTEP
            dynamic_step = (self.target_dynamic - self.start_dynamic) / num_steps
            self.value += dynamic_step
            self.time_spent_changing += TIMESTEP

    def change_as_lilypond(self):
        """
        Encode an ongoing change in dynamics in LilyPond notation: \< for a
        crescendo, \> for a decrescendo, or nothing if no gradual change is
        taking place.

        @returns:   The current ongoing change (crescendo, decrescendo, none)
                    in LilyPond notation.
        """
        if self.is_changing:
            if self.target_dynamic > self.start_dynamic:
                return "\\<"
            else:
                return "\\>"

        return ""

    def as_lilypond(self):
        if self.is_changing:
            return self.change_as_lilypond()
        else:
            return Dynamic.value_as_string(self.value)


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
        self.allowed_to_play = False
        self.events = []
        self.events_before = []
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
            self.handle_dynamics()

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
            self.play_time = 0
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

    def become_quiet(self):
        self.is_stopping = False
        self.is_playing = False
        self.play_time = 0
        self.pitch.note = -1
        print(self, "has stopped", end="")

    def step(self, step_callback, should_start_new_measure, replace_last_note=False):
        """
        The generic part of an instrument's simulation step. Tracks time, calls
        the dynamic's step function, ensures the music played by this
        instrument is tracked properly in the score. Takes a callback for all
        texture-specific behaviours.

        TODO: This function could use a cleanup, mainly by splitting it into
        several functions for legibility.
        """
        if self.play_time is not None:
            self.play_time += TIMESTEP

        step_callback(self)

        # Dynamic is none if instrument has not started playing yet.
        if self.dynamic is not None:
            self.dynamic.step()

        if should_start_new_measure:
            self.score.new_measure()

        if replace_last_note:
            self.score.get_last_measure().notes.pop(-1)
            self.score.get_last_measure().add_note(self.pitch, self.events, self.events_before)
        else:
            previous_note = self.score.get_last_note()

            if (
                previous_note is not None and
                previous_note.pitch == self.pitch and
                not self.pitch.is_rest()
            ):
                previous_note.add_tie()

            self.score.get_last_measure().add_note(self.pitch, self.events, self.events_before)

        self.events = []
        self.events_before = []


    def can_start_playing(self):
        # If the instrument is not playing, play_time tracks the length of the
        # rest.
        if not self.allowed_to_play:
            return False
        elif self.play_time is None:
            return True

        ready_to_start = self.play_time >= self.instrument_group.texture.rest_time

        return ready_to_start and (not self.is_playing) and self.allowed_to_play

    def counts_as_playing(self):
        return self.is_playing

    def get_lilypond_variable_name(self):
        varname_list = []

        for substr in self.name.split():
            if substr.isnumeric():
                varname_list.append(to_roman_numeral(int(substr)))
            else:
                varname_list.append(substr)

        return "".join(varname_list) + "notes"

    def encode_lilypond(self):
        print(f'encoding lilypond for {self}...')
        filename = self.name.replace(" ", "") + ".ly"
        lilypond_score = ""

        # if not DEBUG_MODE:
        #     lilypond_score += "\\" + self.get_lilypond_variable_name() + " = "

        lilypond_score += "{" + self.score.encode_lilypond() + "}\n"

        with open(f'{FOLDER_NAME}/{filename}', 'w+') as file:
            file.write(lilypond_score)

    def handle_dynamics(self):
        """
        Handle dynamics changes etc. by tracking them in LilyPond notes.
        """
        # Dynamics marks at a rest are added to the previous note.
        if self.pitch.note == -1:
            self.score.get_last_note().delayed_events.append(
                self.dynamic.as_lilypond()
            )
        elif (
            self.dynamic.start_dynamic is not None and
            self.dynamic.start_dynamic == self.dynamic.value and
            not self.dynamic.is_changing
        ):
            self.score.remove_hairpin(
                self.dynamic.time_spent_changing,
                self.instrument_group.texture.piece.time
            )
        else:
            self.events.append(self.dynamic.as_lilypond())

    def add_note_event(self, event, place_before=False):
        """
        Add a note event, such as a rehearsal mark or staff text.
        """

        if place_before:
            self.events_before.append(event)
        else:
            self.events.append(event)


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
        self.instruments = []

        for i in range(size):
            name = instrument_name

            # Only add number if this is the only instrument of its type
            # NOTE: Assumes no groups of one exist if there are multiple of the
            # same instrument.
            if size != 1 or number_start != 1:
                name += f' {i + number_start}'

            self.instruments.append(Instrument(
                name,
                pitch_range,
                self,
                max_note_length,
                False
            ))

        self.num_playing = 0
        self.time_since_start = 10000
        self.max_playing = 0

    def __str__(self):
        return f'[Instrument group: {self.name}]'

    def print_instruments(self):
        for instrument in self.instruments:
            print(instrument)

    def should_start_playing(self):
        return (
            self.num_playing < self.max_playing and
            self.time_since_start >= self.texture.fade_time and
            self.texture.allows_start_playing()
        )

    def step(self, step_callback, should_start_new_measure):
        """
        The generic part of a simulation step for an instrument group. Calls
        the callback function for texture-specific behaviour and tracks time.
        """
        step_callback(self, should_start_new_measure)
        self.time_since_start += TIMESTEP

    def set_texture(self, texture):
        self.texture = texture

    def encode_lilypond(self):
        for instrument in self.instruments:
            instrument.encode_lilypond()

    def add_note_event(self, event, place_before=False):
        """
        Add a note event, such as an instruction or rehearsal mark, to all
        instruments in this group.
        """
        for instrument in self.instruments:
            instrument.add_note_event(event, place_before)

    def allow_instrument(self, index, allowed):
        """
        Allow the instrument at the given index to start playing.
        """
        if index >= len(self.instruments):
            return

        self.instruments[index].allowed_to_play = allowed

    def set_num_allowed_to_play(self, num):
        """
        Set the first num instruments to be allowed to play. Disallow playing
        for all other instruments in this group.
        """
        for i in range(num):
            self.allow_instrument(i, i<num)


class Texture:
    def __init__(
            self,
            pitches,
            dynamic,
            instrument_groups,
            piece=None,
            max_playing=1
        ):
        self.pitches = pitches
        self.piece = piece
        self.dynamic = Dynamic(dynamic, self)
        self.instrument_groups = instrument_groups
        self.max_playing = max_playing

        self.instrument_group_index = 0
        self.instrument_groups[0].max_playing = self.max_playing
        self.density = 0

        for instrument_group in self.instrument_groups:
            instrument_group.set_texture(self)

    def __str__(self):
        return "[Texture]"

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
        self.update_groups_max_playing()

    def update_groups_max_playing(self):
        decimal = self.instrument_group_index % 1

        # If the index has no decimal numbers, all instruments should be played
        # by the same group.
        if decimal == 0:
            self.instrument_groups[self.instrument_group_index].max_playing = self.max_playing
            return

        index = math.floor(self.instrument_group_index)
        # If 50/50, favour the first instrument group.
        # TODO: If the calculation below results in a number larger than the
        #       size of the group, have the exceeding amount "overflow" into
        #       adjacent groups.
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

    def step(self, should_start_new_measure):
        self.dynamic.step()

        for instrument_group in self.instrument_groups:
            instrument_group.step(
                self.instrument_group_step,
                should_start_new_measure
            )

    def instrument_group_step(self, instrument_group, should_start_new_measure):
        raise Exception(
            f'Texture {self} instrument_group_step not implemented.'
        )

    def instrument_step(self, instrument, should_start_new_measure):
        raise Exception(
            f'Texture {self} instrument_step not implemented.'
        )

    def get_pitch(self, *_):
        raise Exception(f'Texture {self} get_pitch not implemented.')

    def encode_lilypond(self):
        for instrument_group in self.instrument_groups:
            instrument_group.encode_lilypond()

    def handle_dynamics(self):
        raise Exception("Texture handle_dynamics not implemented.")

    def add_note_event(self, event, place_before=False):
        """
        Add a note event, like an instruction, rehearsal mark, etc, to all
        instrument groups performing this texture.
        """

        for instrument_group in self.instrument_groups:
            instrument_group.add_note_event(event, place_before)

    def set_density(self, density):
        """
        Set the texture's density in number of instruments.
        """
        self.density = density

        for instrument_group in self.instrument_groups:
            instrument_group.set_num_allowed_to_play(density)

    def add_player(self):
        if self.density < self.max_playing:
            self.set_density(self.density + 1)
        elif self.max_playing < self.density:
            self.set_max_playing(self.max_playing + 1)
        else:
            self.set_density(self.density + 1)
            self.set_max_playing(self.max_playing + 1)

    def stop(self):
        self.set_density(0)
        self.set_max_playing(0)


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
            piece=None,
            max_playing=1,
            change_rate=0,
            rest_time=0.5,
            fade_time=0.5
        ):

        super().__init__(pitches, dynamic, instrument_groups, piece, max_playing)
        self.change_rate = change_rate
        self.rest_time = rest_time
        self.fade_time = fade_time
        self.piece = piece

    def __str__(self):
        return f'[Line with pitches {self.pitches}]'

    def instrument_group_step(self, instrument_group, should_start_new_measure):
        """
        The part of an InstrumentGroup's simulation step that is specific to
        the Line texture.
        """
        for instrument in instrument_group.instruments:
            instrument.step(self.instrument_step, should_start_new_measure)

        if instrument_group.should_start_playing():
            for instrument in instrument_group.instruments:
                if instrument.can_start_playing():
                    instrument.start_playing()
                    instrument.step(self.instrument_step, False, True)
                    instrument_group.time_since_start = 0
                    break

    def instrument_step(self, instrument):
        """
        The part of an instrument's simulation step that is specific to the
        Line texture.
        """
        if (instrument.is_stopping and instrument.play_time >= self.fade_time):
            instrument.become_quiet()

        if instrument.should_stop():
            instrument.stop_playing()

    def get_pitch(self):
        """
        Get the next pitch to be performed for this texture.

        @returns:   A Pitch object.
        """
        pitch = self.pitches.pop(0)
        self.pitches.append(pitch)
        return Pitch(pitch.note, pitch.octave)

    def handle_dynamics(self):
        """
        Handle a change in dynamics by having the instrument groups creating
        this texture follow suit.
        """

        for instrument_group in self.instrument_groups:
            for instrument in instrument_group.instruments:

                if instrument.is_playing and not instrument.is_stopping:
                    # Change the instrument's target dynamic to this Line's
                    # target dynamic.
                    if self.dynamic.is_changing:
                        instrument.dynamic.start_change(
                            self.dynamic.target_dynamic,
                            self.dynamic.time_to_reach_target
                        )
                    else:
                        instrument.dynamic.start_change(
                            self.dynamic.value,
                            self.fade_time
                        )


class MusicEvent:
    """
    An event that occurs at a given time. Things like pitch changes, dynamics
    changes, etc. Action is a function to be executed at the given time.
    """
    def __init__(self, time, action, args=None):
        self.time = time
        self.action = action
        self.args = args

    def execute(self):
        if self.args is None:
            self.action()
        else:
            self.action(*self.args)


class Piece:
    """
    This class is used to generate the piece. It manages the timeline and
    ensures the music is executed correctly.
    """
    def __init__(self, tempo, time_signature, num_measures, events, textures):
        self.time = 0  # The time in measures.
        self.tempo = tempo
        self.time_signature = time_signature  # Does nothing as of yet.
        self.num_measures = num_measures
        self.events = events
        self.textures = textures

        for texture in self.textures:
            texture.piece = self

    def show(self):
        print("%3f" % self.time, end="")

        if self.time.is_integer():
            print("---------", end="")
        elif self.time % 0.25 == 0:
            print("-", end="")
        else:
            print(".", end="")

    def start(self):
        self.events.sort(key=lambda x: x.time)

        while self.time < self.num_measures:
            if DEBUG_MODE:
                self.show()

            self.step()

            if DEBUG_MODE:
                print("")

            self.time += TIMESTEP

    def step(self):
        # Time is measured in bars/measures.
        should_start_new_measure = self.time.is_integer()

        while len(self.events) != 0 and self.time >= self.events[0].time:
            self.events.pop(0).execute()

        for texture in self.textures:
            texture.step(should_start_new_measure)

    def encode_lilypond(self):
        Path(FOLDER_NAME).mkdir(exist_ok=True)

        for texture in self.textures:
            texture.encode_lilypond()

    def seconds_to_measures(self, seconds):
        """
        Convert time in seconds to a number of measures. Round to the nearest
        TIMESTEP.

        NOTE: Only works for 4/4 for now. Might be updated if this type of
        texture is revisited in a future piece.
        """
        num_beats = seconds * self.tempo / 60
        num_measures = num_beats / 4
        num_measures_rounded = round(num_measures / TIMESTEP) * TIMESTEP
        return num_measures_rounded

    def measures_to_seconds(self, measures):
        """
        Convert time in measures to time in seconds.

        NOTE: Only works for 4/4 for now. Might be updated if this type of
        texture is revisited in a future piece.
        """
        seconds_per_beat = 60 / self.tempo
        seconds_per_measure = seconds_per_beat * 4
        return seconds_per_measure * measures

    def add_note_event(self, event, place_before=True):
        """
        Add a note event to all notes at the current time.

        @param event:   A string containing the note event in LilyPond notation.
        """
        for texture in self.textures:
            texture.add_note_event(event, place_before)

    def add_texture(self, texture):
        self.textures.append(texture)
