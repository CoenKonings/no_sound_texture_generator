import sys
from classes import *


if __name__ == "__main__":
    NUM_MEASURES = int(sys.argv[1])

    trumpets = InstrumentGroup("trumpets", "trumpet", (58, 77), 2, 5)
    flugelhorns_1 = InstrumentGroup("flugelhorns", "flugelhorn", (58, 77), 2, 5)
    line = Line(76, Dynamic.P, [trumpets, flugelhorns_1], 2)

    piece = Piece(70, (4, 4), NUM_MEASURES, [
        MusicEvent(5, line.set_instrument_group, [1])
    ], [line])
    piece.start()
