import sys

import numpy as np
import pytest

sys.path.append("src/")
import wx

import tracker_bars
from midi_controller import MidiWrap

app = wx.App()

class TestRecordoA:
    @pytest.fixture
    def player(self):
        midiobj = MidiWrap()
        obj = tracker_bars.RecordoA("src/playsk_config/Recordo A.json", midiobj)
        return obj

    def test_emulate_off(self, player):
        player.bass_vacuum = 40
        player.treble_vacuum = 40
        player.emulate_off()
        assert player.bass_vacuum == player.intensities[0]
        assert player.treble_vacuum == player.intensities[0]

    def test_pedal(self, player, mocker):

        # sustain on
        frame = np.full((600, 800, 3), 0, np.uint8)
        sustain_on_mock = mocker.patch("midi_controller.MidiWrap.sustain_on")
        x1, y1, x2, y2 = player.holes["sustain"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.emulate_pedals()
        sustain_on_mock.assert_called_once()

        # sustain off
        frame = np.full((600, 800, 3), 0, np.uint8)
        sustain_off_mock = mocker.patch("midi_controller.MidiWrap.sustain_off")
        frame[y1:y2, x1:x2, :] = 0
        player.holes.set_frame(frame, 0)
        player.emulate_pedals()
        sustain_off_mock.assert_called_once()

    @pytest.mark.parametrize("open_ports, expect", [
        # ((open port name), (bass_vacuum, treble_vacuum))
        (("bass_hammer_rail", "treble_hammer_rail"), (7, 7)),
        (("bass_hammer_rail",), (7, 8)),
        (("treble_hammer_rail",), (8, 7)),
        ((), (8, 8)),
        (("p", "bass_hammer_rail"), (8.5, 9)),
        (("mf", "bass_hammer_rail"), (9.5, 10)),
        (("p", "mf", "bass_hammer_rail"), (10.75, 11.5)),
        (("f", "bass_hammer_rail"), (12.25, 13)),
        (("f", "p", "bass_hammer_rail"), (13.75, 14.5)),
        (("f", "mf", "bass_hammer_rail"), (15.25, 16)),
        (("f", "mf", "p", "bass_hammer_rail"), (17, 18)),
        (("ff", "bass_hammer_rail"), (19.25, 20.5)),
        (("ff", "p", "bass_hammer_rail"), (23.75, 27)),
        (("ff", "mf", "bass_hammer_rail"), (31, 35)),
        (("ff", "f", "bass_hammer_rail"), (31, 35)),
        (("ff", "p", "mf", "bass_hammer_rail"), (31, 35)),
        (("ff", "p", "f", "bass_hammer_rail"), (31, 35)),
        (("ff", "mf", "f", "bass_hammer_rail"), (31, 35)),
        (("ff", "f", "mf", "p", "bass_hammer_rail"), (31, 35)),
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
