import sys
from classes import *


if __name__ == "__main__":
    NUM_MEASURES = int(sys.argv[1])

    trumpets = InstrumentGroup("trumpets", "trumpet", (58, 77), 2, 5)
    flugelhorns_1 = InstrumentGroup("flugelhorns", "flugelhorn", (58, 77), 2, 5)
    line = Line([Pitch(4, 6)], Dynamic.P, [trumpets, flugelhorns_1], 1)

    # trumpets = InstrumentGroup("trumpets", "trumpet", (58, 77), 2, 1)
    # line = Line([Pitch(4, 7)], Dynamic.P, [trumpets], 1)

    piece = Piece(70, (4, 4), NUM_MEASURES, [
        MusicEvent(2, line.set_max_playing, [3]),
        MusicEvent(5, line.set_instrument_group_index, [0.5]),
        MusicEvent(7, line.set_max_playing, [5]),
        MusicEvent(9, line.set_instrument_group_index, [1])
    ], [line])
    piece.start()
    piece.encode_lilypond()
