import sys

import numpy as np
import pytest

sys.path.append("src/")
import wx

from midi_controller import MidiWrap
from tracker_bars.Themodist_eValve import Themodist_eValve

app = wx.App()

class TestThemodist_eValve:
    @pytest.fixture
    def player(self) -> Themodist_eValve:
        midiobj = MidiWrap()
        return Themodist_eValve("src/playsk_config/Themodist e-Valve.json", midiobj)

    def test_emulate_off(self, player):
        player.bass_vacuum = player.treble_vacuum = player.accent_vacuum
        player.emulate_off()
        assert player.bass_vacuum == player.base_vacuum
        assert player.treble_vacuum == player.base_vacuum

    def test_accent(self, player, mocker):
        # bass accent on
        frame = np.full((600, 800, 3), 0, np.uint8)
        x1, y1, x2, y2 = player.holes["bass_snakebite"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        midi_mock = mocker.patch("midi_controller.MidiWrap.note_on")
        player.holes.set_frame(frame, 0)
        player.emulate_expression(0)
        midi_mock.assert_called_with(player.bass_snake_midi_no, velocity=64)
        assert player.bass_vacuum == player.accent_vacuum
        assert player.treble_vacuum == player.base_vacuum

        # bass accent off
        frame[y1:y2, x1:x2, :] = 0
        midi_mock = mocker.patch("midi_controller.MidiWrap.note_off")
        player.holes.set_frame(frame, 0)
        player.emulate_expression(0)
        midi_mock.assert_called_with(player.bass_snake_midi_no, velocity=64)
        assert player.bass_vacuum == player.base_vacuum
        assert player.treble_vacuum == player.base_vacuum

        # treble accent on
        frame = np.full((600, 800, 3), 0, np.uint8)
        x1, y1, x2, y2 = player.holes["treble_snakebite"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        midi_mock = mocker.patch("midi_controller.MidiWrap.note_on")
        player.holes.set_frame(frame, 0)
        player.emulate_expression(0)
        midi_mock.assert_called_with(player.treble_snake_midi_no, velocity=64)
        assert player.bass_vacuum == player.base_vacuum
        assert player.treble_vacuum == player.accent_vacuum

        # treble accent off
        frame[y1:y2, x1:x2, :] = 0
        midi_mock = mocker.patch("midi_controller.MidiWrap.note_off")
        player.holes.set_frame(frame, 0)
        player.emulate_expression(0)
        midi_mock.assert_called_with(player.treble_snake_midi_no, velocity=64)
        assert player.bass_vacuum == player.base_vacuum
        assert player.treble_vacuum == player.base_vacuum

    def test_sustain(self, player, mocker):
        # sustein on
        frame = np.full((600, 800, 3), 0, np.uint8)
        x1, y1, x2, y2 = player.holes["sustain"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        midi_mock = mocker.patch("midi_controller.MidiWrap.note_on")
        player.holes.set_frame(frame, 0)
        player.emulate_pedals()
        midi_mock.assert_called_with(player.sustein_midi_no, velocity=64)

        # sustein off
        frame[y1:y2, x1:x2, :] = 0
        midi_mock = mocker.patch("midi_controller.MidiWrap.note_off")
        player.holes.set_frame(frame, 0)
        player.emulate_pedals()
        midi_mock.assert_called_with(player.sustein_midi_no, velocity=64)
