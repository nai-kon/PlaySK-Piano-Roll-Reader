import sys

import numpy as np
import pytest

sys.path.append("src/")
import tracker_bars
from midi_controller import MidiWrap


class TestWelteT98:
    @pytest.fixture
    def player(self):
        midiobj = MidiWrap()
        obj = tracker_bars.WelteT98("src/playsk_config/Welte T98.json", midiobj)
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
        x1, y1, x2, y2 = player.holes["sustain"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.emulate_pedals()
        sustain_on_mock.assert_called_once()

        # sustain off
        sustain_off_mock = mocker.patch("midi_controller.MidiWrap.sustain_off")
        frame[y1:y2, x1:x2, :] = 0
        player.holes.set_frame(frame, 0)
        player.emulate_pedals()
        sustain_off_mock.assert_called_once()

        # soft on
        frame = np.full((600, 800, 3), 0, np.uint8)
        sustain_on_mock = mocker.patch("midi_controller.MidiWrap.soft_on")
        x1, y1, x2, y2 = player.holes["soft"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.emulate_pedals()
        sustain_on_mock.assert_called_once()

        # soft off
        sustain_off_mock = mocker.patch("midi_controller.MidiWrap.soft_off")
        frame[y1:y2, x1:x2, :] = 0
        player.holes.set_frame(frame, 0)
        player.emulate_pedals()
        sustain_off_mock.assert_called_once()


    def test_emulate_expression(self, player):
        # bass mf on
        frame = np.full((600, 800, 3), 0, np.uint8)
        x1, y1, x2, y2 = player.holes["bass_mf"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.emulate_expression(0)
        assert player.bass_mf_hook

        # bass mf off
        frame[y1:y2, x1:x2, :] = 0
        player.holes.set_frame(frame, 0)
        player.emulate_expression(0)
        assert not player.bass_mf_hook

        # bass crescendo
        frame = np.full((600, 800, 3), 0, np.uint8)
        x1, y1, x2, y2 = player.holes["bass_cresc"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.emulate_expression(0)
        assert player.bass_cres_state == "slow_cres"

        frame[y1:y2, x1:x2, :] = 0
        player.holes.set_frame(frame, 0)
        player.emulate_expression(0)
        assert player.bass_cres_state == "slow_decres"

        # treble mf on
        frame = np.full((600, 800, 3), 0, np.uint8)
        x1, y1, x2, y2 = player.holes["treble_mf"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.emulate_expression(0)
        assert player.treble_mf_hook

        # treble mf off
        frame[y1:y2, x1:x2, :] = 0
        player.holes.set_frame(frame, 0)
        player.emulate_expression(0)
        assert not player.treble_mf_hook

        # treble crescendo
        frame = np.full((600, 800, 3), 0, np.uint8)
        x1, y1, x2, y2 = player.holes["treble_cresc"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.emulate_expression(0)
        assert player.treble_cres_state == "slow_cres"

        frame[y1:y2, x1:x2, :] = 0
        player.holes.set_frame(frame, 0)
        player.emulate_expression(0)
        assert player.treble_cres_state == "slow_decres"
