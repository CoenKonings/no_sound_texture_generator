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

    piece = Piece(70, (4, 4), NUM_MEASURES, None, lines)

    # Compositional structure
    music_events = [
        MusicEvent(0, lines[5].add_player),  # Euphonium 1 start playing
        MusicEvent(3.5, lines[6].add_player),  # Tenorsax 1 start playing
        MusicEvent(5, lines[5].add_player),  # Euphonium 2 joins
        MusicEvent(6.5, lines[4].add_player),  # Altsax 1 starts playing
        MusicEvent(7, lines[6].add_player),  # Tenorsax 2 joins
        MusicEvent(8, lines[4].add_player),  # Altsax 2 joins
        MusicEvent(8.5, lines[2].add_player),  # Sopsax 1 starts playing
        MusicEvent(8.75, lines[5].set_density, [3]),  # Euphonium 3 starts playing
        MusicEvent(9, lines[3].set_max_playing, [2]),  # Horns start playing
        MusicEvent(9, lines[3].set_density, [6]),
        MusicEvent(9.5, lines[7].add_player),  # Euphonium 4 starts playing
        MusicEvent(10, lines[7].set_density, [3]),  # Euphoniums 2 sustain note
        MusicEvent(11, lines[8].add_player),
        MusicEvent(11.25, lines[1].add_player),
        MusicEvent(11.5, lines[0].add_player),
        MusicEvent(12, lines[7].add_player),
        MusicEvent(12.5, lines[9].add_player),
        MusicEvent(13, lines[10].add_player),
        MusicEvent(20, piece.add_note_event, ["\\bar \"||\""])
    ]

    # All lines start increasing dynamics from measure 9 to 18
    music_events += [
        MusicEvent(8, line.dynamic.start_change, [Dynamic.FF, 9]) for line in lines
    ]

    print(music_events)

    piece.events = music_events
    piece.start()
    piece.encode_lilypond()

    mvmt_1_length_bars = round(piece.seconds_to_measures(60))
    line_texture_length_bars = mvmt_1_length_bars + 18
    print(f'Movement 1 length: {mvmt_1_length_bars} bars')
    print(f'Line texture time: {piece.measures_to_seconds(line_texture_length_bars)} seconds')
