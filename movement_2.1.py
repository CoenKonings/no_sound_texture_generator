import sys
from classes import *


FOLDER_NAME = '../no_sound_lilypond/notes/movement-2'


"""
TODO:
Overgebonden (kwart)noten vaak niet nodig
"""

def set_all_fade_times(lines, fade_time):
    for line in lines:
        line.fade_time = fade_time


if __name__ == "__main__":
    NUM_MEASURES = int(sys.argv[1])

    sopsaxes = InstrumentGroup("sopsaxes", "sopsax", None, 2, 2)
    altsaxes = InstrumentGroup("altsaxes", "altsax", None, 2.25, 5)
    tenorsaxes = InstrumentGroup("tenorsaxes", "tenorsax", None, 1.75, 3)
    baritonesaxes = InstrumentGroup("baritonesaxes", "baritonesax", None, 1.75, 1)
    basssaxes = InstrumentGroup("basssaxes", "basssax", None, 1.5, 1)

    flugelhorns = [
        InstrumentGroup(f"flugelhorns{num + 1}", "flugelhorn", (58, 77), 2, i, number_start=j) for num,(i,j) in enumerate([(3,3), (4, 6), (4, 10)])
    ]

    horns = InstrumentGroup("horns", "horn", None, 2, 6)
    altohorns = InstrumentGroup("alto horns", "alto horn", None, 2, 3)

    trumpets = InstrumentGroup("trumpets", "trumpet", (58, 77), 2, 5)

    trombones = InstrumentGroup("trombones", "trombone", None, 1.75, 4)
    basstrombone = InstrumentGroup("basstrombones", "bass trombone", None, 1.5, 1)

    euphoniums = InstrumentGroup("euphoniums", "euphonium", None, 2, 4, number_start=3)

    esbasstubas = InstrumentGroup("esbasstubas", "es bass", None, 1.5, 3)
    besbasstubas = InstrumentGroup("besbasstubas", "bes bass", None, 1.5, 3)

    lines = {
        "sopsaxes": Line(
            [
                Pitch.new_from_lilypond_notation("a\'\'"),
                Pitch.new_from_lilypond_notation("b\'\'"),
            ],
            Dynamic.P,
            [sopsaxes],
            max_playing=1
        ),

        "flugelhorns1": Line(
            [
                Pitch.new_from_lilypond_notation("e\'\'"),
                Pitch.new_from_lilypond_notation("f\'\'"),
            ],
            Dynamic.P,
            [flugelhorns[0]],
            max_playing=1
        ),

        "flugelhorns2": Line(
            [
                Pitch.new_from_lilypond_notation("a\'"),
                Pitch.new_from_lilypond_notation("b\'"),
            ],
            Dynamic.P,
            [flugelhorns[1]],
            max_playing=1
        ),

        "flugelhorns3": Line(
            [
                Pitch.new_from_lilypond_notation("as\'"),
                Pitch.new_from_lilypond_notation("ges\'"),
            ],
            Dynamic.P,
            [flugelhorns[2]],
            max_playing=0
        ),

        "altsaxes": Line(
            [
                Pitch.new_from_lilypond_notation("a"),
                Pitch.new_from_lilypond_notation("b"),
            ],
            Dynamic.P,
            [altsaxes],
            max_playing=2
        ),

        "euphoniums": Line(
            [
                Pitch.new_from_lilypond_notation("es"),
                Pitch.new_from_lilypond_notation("b,"),
            ],
            Dynamic.P,
            [euphoniums],
            max_playing=1
        ),

        "trombones": Line(
            [
                Pitch.new_from_lilypond_notation("b,"),
                Pitch.new_from_lilypond_notation("a,"),
            ],
            Dynamic.MF,
            [trombones],
        ),

        "horns": Line(
            [
                Pitch.new_from_lilypond_notation("bes"),
                Pitch.new_from_lilypond_notation("es"),
                Pitch.new_from_lilypond_notation("d"),
                Pitch.new_from_lilypond_notation("as")
            ],
            Dynamic.P,
            [horns]
        )
    }

    piece = Piece(70, (4,4), NUM_MEASURES, None, lines.values())

    for texture in piece.textures:
        texture.link_rest_time_to_dynamic([0.125, 2])

    events = [
        MusicEvent(2, lines["altsaxes"].set_density, [4]),
        MusicEvent(2, lines["flugelhorns1"].set_density, [2]),
        MusicEvent(4.5, lines["flugelhorns1"].set_density, [3]),
        MusicEvent(4.5, lines["flugelhorns1"].set_max_playing, [2]),
        MusicEvent(6.5, lines["flugelhorns1"].add_pitch, [Pitch.new_from_lilypond_notation("d\'\'")]),
        MusicEvent(8, lines["altsaxes"].dynamic.start_change, [Dynamic.MF, 11]),
        MusicEvent(8.5, lines["flugelhorns2"].set_max_playing, [2]),
        MusicEvent(8.5, lines["flugelhorns2"].set_density, [3]),
        MusicEvent(9.5, lines["altsaxes"].add_pitch, [Pitch.new_from_lilypond_notation("ges")]),
        MusicEvent(9.5, lines["altsaxes"].set_density, [4]),
        MusicEvent(10, lines["flugelhorns1"].dynamic.start_change, [Dynamic.MF, 9]),
        MusicEvent(11, lines["flugelhorns2"].set_density, [4]),
        MusicEvent(11, lines["flugelhorns2"].set_max_playing, [3]),
        MusicEvent(11, lines["flugelhorns1"].add_pitch, [Pitch.new_from_lilypond_notation("bes\'")]),
        MusicEvent(11.5, lines["euphoniums"].set_density, [2]),
        MusicEvent(12, lines["flugelhorns2"].dynamic.start_change, [Dynamic.MF, 7]),
        MusicEvent(12, lines["euphoniums"].dynamic.start_change, [Dynamic.MF, 7]),
        MusicEvent(13, lines["trombones"].set_fade_time, [0]),
        MusicEvent(13, lines["trombones"].set_density, [4]),
        MusicEvent(13, lines["trombones"].set_max_playing, [4]),
        MusicEvent(13, lines["horns"].set_density, [6]),
        MusicEvent(13, lines["horns"].set_max_playing, [3]),
        MusicEvent(13, lines["horns"].dynamic.start_change, [Dynamic.MF, 7]),
        MusicEvent(13.25, lines["trombones"].dynamic.start_change, [Dynamic.P, 1]),
        MusicEvent(13.5, lines["trombones"].set_fade_time, [0.5]),
        MusicEvent(13.5, lines["trombones"].add_pitch, [Pitch.new_from_lilypond_notation("as,")]),
        MusicEvent(15, lines["trombones"].dynamic.start_change, [Dynamic.MF, 4]),
        MusicEvent(15, lines["trombones"].set_density, [3]),
        MusicEvent(15, lines["euphoniums"].set_density, [4]),
        MusicEvent(15, lines["euphoniums"].set_max_playing, [3]),
        MusicEvent(15, lines["euphoniums"].add_pitch, [Pitch.new_from_lilypond_notation("as,")]),
        MusicEvent(15, lines["euphoniums"].add_pitch, [Pitch.new_from_lilypond_notation("ges,")]),
        MusicEvent(16, lines["flugelhorns3"].set_density, [3]),
        MusicEvent(16, lines["flugelhorns3"].set_max_playing, [2]),
        MusicEvent(16, lines["flugelhorns3"].dynamic.start_change, [Dynamic.MF, 3]),
        MusicEvent(16, lines["sopsaxes"].set_density, [2]),
        MusicEvent(16, lines["sopsaxes"].set_max_playing, [2]),
        MusicEvent(16, lines["sopsaxes"].dynamic.start_change, [Dynamic.MF, 3]),
    ]

    events += [
        MusicEvent(19, line.set_fade_time, [0.25]) for line in lines.values()
    ]

    piece.events = events

    piece.start()
    piece.encode_lilypond(FOLDER_NAME)

