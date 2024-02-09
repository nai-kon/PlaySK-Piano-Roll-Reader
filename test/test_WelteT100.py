import sys

import numpy as np
import pytest

sys.path.append("src/")

from midi_controller import MidiWrap
from WelteT100 import WelteT100


class TestWelteT100:
    @pytest.fixture
    def player(self):
        midiobj = MidiWrap()
        obj = WelteT100("src/playsk_config/Welte T100 white back.json", midiobj)
        return obj

    def test_emulate_off(self, player):
        player.bass_cres_pos = 1
        player.bass_cres_state = "slow_cres"
        player.bass_mf_hook = True
        player.treble_cres_pos = 1
        player.treble_cres_state = "slow_cres"
        player.treble_mf_hook = True
        player.bass_vacuum = 30
        player.treble_vacuum = 30
        player.emulate_off()
        assert player.bass_cres_pos == 0
        assert player.bass_cres_state == "slow_decres"
        assert not player.bass_mf_hook
        assert player.treble_cres_pos == 0
        assert player.treble_cres_state == "slow_decres"
        assert not player.treble_mf_hook
        assert player.bass_vacuum == player.min_vacuum
        assert player.treble_vacuum == player.min_vacuum

    def test_pedal(self, player, mocker):

        # sustain on
        frame = np.full((600, 800, 3), 0, np.uint8)
        sustain_on_mock = mocker.patch("midi_controller.MidiWrap.sustain_on")
        x1, y1, x2, y2 = player.holes["sustain_on"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.emulate_pedals()
        sustain_on_mock.assert_called_once()

        # sustain off
        frame = np.full((600, 800, 3), 0, np.uint8)
        sustain_off_mock = mocker.patch("midi_controller.MidiWrap.sustain_off")
        x1, y1, x2, y2 = player.holes["sustain_off"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.emulate_pedals()
        sustain_off_mock.assert_called_once()

        # soft on
        frame = np.full((600, 800, 3), 0, np.uint8)
        sustain_on_mock = mocker.patch("midi_controller.MidiWrap.soft_on")
        x1, y1, x2, y2 = player.holes["soft_on"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.emulate_pedals()
        sustain_on_mock.assert_called_once()

        # soft off
        frame = np.full((600, 800, 3), 0, np.uint8)
        sustain_off_mock = mocker.patch("midi_controller.MidiWrap.soft_off")
        x1, y1, x2, y2 = player.holes["soft_off"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.emulate_pedals()
        sustain_off_mock.assert_called_once()
