"""
Contains all classes needed to generate the LilyPond notation of the textures
in No Sound, a WIP piece for fanfare orchestra.

TODO
- Cleanup (refer to TODOs dotted throughout this file)
- Implement semitone cluster texture.
"""

import math
from copy import copy, deepcopy
from pathlib import Path
import time
import pprint


pp = pprint.PrettyPrinter(indent=4)


# Globals to easily edit some parameters.
TIMESTEP = 0.125  # TODO: move to Piece class
# FOLDER_NAME = None
DEBUG_MODE = False
SHOW_WARNINGS = False
# FONT_SIZE_RANGE = (-4, 20)
FONT_SIZE_RANGE = None
# MIDI_EXPR_RANGE = (0, 1)
MIDI_EXPR_RANGE = None


def debug(x, end="\n"):
    if DEBUG_MODE:
        print(x, end=end)


def warn(x, end="\n"):
    if SHOW_WARNINGS:
        print(x, end=end)


def duration_to_lilypond(time):
    """
    NOTE: Does not support notes faster than 16ths.
    """
    if time > 1:
        raise Exception("Multi-measure time to lilypond not supported.")

    # Account for dotted notes
    if time % TIMESTEP != 0:
        lilypond_time = 1 / (time / 3 * 4) * 2

        if round(lilypond_time) == 7:
            raise Exception(f"Time is 7? {time}")

        return str(round(lilypond_time)) + "."
    else:
        return str(int(1 / time))


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


class LilyPondDuration:
    def __init__(self, lilypond_duration):
        self.value = lilypond_duration

    def new_from_measures(measures):
        measures_left = measures
        lilypond_notation = ""
        duration = 1
        can_dot = False

        while measures_left > 0:
            if measures_left - duration >= 0:
                measures_left = measures_left - duration

                if lilypond_notation == "":
                    lilypond_notation = str(int(1 / duration))
                    can_dot = True
                elif can_dot:
                    lilypond_notation += "."
                else:
                    can_dot = False

            if duration < 1 / 1024:
                raise Exception(
                    f"Durations smaller than 1024th notes not supported. Input: {measures}, duration: {duration}"
                )

            duration /= 2

        return LilyPondDuration(lilypond_notation)

    def as_lilypond(self):
        return self.value

    def in_measures(self):
        dotted = "." in self.value
        duration = 1 / int(self.value.replace(".", ""))

        return duration * (1.5 if dotted else 1)


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
        if isinstance(other, Pitch):
            return self.note == other.note and self.octave == other.octave
        elif isinstance(other, int):  # If integer is given, disregard octave.
            return self.note == other

    def __ne__(self, other):
        if isinstance(other, Pitch):
            return self.note != other.note or self.octave != other.octave
        elif isinstance(other, int):  # If integer is given, disregard octave
            return self.note != other

    def __lt__(self, other):
        """
        NOTE: rests are considered the lowest note, regardless of octave.
        """
        if isinstance(other, Pitch):
            return (
                self.note < other.note and self.octave == other.octave or
                other.note != Pitch.REST and (
                    self.octave < other.octave or
                    self.note == Pitch.REST
                )
            )
        elif isinstance(other, int):  # If integer is given, disregard octave.
            return self.note < other

    def __gt__(self, other):
        """
        NOTE: rests are considered the lowest note, regardless of octave.
        """
        if isinstance(other, Pitch):
            return (
                self.note > other.note and self.octave == other.octave or
                self.pitch != Pitch.REST and (
                    self.octave > other.octave or
                    other.note == Pitch.REST
                )
            )
        elif isinstance(other, int):  # If integer is given, disregard octave.
            return self.note < other

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
        self.events = []

        for event in events:
            self.add_event(event)

        self.delayed_events = []
        self.end_events = []

    def __str__(self):
        note = str(self.pitch) + str(self.duration_as_lilypond())

        if (
            note == "r1" and
            len(self.events_before) == 0 and
            len(self.delayed_events) == 0 and
            len(self.events) == 0 and
            len(self.end_events) == 0
        ):
            note = "R1"

        return " ".join(self.events_before) + " " + self.delayed_events_string() + " " + self.end_events_string() + note + " " + " ".join(self.events)

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
            # (len(note_after.events) == 0 or note_after.events == ["~"]) and
            # len(note_after.events_before) == 0 and
            (self.has_tie() or self.pitch.is_rest()) and
            len(self.end_events) == 0
        )

    def merge(self, note):
        """
        Merge this and the given note by adding the given note's duration to
        this note, and merging their events.
        """


        if self.has_tie() and not note.has_tie():
            self.remove_tie()

        if note.has_tie():
            note.remove_tie()

        for event in note.events:
            self.delayed_events.append([
                LilyPondDuration.new_from_measures(self.duration),
                event
            ])

        for delayed_event in note.delayed_events:
            self.delayed_events.append([
                LilyPondDuration.new_from_measures(delayed_event[0].in_measures() + self.duration),
                delayed_event[1]
            ])

        for event_before in note.events_before:
            if "font-size" not in event_before and "midiExpression" not in event_before:
                self.delayed_events.append([
                    LilyPondDuration.new_from_measures(self.duration),
                    event_before
                ])

        self.end_events = note.end_events
        self.events_before += note.events_before
        self.duration += note.duration

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

        for event in self.delayed_events:
            delay_time = event[0].as_lilypond()
            events_string += f'\\after {delay_time} {event[1]} '

        return events_string

    def end_events_string(self):
        events_string = ""

        for event in self.end_events:
            delay_time = str(self.duration_as_lilypond() * 2) + "."
            events_string += f'\\after {delay_time} {event} '

        return events_string

    def add_tie(self):
        """
        Add a tie to the next note.
        """
        if "~" not in self.events:
            self.events.insert(0, "~")

    def remove_hairpin(self):
        """
        Remove any hairpin dynamics markings if they exist.
        """

        if ("\\>" in self.events):
            self.events.remove("\\>")

        if ("\\<" in self.events):
            self.events.remove("\\<")

    def add_event(self, event):
        if event in ["\\<", "\\>"]:
            # Newest (de)crescendo has priority
            if "\\<" in self.events:
                self.events.remove("\\<")
            if "\\>" in self.events:
                self.events.remove("\\>")

        if event not in self.events:
            self.events.append(event)


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

    def merge_notes(self):
        i = 0
        timescale = TIMESTEP * 2 # Scale at which notes will be merged.
        time_in_measure = 0
        merged_this_round = False

        # Merge notes if possible. Ensure eighth note groupings and the center
        # of the measure remain visible.
        while timescale <= 1:
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


    def lilypond_encode(self):
        """
        First merge the notes in this measure, then convert it to readable
        lilypond code.

        TODO    This should be split into a number of separate functions, but
                more important features will get priority.
        """
        self.merge_notes()  # Comment this for midi velocity
        # This is where the actual encoding begins.
        # TODO: everything above this point should be a separate function.
        lilypond_string = ""

        for note in self.notes:
            lilypond_string += f'{note} '

        return lilypond_string + "| "  # Add barline at the end of the measure.

    def is_empty(self):
        for note in self.notes:
            if (note.pitch != Pitch.REST):
                return False

        return True


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

    def remove_hairpin(self, start_time, current_time):
        """
        Remove a hairpin dynamic mark that was started time measures ago.

        @param time:    How long ago the hairpin started. Time in measures.
        """
        if start_time == current_time:
            warn("WARNING: remove_hairpin: start time is current time")
            return

        measure_index = math.floor(start_time)
        note_index = round((start_time % 1) / TIMESTEP)
        self.get_measure(measure_index).get_note(note_index).remove_hairpin()

    def get_num_trailing_empty_measures(self):
        num_trailing_empty_measures = 0

        for measure in reversed(self.measures):
            if measure.is_empty():
                num_trailing_empty_measures += 1
            else:
                break

        return num_trailing_empty_measures

    def remove_measures_from_end(self, num_measures):
        end_index = len(self.measures)
        start_index = end_index - num_measures
        del self.measures[start_index:end_index]


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
        self.change_start_time = None

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

    def start_change(self, target, time, start_dynamic=None):
        """
        Start a dynamic change, going from the current dynamic to the target
        dynamic, either by gradual (de)crescendo (time > 0) or sudden change
        (time == 0).

        @param target:  The target dynamic value, represented as one of the
                        Dynamic class's constants.
        @param time:    The time the change should take in measures (e.g. a
                        quarter note is 0.25, a dotted whole note is 1.5.)
        """
        if start_dynamic is None:
            start_dynamic = self.value

        # Prevent starting a change if an instrument is still fading in.
        # TODO kind of hacky, find better way.
        if self.is_changing and self.value < start_dynamic:
            return
        # If not on fade-in, stop the current dynamic change to start a new one.
        elif self.is_changing:
            self.stop_change()

        if self.value != target:
            self.is_changing = True
            self.target_dynamic = target
            self.start_dynamic = self.value
            self.time_to_reach_target = time

            if isinstance(self.parent, Instrument):
                self.change_start_time = self.parent.instrument_group.texture.piece.time
            else:
                self.change_start_time = self.parent.piece.time

            self.parent.handle_dynamics()

    def stop_change(self):
        """
        Stop any dynamic change. This can be used both when a change's target
        dynamic was reached or when a new change in dynamics was started before
        the target was reached.
        """
        self.value = round(self.value)
        # self.value = math.floor(self.value) if self.value % 1 < 0.8 else math.ceil(self.value)
        self.is_changing = False
        self.parent.handle_dynamics()
        self.target_dynamic = None
        self.start_dynamic = None
        self.time_to_reach_target = 0
        self.change_start_time = None
        debug(f"{self.parent} reached dynamic", end="")

    def reached_target(self, step_size):
        if not self.is_changing:
            return False

        if abs(self.value - self.target_dynamic) < abs(step_size * 0.5):
            return True

        return False

    def step(self):
        """
        Perform a simulation step by continuing a change that was started
        before, or by stopping change if the target dynamic was reached.
        """

        if self.is_changing:
            num_steps = self.time_to_reach_target / TIMESTEP
            dynamic_step = None

            if num_steps == 0:
                dynamic_step = self.target_dynamic - self.value
            else:
                dynamic_step = (self.target_dynamic - self.start_dynamic) / num_steps


            if isinstance(self.parent, Texture) and FONT_SIZE_RANGE is not None:
                font_size_diff = FONT_SIZE_RANGE[1] - FONT_SIZE_RANGE[0]
                font_size = self.value / 7 * font_size_diff + FONT_SIZE_RANGE[0]
                self.parent.add_note_event(
                    f"\\override NoteHead.font-size = {font_size}",
                    place_before=True
                )
            elif isinstance(self.parent, Instrument) and MIDI_EXPR_RANGE is not None:
                midi_expr_diff = MIDI_EXPR_RANGE[1] - MIDI_EXPR_RANGE[0]
                midi_expr = self.value / 7 * midi_expr_diff + MIDI_EXPR_RANGE[0]
                self.parent.add_note_event(
                    f'\\set midiExpression = {midi_expr}',
                    place_before=True
                )

            if self.reached_target(dynamic_step):
                self.stop_change()
                return

            self.value += dynamic_step

        elif isinstance(self.parent, Instrument):
            if self.parent.pitch == Pitch.REST:
                return

            texture = self.parent.instrument_group.texture
            if texture.dynamic.is_changing:
                self.start_change(
                    texture.dynamic.target_dynamic,
                    texture.dynamic.time_to_reach_target
                )
            elif texture.dynamic.value != self.value:
                self.start_change(
                    texture.dynamic.value,
                    texture.fade_time  # TODO only works for line textures.
                )

    def change_as_lilypond(self):
        """
        Encode an ongoing change in dynamics in LilyPond notation: \\< for a
        crescendo, \\> for a decrescendo, or nothing if no gradual change is
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
        self.dynamic = None  # Dynamics cannot be manually assigned, use texture dynamics instead.
        self.allowed_to_play = False
        self.events = []  # Instructions like dynamics or text.
        self.events_before = []  # Instructions that should be placed before a note in LilyPond notation.
        self.score = LilyPondScore()
        self.pitch = Pitch(-1, 0)
        self.after_rest_events = []  # Events that should happen immediately after a rest.
        self.rested = True  # Track if the instrument played a rest.

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

        debug(
            f'{self} starts playing {self.pitch} on {self.dynamic}',
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

            debug((f"{self} is stopping with {self.dynamic}"), end="")
        else:
            self.is_stopping = False
            self.is_playing = False
            self.pitch.note = -1
            debug(f"{self} has stopped", end="")

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

        debug(f"{self} has stopped", end="")

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

        if self.is_playing and self.rested:
            self.rested = False
            self.events += [x["event"] for x in self.after_rest_events if not x["place_before"]]
            self.events_before += [x["event"] for x in self.after_rest_events if x["place_before"]]
            self.after_rest_events = []
        elif not self.is_playing and not self.rested:
            self.rested = True

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

            if (  # Comment this if statement for MIDI velocity.
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
        return ready_to_start and not self.is_playing

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

    def encode_lilypond(self, folder_name):
        print(f'\x1b[2KEncoding score for {self.name} in lilypond...', end="\r")
        time.sleep(0.05)
        filename = self.name.replace(" ", "") + ".ly"
        lilypond_score = ""
        lilypond_score += "{" if folder_name is not None else ""
        lilypond_score += self.score.encode_lilypond()
        lilypond_score += "}\n" if folder_name is not None else "\n"

        if folder_name is None:
            print()
            print(lilypond_score)
            print("------------------------------")
            return

        with open(f'{folder_name}/{filename}', 'w+') as file:
            file.write(lilypond_score)

    def handle_dynamics(self):
        """
        Handle dynamics changes etc. by tracking them in LilyPond notes.
        """
        # Dynamics marks at a rest are added to the previous note.
        if self.pitch.note == -1:
            last_note = self.score.get_last_note()
            last_note.end_events.append(self.dynamic.as_lilypond())
        elif (
            self.dynamic.start_dynamic is not None and
            self.dynamic.start_dynamic == self.dynamic.value and
            not self.dynamic.is_changing
        ):
            self.score.remove_hairpin(
                self.dynamic.change_start_time,
                self.instrument_group.texture.piece.time
            )
        else:
            self.add_note_event(self.dynamic.as_lilypond())

    def add_note_event(self, event, place_before=False):
        """
        Add a note event, such as a rehearsal mark or staff text.
        """

        if place_before:
            self.events_before.append(event)
        else:
            self.events.append(event)

    def add_event_after_rest(self, event, place_before=False):
        """
        Add a note event after the next rest.
        TODO: implement place before.
        """
        self.after_rest_events.append({
            "event": event,
            "place_before": place_before
        })

    def get_num_trailing_empty_measures(self):
        return self.score.get_num_trailing_empty_measures()

    def remove_measures_from_end(self, num_measures):
        self.score.remove_measures_from_end(num_measures)


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

    def __gt__(self, other):
        return self.get_num_instruments() > other.get_num_instruments()

    def __lt__(self, other):
        return self.get_num_instruments() < other.get_num_instruments()

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

    def encode_lilypond(self, folder_name):
        for instrument in self.instruments:
            instrument.encode_lilypond(folder_name)

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
        self.instruments[index].allowed_to_play = allowed

    def set_num_allowed_to_play(self, num):
        """
        Set the first num instruments to be allowed to play. Disallow playing
        for all other instruments in this group.
        """
        for i in range(len(self.instruments)):
            self.allow_instrument(i, i<num)

    def get_num_instruments(self):
        return len(self.instruments)

    def add_event_after_rest(self, event, place_before=False):
        for instrument in self.instruments:
            instrument.add_event_after_rest(event, place_before=place_before)

    def get_num_trailing_empty_measures(self):
        num_trailing_empty_measures = self.texture.piece.num_measures

        for instrument in self.instruments:
            num_trailing_empty_measures = min(
                num_trailing_empty_measures,
                instrument.get_num_trailing_empty_measures()
            )

        return num_trailing_empty_measures

    def remove_measures_from_end(self, num_measures):
        for instrument in self.instruments:
            instrument.remove_measures_from_end(num_measures)


class Texture:
    def __init__(
            self,
            pitches,
            dynamic,
            instrument_groups,
            piece=None,
            max_playing=1,
            density=0
        ):
        self.pitches = pitches
        self.piece = piece
        self.dynamic = Dynamic(dynamic, self)
        self.instrument_groups = instrument_groups
        self.max_playing = max_playing

        self.instrument_group_index = 0
        self.instrument_groups[0].max_playing = self.max_playing

        for instrument_group in self.instrument_groups:
            instrument_group.set_texture(self)

        self.set_density(density)

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
        index = round(self.instrument_group_index)
        decimal = abs(self.instrument_group_index - index)
        max_playing = self.max_playing
        num_instrument_groups = len(self.instrument_groups)

        # TODO: Clean if else spaghetti
        for i in range(int(num_instrument_groups / 2) + 1):
            x = (index + i) % num_instrument_groups
            y = (index - i) % num_instrument_groups

            # If x is the instrument group that should be loudest
            if i == 0:
                n = max_playing * (1 - decimal)
                instrument_group = self.instrument_groups[x]
                n = min(n, instrument_group.get_num_instruments())
                instrument_group.max_playing = n
                max_playing -= n
            # If x is the index of the final instrument group
            elif x == y:
                instrument_group = self.instrument_groups[x]
                n = min(max_playing, instrument_group.get_num_instruments())
                instrument_group.max_playing = n
                max_playing -= n
            else:
                instrument_group_a = self.instrument_groups[x]
                n_a = min(round(max_playing / 2), instrument_group_a.get_num_instruments())
                instrument_group_a.max_playing = n_a
                max_playing -= n_a

                instrument_group_b = self.instrument_groups[y]
                n_b = min(round(max_playing / 2), instrument_group_b.get_num_instruments())
                instrument_group_b.max_playing = n_b
                max_playing -= n_b

            if max_playing == 0:
                break

    def split_instrument_groups(self):
        """
        If this texture has multiple instrument groups, return a list of copies
        of this texture, each with one of this texture's instrument groups.
        """
        raise Exception(f'Texture {self} split_instrument_groups not implemented')

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

    def encode_lilypond(self, folder_name):
        for instrument_group in self.instrument_groups:
            instrument_group.encode_lilypond(folder_name)

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

    def add_event_after_rest(self, event, placeBefore=False):
        for instrument_group in self.instrument_groups:
            instrument_group.add_event_after_rest(event, placeBefore=placeBefore)

    def remove_player(self):
        if self.density > self.max_playing:
            self.set_density(self.density - 1)
        elif self.max_playing > self.density:
            self.set_max_playing(self.max_playing - 1)
        else:
            self.set_density(self.density - 1)
            self.set_max_playing(self.max_playing - 1)

    def get_num_instruments(self):
        num_instruments = 0

        for instrument_group in self.instrument_groups:
            num_instruments += instrument_group.get_num_instruments()

        return num_instruments

    def largest_instrument_group_size(self):
        return max(self.instrument_groups).get_num_instruments()

    def get_num_trailing_empty_measures(self):
        num_trailing_empty_measures = self.piece.num_measures

        for instrument_group in self.instrument_groups:
            num_trailing_empty_measures = min(
                num_trailing_empty_measures,
                instrument_group.get_num_trailing_empty_measures()
            )

        return num_trailing_empty_measures

    def remove_measures_from_end(self, num_measures):
        for instrument_group in self.instrument_groups:
            instrument_group.remove_measures_from_end(num_measures)


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
            fade_time=0.5,
            density=0
        ):

        super().__init__(pitches, dynamic, instrument_groups, piece, max_playing, density=density)
        self.change_rate = change_rate
        self.rest_time = rest_time
        self.fade_time = fade_time
        self.piece = piece
        self.manual_rest_time = True
        self.rest_time_range = (None, None)

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
                    # Break to stagger start times
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


    def step(self, should_start_new_measure):
        if not self.manual_rest_time:
            # Interpolate rest time from range based on dynamic.
            scaled_dynamic = self.dynamic.value / Dynamic.FFF
            rest_range_diff = self.rest_time_range[1] - self.rest_time_range[0]
            scaled_rest_time = scaled_dynamic * rest_range_diff
            scaled_rest_time += self.rest_time_range[0]
            rounded_rest_time = round(scaled_rest_time / TIMESTEP) * TIMESTEP
            self.rest_time = rounded_rest_time

        super().step(should_start_new_measure)

    def add_pitch(self, pitch):
        self.pitches.insert(0, pitch)

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
                            self.dynamic.time_to_reach_target,
                            self.dynamic.start_dynamic
                        )
                    else:
                        instrument.dynamic.start_change(
                            self.dynamic.value,
                            self.fade_time
                        )

    def split_instrument_groups(self):
        if len(self.instrument_groups) == 1:
            return self

        new_lines = []

        for i, instrument_group in enumerate(self.instrument_groups):
            if i == len(self.instrument_groups) - 1:
                # Skip the last iteration
                break

            new_line = copy(self)
            new_line.instrument_groups = [instrument_group]
            new_line.dynamic = copy(self.dynamic)
            new_line.dynamic.parent = new_line
            new_line.pitches = deepcopy(self.pitches)
            instrument_group.texture = new_line
            new_line.piece.textures.append(new_line)
            new_line.set_density(
                min(new_line.density, new_line.largest_instrument_group_size())
            )
            new_line.set_max_playing(
                min(new_line.max_playing, new_line.get_num_instruments())
            )

            new_lines.append(new_line)

        self.instrument_groups = [self.instrument_groups[-1]]
        self.set_density(
            min(self.density, self.largest_instrument_group_size())
        )
        self.set_max_playing(
            min(self.max_playing, self.get_num_instruments())
        )

        new_lines.append(self)

        return new_lines


    def set_rest_time(self, rest_time):
        self.manual_rest_time = True
        self.rest_time = rest_time

    def set_fade_time(self, fade_time):
        self.fade_time = fade_time


    def link_rest_time_to_dynamic(self, range):
        self.manual_rest_time = False
        self.rest_time_range = range

    def set_pitches(self, pitches):
        self.pitches = pitches


class MusicEvent:
    """
    An event that occurs at a given time. Things like pitch changes, dynamics
    changes, etc. Action is a function to be executed at the given time.
    """
    def __init__(self, time, action, args=None):
        self.time = time - 1  # Convert between start=0 and start=1
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
        debug("%3f" % self.time, end="")

        if self.time.is_integer():
            debug("---------", end="")
        elif self.time % 0.25 == 0:
            debug("-", end="")
        else:
            debug(".", end="")

    def start(self, num_measures=None):
        if self.time == 0:
            print("Generating piece...")

        self.events.sort(key=lambda x: x.time)

        if num_measures is None:
            num_measures = self.num_measures

        while self.time < num_measures:
            self.show()
            self.step()
            debug("")

            self.time += TIMESTEP

            if self.time % 1 == 0:
                time.sleep(0.02)  # This makes for a prettier demonstration vid.
                print(f"\x1b[2KGenerating measure {int(self.time)}", end="\r")

        if self.time == self.num_measures:
            print("\x1b[2K\rPiece finished.")

    def step(self):
        # Time is measured in bars/measures.
        should_start_new_measure = self.time.is_integer()

        while len(self.events) != 0 and self.time >= self.events[0].time:
            self.events.pop(0).execute()

        for texture in self.textures:
            texture.step(should_start_new_measure)

    def remove_trailing_empty_measures(self):
        num_trailing_empty_measures = self.num_measures

        for texture in self.textures:
            empty = texture.get_num_trailing_empty_measures()
            num_trailing_empty_measures = min(
                num_trailing_empty_measures,
                empty
            )

        for texture in self.textures:
            texture.remove_measures_from_end(num_trailing_empty_measures)

    def encode_lilypond(self, folder_name, remove_trailing_empty_measures=False):
        if folder_name is not None:
            Path(folder_name).mkdir(exist_ok=True)

        print("Encoding piece in LilyPond...")

        if remove_trailing_empty_measures:
            self.remove_trailing_empty_measures()

        for texture in self.textures:
            texture.encode_lilypond(folder_name)

        print("\x1b[2K\rLilyPond encoding finished.")

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

    def add_event_after_rest(self, event, place_before=True):
        for texture in self.textures:
            texture.add_event_after_rest(event, place_before)

    def add_texture(self, texture):
        self.textures.append(texture)

    def remove_player_from_top(self):
        """
        Remove one player from the active texture with the highest pitch,
        determined by highest pitch in texture.pitches.
        """
        raise Exception("Piece.remove_player_from_top not implemented yet.")

    def remove_player_from_bottom(self):
        """
        Remove one player from the active texture with the lowest pitch,
        determined by lowest pitch in texture.pitches.
        """
        lowest_pitch_texture = None

        for texture in self.textures:
            if (
                texture.density > 0 and
                texture.max_playing > 0
            ):
                if (
                    lowest_pitch_texture is None or
                    min(texture.pitches) < min(lowest_pitch_texture.pitches)
                ):
                    lowest_pitch_texture = texture

        if lowest_pitch_texture is not None:
            lowest_pitch_texture.remove_player()

    def get_num_instruments(self):
        num_instruments = 0

        for texture in self.textures:
            num_instruments += texture.get_num_instruments()

        return num_instruments
