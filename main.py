import sys
from classes import *


if __name__ == "__main__":
    NUM_MEASURES = int(sys.argv[1])

    sopsaxes = InstrumentGroup("sopsaxes", "sopsax", None, 2.5, 2)
    altsaxes = InstrumentGroup("altsaxes", "altsax", None, 2.25, 5)
    tenorsaxes = InstrumentGroup("tenorsaxes", "tenorsax", None, 2, 3)
    baritonesaxes = InstrumentGroup("baritonesaxes", "baritonesax", None, 1.75, 1)
    basssaxes = InstrumentGroup("basssaxes", "basssax", None, 1.5, 1)

    flugelhorns = [
        InstrumentGroup("flugelhorns", "flugelhorn", (58, 77), 2, i, number_start=j) for i,j in [(5,1), (4, 6), (4, 10)]
    ]

    horns = InstrumentGroup("horns", "horn", None, 2, 6)
    altohorns = InstrumentGroup("alto horns", "alto horn", None, 2, 3)

    trumpets = InstrumentGroup("trumpets", "trumpet", (58, 77), 2.25, 5)

    trombones = InstrumentGroup("trombones", "trombone", None, 1.75, 4)
    basstrombone = InstrumentGroup("basstrombones", "bass trombone", None, 1.5, 1)

    euphoniums = [
        InstrumentGroup("euphoniums", "euphonium", None, 2, 3, number_start=x) for x in [1, 4]
    ]

    esbasstubas = InstrumentGroup("esbasstubas", "es bass", None, 1.5, 3)
    besbasstubas = InstrumentGroup("besbasstubas", "bes bass", None, 1.5, 3)

    # TODO timpani & bass drum? Misschien met de hand componeren.

    # Movement 1 uses only the line texture.
    lines = [
        Line([  # 0
            Pitch.new_from_lilypond_notation("e\'\'")
        ], Dynamic.MP, [
            flugelhorns[0],
            trumpets
        ], max_playing=0),

        Line([  # 1
            Pitch.new_from_lilypond_notation("b\'")
        ], Dynamic.MP, [
            flugelhorns[1]
        ], max_playing=0),

        Line([  # 2
            Pitch.new_from_lilypond_notation("a\'")
        ], Dynamic.MP, [
            sopsaxes,
            flugelhorns[2]
        ], max_playing=0),

        Line([  # 3
            Pitch.new_from_lilypond_notation("f\'")
        ], Dynamic.MP, [
            horns
        ], max_playing=0),

        Line([  # 4
            Pitch.new_from_lilypond_notation("e\'")
        ], Dynamic.MP, [
            altsaxes
        ], max_playing=0),

        Line([  # 5
            Pitch.new_from_lilypond_notation("b")
        ], Dynamic.MP, [
            euphoniums[0],
            altohorns
        ], max_playing=0),

        Line([  # 6
            Pitch.new_from_lilypond_notation("a")
        ], Dynamic.MP, [
            tenorsaxes,
            trombones
        ], max_playing=0),

        Line([  # 7
            Pitch.new_from_lilypond_notation("f")
        ], Dynamic.MP, [
            euphoniums[1]
        ], max_playing=0),

        Line([  # 8
            Pitch.new_from_lilypond_notation("e")
        ], Dynamic.MP, [
            basstrombone
        ], max_playing=0),

        Line([  # 9
            Pitch.new_from_lilypond_notation("b,")
        ], Dynamic.MP, [
            baritonesaxes
        ], max_playing=0),

        Line([  # 10
            Pitch.new_from_lilypond_notation("f,")
        ], Dynamic.MP, [
            basssaxes,
            esbasstubas,
            besbasstubas
        ], max_playing=0),
    ]

    for line in lines:
        line.set_density(1)

    # Compositional structure
    music_events = [
        MusicEvent(0, lines[5].set_max_playing, [1]),  # Euphoniums 1 start playing
        MusicEvent(4.5, lines[6].set_max_playing, [1]),  # Tenorsaxes start playing
        MusicEvent(7, lines[5].set_density, [2]),
        MusicEvent(7, lines[5].set_max_playing, [2]),
        MusicEvent(7.5, lines[4].set_max_playing, [1]),
    ]

    piece = Piece(70, (4, 4), NUM_MEASURES, music_events, lines)
    piece.start()
    piece.encode_lilypond()
