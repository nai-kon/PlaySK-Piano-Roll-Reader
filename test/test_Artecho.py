import sys

import numpy as np
import pytest

sys.path.append("src/")
import players
from midi_controller import MidiWrap


class TestArtecho:
    @pytest.fixture
    def player(self):
        midiobj = MidiWrap()
        obj = players.Artecho("src/playsk_config/Artecho white back (experimental).json", midiobj)
        return obj

    def test_emulate_off(self, player):
        player.bass_cres_pos = 1
        player.treble_cres_pos = 1
        player.pianissimo_lock = True
        player.bass_hammer_rail_lock = True
        player.treble_hammer_rail_lock = True
        player.bass_intensity_lock = [True, True, True]
        player.treble_intensity_lock = [True, True, True]
        player.bass_vacuum = 30
        player.treble_vacuum = 30
        player.bass_vacuum_pre = 30
        player.treble_vacuum_pre = 30
        player.emulate_off()
        assert player.bass_cres_pos == 0
        assert player.treble_cres_pos == 0
        assert not player.pianissimo_lock
        assert not player.bass_hammer_rail_lock
        assert not player.treble_hammer_rail_lock
        assert player.bass_intensity_lock == [False, False, False]
        assert player.treble_intensity_lock == [False, False, False]
        assert player.bass_vacuum == 5.5
        assert player.treble_vacuum == 5.5
        assert player.bass_vacuum_pre == 5.5
        assert player.treble_vacuum_pre == 5.5

    def test_calc_velocity(self, player):
        # check bass/treble hammer rail velocity reduction
        player.bass_vacuum = 11
        player.treble_vacuum = 11
        player.bass_hammer_rail_lock = True
        player.treble_hammer_rail_lock = False
        assert player.calc_velocity() == (54, 60)
        player.bass_hammer_rail_lock = False
        player.treble_hammer_rail_lock = True
        assert player.calc_velocity() == (60, 54)

    def test_emulate_pedals(self, player, mocker):
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

    def test_emulate_expression(self, player):
        # bass intensity cancel
        frame = np.full((600, 800, 3), 0, np.uint8)
        x1, y1, x2, y2 = player.holes["bass_cancel"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.bass_intensity_lock = [True, True, True]
        player.emulate_expression(0)
        assert player.bass_intensity_lock == [False, False, False]

        # treble intensity cancel
        frame = np.full((600, 800, 3), 0, np.uint8)
        x1, y1, x2, y2 = player.holes["treble_cancel"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.treble_intensity_lock = [True, True, True]
        player.emulate_expression(0)
        assert player.treble_intensity_lock == [False, False, False]

        # cancel
        frame = np.full((600, 800, 3), 0, np.uint8)
        x1, y1, x2, y2 = player.holes["cancel"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.bass_hammer_rail_lock = False
        player.treble_hammer_rail_lock = False
        player.pianissimo_lock = False
        player.emulate_expression(0)
        assert not player.bass_hammer_rail_lock
        assert not player.treble_hammer_rail_lock
        assert not player.pianissimo_lock

        # pianissimo
        frame = np.full((600, 800, 3), 0, np.uint8)
        x1, y1, x2, y2 = player.holes["pianissimo"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.emulate_expression(0)
        assert player.pianissimo_lock

