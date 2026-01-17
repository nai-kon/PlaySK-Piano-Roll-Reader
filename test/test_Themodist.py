import sys

import numpy as np
import pytest

sys.path.append("src/")
import wx

import tracker_bars
from midi_controller import MidiWrap

app = wx.App()

class TestThemodist:
    @pytest.fixture
    def player(self):
        midiobj = MidiWrap()
        obj = tracker_bars.Themodist("src/playsk_config/Themodist.json", midiobj)
        return obj

    def test_emulate_off(self, player):
        player.bass_vacuum = player.treble_vacuum = player.accent_vacuum
        player.emulate_off()
        assert player.bass_vacuum == player.base_vacuum
        assert player.treble_vacuum == player.base_vacuum

    def test_accent(self, player):
        # bass accent
        frame = np.full((600, 800, 3), 0, np.uint8)
        x1, y1, x2, y2 = player.holes["bass_snakebite"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.emulate_expression(0)
        assert player.bass_vacuum == player.accent_vacuum
        assert player.treble_vacuum == player.base_vacuum

        # treble accent
        frame = np.full((600, 800, 3), 0, np.uint8)
        x1, y1, x2, y2 = player.holes["treble_snakebite"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.emulate_expression(0)
        assert player.bass_vacuum == player.base_vacuum
        assert player.treble_vacuum == player.accent_vacuum
