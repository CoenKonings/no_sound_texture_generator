import sys
from classes import *


"""
TODO:
Overgebonden (kwart)noten vaak niet nodig
"""


def split_instrument_groups(instrument_group_dict):
    for line in lines:
        if len(line.instrument_groups) > 1:
            for new_line in line.split_instrument_groups():
                instrument_group_dict[new_line.instrument_groups[0].name] = new_line
        else:
            instrument_group_dict[line.instrument_groups[0].name] = line


if __name__ == "__main__":
    NUM_MEASURES = int(sys.argv[1])

    sopsaxes = InstrumentGroup("sopsaxes", "sopsax", None, 2.5, 2)
    altsaxes = InstrumentGroup("altsaxes", "altsax", None, 2.25, 5)
    tenorsaxes = InstrumentGroup("tenorsaxes", "tenorsax", None, 1.75, 3)
    baritonesaxes = InstrumentGroup("baritonesaxes", "baritonesax", None, 1.75, 1)
    basssaxes = InstrumentGroup("basssaxes", "basssax", None, 1.5, 1)

    flugelhorns = [
        InstrumentGroup(f"flugelhorns{num + 1}", "flugelhorn", (58, 77), 2, i, number_start=j) for num,(i,j) in enumerate([(5,1), (4, 6), (4, 10)])
    ]

    horns = InstrumentGroup("horns", "horn", None, 2, 6)
    altohorns = InstrumentGroup("alto horns", "alto horn", None, 2, 3)

    trumpets = InstrumentGroup("trumpets", "trumpet", (58, 77), 2, 5)

    trombones = InstrumentGroup("trombones", "trombone", None, 1.75, 4)
    basstrombone = InstrumentGroup("basstrombones", "bass trombone", None, 1.5, 1)

    euphoniums = [
        InstrumentGroup(f"euphoniums{num+1}", "euphonium", None, 2, 3, number_start=x) for num,x in enumerate([1, 4])
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
        ], max_playing=0, rest_time=1),

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
        line.link_rest_time_to_dynamic([2, 0.25])

    piece = Piece(70, (4, 4), NUM_MEASURES, None, lines)


    # Composition: Movement 1 part 1 (building up)
    music_events = [
        MusicEvent(1, trumpets.add_event_after_rest, ["\\open ^\"harmon mute\""]),
        MusicEvent(1, lines[5].add_player),  # Euphonium 1 start playing
        MusicEvent(4.5, lines[4].add_player),  # Altsax 1 start playing
        MusicEvent(8.5, lines[6].add_player),  # Tenorsax 1 start playing
        MusicEvent(9, lines[5].add_player),  # Euphonium 2 joins
        MusicEvent(9, lines[4].add_player),  # And alt sax 2
        MusicEvent(10, lines[6].add_player),  # Tenor sax 2 joins
        MusicEvent(10.5, lines[2].add_player), # Sopsax 1 starts playing
        MusicEvent(10.5, lines[5].add_player),  # Euphonium 3 joins
        MusicEvent(11.5, lines[6].add_player),  # Tenor sax 3 starts
        MusicEvent(12, lines[4].add_player),  # Alt sax 3 joins
        MusicEvent(12, lines[4].add_player),  # And alt sax 4
        MusicEvent(13, lines[9].add_player),  # Baritone sax starts
        MusicEvent(13.5, lines[1].set_density, [2]),
        MusicEvent(13.5, lines[1].set_max_playing, [2]),
        MusicEvent(14, lines[2].set_density, [2]), # Sopsaxes sustain note
        MusicEvent(14, lines[4].add_player), # All altsaxes play
        MusicEvent(15, lines[2].set_max_playing, [2]),
        MusicEvent(15, lines[2].set_instrument_group_index, [0.5]),
        MusicEvent(15.5, lines[5].set_instrument_group_index, [0.5]),
        # First time F is heard
        MusicEvent(16, lines[7].set_density, [3]),  # Euphs 2 sustains 1 note...
        MusicEvent(16, lines[7].set_max_playing, [1]),  # With one player
        MusicEvent(17, lines[5].set_instrument_group_index, [1]),
        MusicEvent(19, lines[2].set_instrument_group_index, [1]),  # Sopsaxes are taken over by flugelhorns
        MusicEvent(19, lines[3].set_density, [2]),  # 2 horns join
        MusicEvent(19, lines[3].set_max_playing, [2]),
        MusicEvent(20, lines[7].set_max_playing, [2]),  # Euhps 2 note with two players
        MusicEvent(20, lines[0].set_max_playing, [2]),  # Flg 1 joins with 2 players
        MusicEvent(20, lines[0].set_density, [2]),
        MusicEvent(20.5, lines[2].set_density, [4]),  # Flg 2 note with two players
        # First time contra octave is heard
        MusicEvent(21, lines[3].set_max_playing, [6]),
        MusicEvent(21, lines[3].add_player),  # Horn 3 joins
        MusicEvent(21.5, lines[10].add_player),  # Bass sax joins
        MusicEvent(22, lines[2].add_player),  # Flg 2 note with 3 players
        MusicEvent(22.5, lines[10].add_player),  # E flat bass joins
        MusicEvent(23, lines[0].set_max_playing, [3]),  # Add another flg. 1 player
        MusicEvent(23, lines[0].set_density, [5]),
        MusicEvent(23, lines[2].add_player),  # Flg 2 note with 4 players
        MusicEvent(23, lines[10].add_player),  # E flat bass 2 joins
        MusicEvent(23, lines[3].add_player),
        MusicEvent(23, lines[6].add_player),
        MusicEvent(23, lines[3].set_max_playing, [6]),
        MusicEvent(23, lines[3].set_density, [6]),
        MusicEvent(24, lines[10].add_player),  # E flat bass 3 joins
        MusicEvent(24, lines[2].add_player),  # Sopsaxes rejoin note with 4 players

        MusicEvent(24.5, lines[0].set_max_playing, [7]),
        MusicEvent(24.5, lines[0].set_density, [5]),

        MusicEvent(25, lines[1].set_max_playing, [4]),
        MusicEvent(25, lines[1].set_density, [4]),

        MusicEvent(25, lines[2].set_max_playing, [6]),

        MusicEvent(25, lines[4].set_max_playing, [5]),
        MusicEvent(25, lines[4].set_density, [5]),

        MusicEvent(25, lines[5].set_max_playing, [6]),
        MusicEvent(25, lines[5].set_density, [3]),

        MusicEvent(25, lines[7].set_max_playing, [3]),
        MusicEvent(25, lines[7].set_density, [3]),

        MusicEvent(25, lines[9].set_max_playing, [1]),
        MusicEvent(25, lines[9].set_density, [1]),

        MusicEvent(25, lines[6].add_player),
        MusicEvent(25.5, lines[6].add_player),

        MusicEvent(26, lines[6].set_max_playing, [7]),
        MusicEvent(26, lines[6].set_density, [4]),

        MusicEvent(26, lines[10].set_density, [3]),
        MusicEvent(26, lines[10].set_max_playing, [7]),

        MusicEvent(27, lines[0].set_max_playing, [8]),
        MusicEvent(27, lines[8].set_max_playing, [1]),
        MusicEvent(27, lines[8].set_density, [1]),
        MusicEvent(28, lines[0].set_max_playing, [9]),
        MusicEvent(29, lines[0].set_max_playing, [10]),

        MusicEvent(30, piece.add_note_event, ["\\bar \"||\""]),
    ]

    # All lines start increasing dynamics from measure 19 to 29
    music_events += [
        MusicEvent(19, line.dynamic.start_change, [Dynamic.FF, 10]) for line in lines
    ]

    """
    At the end of the build-up, the instrument groups start coming loose from
    the texture. To this end, the lines with more than 1 instrument group
    need to be split.

    For legibility, the line textures are now added to a dictionary, where the
    key is the name of the instrument group playing the line.
    """
    inst_grps = {}

    music_events += [
        MusicEvent(30, split_instrument_groups, [inst_grps])
    ]

    # Generate composition movement 1 part 1 (30 measures)
    # This ensures the new inst_grps dictionary is created before the
    # program continues.
    piece.events = music_events
    piece.start(min(30, NUM_MEASURES))


    # Composition: Movement 1 part 2 (breaking down)
    music_events = [
        # Scherp koper diminuendo
        MusicEvent(30, inst_grps["horns"].dynamic.start_change, [Dynamic.MP, 4]),
        MusicEvent(30, inst_grps["trumpets"].dynamic.start_change, [Dynamic.MP, 4]),
        MusicEvent(30, inst_grps["trombones"].dynamic.start_change, [Dynamic.MP, 4]),
        MusicEvent(30, inst_grps["basstrombones"].dynamic.start_change, [Dynamic.MP, 4]),

        # Saxofoons diminuendo
        MusicEvent(32, inst_grps["sopsaxes"].dynamic.start_change, [Dynamic.P, 4]),
        MusicEvent(32, inst_grps["altsaxes"].dynamic.start_change, [Dynamic.P, 4]),
        MusicEvent(32, inst_grps["tenorsaxes"].dynamic.start_change, [Dynamic.P, 4]),
        MusicEvent(32, inst_grps["baritonesaxes"].dynamic.start_change, [Dynamic.P, 4]),
        MusicEvent(32, inst_grps["basssaxes"].dynamic.start_change, [Dynamic.P, 4]),

        # Scherp koper crescendo
        MusicEvent(34, inst_grps["horns"].dynamic.start_change, [Dynamic.F, 2]),
        MusicEvent(34, inst_grps["trumpets"].dynamic.start_change, [Dynamic.F, 2]),
        MusicEvent(34, inst_grps["trombones"].dynamic.start_change, [Dynamic.F, 2]),
        MusicEvent(34, inst_grps["basstrombones"].dynamic.start_change, [Dynamic.F, 2]),
        MusicEvent(34, trumpets.add_event_after_rest, ["^\"remove mute\""]),

        # Zacht koper diminuendo
        MusicEvent(34, inst_grps["flugelhorns1"].dynamic.start_change, [Dynamic.MP, 2]),
        MusicEvent(34, inst_grps["flugelhorns2"].dynamic.start_change, [Dynamic.MP, 2]),
        MusicEvent(34, inst_grps["flugelhorns3"].dynamic.start_change, [Dynamic.MP, 2]),
        MusicEvent(34, inst_grps["alto horns"].dynamic.start_change, [Dynamic.MP, 2]),
        MusicEvent(34, inst_grps["euphoniums1"].dynamic.start_change, [Dynamic.MP, 2]),
        MusicEvent(34, inst_grps["euphoniums2"].dynamic.start_change, [Dynamic.MP, 2]),
        MusicEvent(34, inst_grps["esbasstubas"].dynamic.start_change, [Dynamic.MP, 2]),
        MusicEvent(34, inst_grps["besbasstubas"].dynamic.start_change, [Dynamic.MP, 2]),

        # Start removing players from lowest notes, creating a "high pass" effect.
        MusicEvent(36, piece.remove_player_from_bottom),
    ]

    piece.events = music_events
    piece.start()
    piece.encode_lilypond()

    print(f'Mvmt. 1 pt. 1 length: 29 measures ({round(piece.measures_to_seconds(29))} seconds)')
    print(f'Piece length: {NUM_MEASURES} measures ({round(piece.measures_to_seconds(NUM_MEASURES))} seconds)')
