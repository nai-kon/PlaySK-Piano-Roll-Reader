import sys

import numpy as np
import pytest

sys.path.append("src/")
import players
from midi_controller import MidiWrap


class TestRecordoB:
    @pytest.fixture
    def player(self):
        midiobj = MidiWrap()
        obj = players.RecordoB("src/playsk_config/Recordo B white back.json", midiobj)
        return obj

    @pytest.mark.parametrize("open_ports, expect", [
        # ((open port name), (bass_vacuum, treble_vacuum))
        (("bass_hammer_rail", "treble_hammer_rail"), (8, 8)),
        (("bass_hammer_rail",), (8, 9)),
        (("treble_hammer_rail",), (9, 8)),
        ((), (9, 9)),
        (("p", "bass_hammer_rail"), (10.125, 11.25)),
        (("mf", "bass_hammer_rail"), (13.375, 15.5)),
        (("p", "mf", "bass_hammer_rail"), (13.375, 15.5)),
        (("f", "bass_hammer_rail"), (17.5, 19.5)),
        (("f", "p", "bass_hammer_rail"), (17.5, 19.5)),
        (("f", "mf", "bass_hammer_rail"), (17.5, 19.5)),
        (("f", "mf", "p", "bass_hammer_rail"), (17.5, 19.5)),
        (("ff", "bass_hammer_rail"), (27.25, 35)),
        (("ff", "p", "bass_hammer_rail"), (27.25, 35)),
        (("ff", "mf", "bass_hammer_rail"), (27.25, 35)),
        (("ff", "f", "bass_hammer_rail"), (27.25, 35)),
        (("ff", "p", "mf", "bass_hammer_rail"), (27.25, 35)),
        (("ff", "p", "f", "bass_hammer_rail"), (27.25, 35)),
        (("ff", "mf", "f", "bass_hammer_rail"), (27.25, 35)),
        (("ff", "f", "mf", "p", "bass_hammer_rail"), (27.25, 35)),
    ])
    def test_expression(self, open_ports, expect, player):
        player.delay_ratio = 1
        frame = np.full((600, 800, 3), 0, np.uint8)
        for port in open_ports:
            pos = player.holes[port]["pos"][0]
            frame[pos[1]: pos[3], pos[0]: pos[2]] = 255

        player.holes.set_frame(frame, 0)
        player.emulate_expression(0)
        assert (player.bass_vacuum, player.treble_vacuum) == expect
