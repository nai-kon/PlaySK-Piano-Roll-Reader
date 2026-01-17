import math
import sys

import numpy as np
import pytest

sys.path.append("src/")
import wx

import tracker_bars
from midi_controller import MidiWrap

app = wx.App()

class TestAmpicoB:
    @pytest.fixture
    def player(self):
        midiobj = MidiWrap()
        obj = tracker_bars.AmpicoB("src/playsk_config/Ampico B.json", midiobj)
        return obj

    def test_emulate_off(self, player):
        player.amp_lock_range = [0.3, 0.85]
        player.amp_cres_pos = 0.5
        player.bass_intensity_lock = [True, True, True]
        player.treble_intensity_lock = [True, True, True]
        player.bass_sub_intensity_lock = True
        player.treble_sub_intensity_lock = True
        player.bass_vacuum = 40
        player.treble_vacuum = 40
        player.emulate_off()
        assert player.amp_lock_range == [0, 1.0]
        assert player.amp_cres_pos == 0
        assert player.bass_intensity_lock == [False, False, False]
        assert player.treble_intensity_lock == [False, False, False]
        assert not player.bass_sub_intensity_lock
        assert not player.treble_sub_intensity_lock
        assert player.bass_vacuum == player.intensity_range["none"][0]
        assert player.treble_vacuum == player.intensity_range["none"][0]

    def test_emulate_expression(self, player):
        # bass intensity cancel
        frame = np.full((600, 800, 3), 0, np.uint8)
        x1, y1, x2, y2 = player.holes["bass_cancel"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.bass_intensity_lock = [True, True, True]
        player.bass_sub_intensity_lock = True
        player.emulate_expression(0)
        assert player.bass_intensity_lock == [False, False, False]
        assert not player.bass_sub_intensity_lock

        # treble intensity cancel
        frame = np.full((600, 800, 3), 0, np.uint8)
        x1, y1, x2, y2 = player.holes["treble_cancel"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.treble_intensity_lock = [True, True, True]
        player.treble_sub_intensity_lock = True
        player.emulate_expression(0)
        assert player.treble_intensity_lock == [False, False, False]
        assert not player.treble_sub_intensity_lock

        # sub intensity
        frame = np.full((600, 800, 3), 0, np.uint8)
        x1, y1, x2, y2 = player.holes["subintensity"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.bass_sub_intensity_lock = False
        player.treble_sub_intensity_lock = False
        player.emulate_expression(0)
        assert player.bass_sub_intensity_lock
        assert player.treble_sub_intensity_lock

        # intensity holes
        for idx in range(3):
            frame = np.full((600, 800, 3), 0, np.uint8)
            x1, y1, x2, y2 = player.holes["bass_intensity"]["pos"][idx]
            frame[y1:y2, x1:x2, :] = 255
            x1, y1, x2, y2 = player.holes["treble_intensity"]["pos"][2 - idx]
            frame[y1:y2, x1:x2, :] = 255
            player.holes.set_frame(frame, 0)
            player.emulate_expression(0)
            assert player.bass_intensity_lock[idx]
            assert player.treble_intensity_lock[idx]

    def test_calc_crescendo(self, player):
        player.pre_time = None
        player.calc_crescendo(100)
        assert player.pre_time == 100

        # slow crescendeo. 4sec min to max
        frame = np.full((600, 800, 3), 0, np.uint8)
        x1, y1, x2, y2 = player.holes["treble_slow_cresc"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.amp_cres_pos = 0
        player.pre_time = 0
        player.calc_crescendo(2)
        assert math.isclose(player.amp_cres_pos, 0.5)
        player.calc_crescendo(4)
        assert math.isclose(player.amp_cres_pos, 1)

        # slow decrescendo. 4sec max to min
        x1, y1, x2, y2 = player.holes["treble_slow_cresc"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 0
        player.holes.set_frame(frame, 0)
        player.calc_crescendo(6)
        assert math.isclose(player.amp_cres_pos, 0.5)
        player.calc_crescendo(8)
        assert math.isclose(player.amp_cres_pos, 0)

        # fast crescendeo. 0.8 sec min to max
        frame = np.full((600, 800, 3), 0, np.uint8)
        x1, y1, x2, y2 = player.holes["treble_slow_cresc"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        x1, y1, x2, y2 = player.holes["treble_fast_cresc"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.amp_cres_pos = 0
        player.pre_time = 0
        player.calc_crescendo(0.4)
        assert math.isclose(player.amp_cres_pos, 0.5)
        player.calc_crescendo(0.8)
        assert math.isclose(player.amp_cres_pos, 1)

        # fast decrescendo. 0.8 sec max to min
        x1, y1, x2, y2 = player.holes["treble_slow_cresc"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 0
        x1, y1, x2, y2 = player.holes["treble_fast_cresc"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.calc_crescendo(1.2)
        assert math.isclose(player.amp_cres_pos, 0.5)
        player.calc_crescendo(1.6)
        assert math.isclose(player.amp_cres_pos, 0)

        # amplifier triggers fast crescendo
        frame = np.full((600, 800, 3), 0, np.uint8)
        x1, y1, x2, y2 = player.holes["treble_slow_cresc"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        x1, y1, x2, y2 = player.holes["amplifier"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.amp_cres_pos = 0
        player.pre_time = 0
        player.calc_crescendo(0.4)
        assert math.isclose(player.amp_cres_pos, 0.5)
        player.calc_crescendo(0.8)
        assert math.isclose(player.amp_cres_pos, 1)

        # amplifier triggers fast crescendo
        x1, y1, x2, y2 = player.holes["treble_slow_cresc"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 0
        x1, y1, x2, y2 = player.holes["amplifier"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.calc_crescendo(1.2)
        assert math.isclose(player.amp_cres_pos, 0.5)
        player.calc_crescendo(1.6)
        assert math.isclose(player.amp_cres_pos, 0)

        # 1st amplifier lock
        frame = np.full((600, 800, 3), 0, np.uint8)
        x1, y1, x2, y2 = player.holes["treble_slow_cresc"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.amp_cres_pos = 0
        player.pre_time = 0
        player.calc_crescendo(2)  # crescendo position is 0.5
        x1, y1, x2, y2 = player.holes["amplifier"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        frame[y1:y2, x1:x2, :] = 0  # 1st amplifier locked
        player.holes.set_frame(frame, 0)
        player.calc_crescendo(10)
        assert math.isclose(player.amp_cres_pos, 0.85)  # max is 0.85
        x1, y1, x2, y2 = player.holes["treble_slow_cresc"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 0
        player.holes.set_frame(frame, 0)
        player.calc_crescendo(20)
        assert math.isclose(player.amp_cres_pos, 0.3)  # min is 0.3
        assert player.amp_lock_range == [0.3, 0.85]

        # 1st amplifier to no amplifier
        x1, y1, x2, y2 = player.holes["amplifier"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.calc_crescendo(20)
        frame[y1:y2, x1:x2, :] = 0  # 1st amplifier unlocked
        player.holes.set_frame(frame, 0)
        player.calc_crescendo(30)
        assert math.isclose(player.amp_cres_pos, 0)  # min is 0
        assert player.amp_lock_range == [0, 1.0]

        # 2nd amplifier lock
        frame = np.full((600, 800, 3), 0, np.uint8)
        x1, y1, x2, y2 = player.holes["treble_slow_cresc"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.amp_cres_pos = 0
        player.pre_time = 0
        player.calc_crescendo(4)  # crescendo position is 1.0
        x1, y1, x2, y2 = player.holes["amplifier"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        frame[y1:y2, x1:x2, :] = 0  # 1st amplifier locked
        player.holes.set_frame(frame, 0)
        player.calc_crescendo(10)
        assert math.isclose(player.amp_cres_pos, 1)  # max is 1
        x1, y1, x2, y2 = player.holes["treble_slow_cresc"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 0
        player.holes.set_frame(frame, 0)
        player.calc_crescendo(20)
        assert math.isclose(player.amp_cres_pos, 0.85)  # min is 0.85
        assert player.amp_lock_range == [0.85, 1]

        # 2nd amplifier to no amplifier
        x1, y1, x2, y2 = player.holes["amplifier"]["pos"][0]
        frame[y1:y2, x1:x2, :] = 255
        player.holes.set_frame(frame, 0)
        player.calc_crescendo(20)
        frame[y1:y2, x1:x2, :] = 0  # 1st amplifier unlocked
        player.holes.set_frame(frame, 0)
        player.calc_crescendo(30)
        assert math.isclose(player.amp_cres_pos, 0)  # min is 0
        assert player.amp_lock_range == [0, 1.0]

