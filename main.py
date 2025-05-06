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

        "altsaxes": Line(
            [
                Pitch.new_from_lilypond_notation("ges")
            ],
            Dynamic.P,
            [altsaxes],
            max_playing=1
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
            Dynamic.F,
            [trombones],
        )
    }

    piece = Piece(70, (4,4), NUM_MEASURES, None, lines.values())

    for texture in piece.textures:
        texture.link_rest_time_to_dynamic([0.125, 2])

    events = [
        # MusicEvent(2, lines["sopsaxes"].set_density, [2]),
        MusicEvent(2, lines["flugelhorns1"].set_density, [2]),
        MusicEvent(4.5, lines["flugelhorns1"].set_density, [3]),
        MusicEvent(4.5, lines["flugelhorns1"].set_max_playing, [2]),
        MusicEvent(6.5, lines["flugelhorns1"].add_pitch, [Pitch.new_from_lilypond_notation("d\'\'")]),
        MusicEvent(8.5, lines["flugelhorns2"].set_max_playing, [2]),
        MusicEvent(8.5, lines["flugelhorns2"].set_density, [3]),
        MusicEvent(9.5, lines["altsaxes"].set_density, [1]),
        MusicEvent(11.5, lines["euphoniums"].set_density, [2]),
        MusicEvent(13, lines["trombones"].set_fade_time, [0]),
        MusicEvent(13, lines["trombones"].set_density, [4]),
        MusicEvent(13, lines["trombones"].set_max_playing, [4]),
        MusicEvent(13.5, lines["trombones"].set_fade_time, [0.5]),
    ]

    piece.events = events

    piece.start()
    piece.encode_lilypond(FOLDER_NAME)

