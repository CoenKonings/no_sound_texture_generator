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

    lines = {
        "sopsaxes": Line(
            [
                Pitch.new_from_lilypond_notation("a\'\'"),
                Pitch.new_from_lilypond_notation("b\'\'"),
            ],
            Dynamic.P,
            sopsaxes,
            max_playing=2
        )
    }

    piece = Piece(70, (4,4), NUM_MEASURES, None, lines.values())

    events = [
    ]

    piece.events = events

    piece.start()
    piece.encode_lilypond()

