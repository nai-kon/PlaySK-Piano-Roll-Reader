import math
import sys

import numpy as np
import pytest

sys.path.append("src/")
import wx

import tracker_bars
from midi_controller import MidiWrap

app = wx.App()

class TestAmpicoA:
    @pytest.fixture
    def player(self):
        midiobj = MidiWrap()
        obj = tracker_bars.AmpicoA("src/playsk_config/Ampico A Brilliant.json", midiobj)
        return obj

    def test_emulate_off(self, player):
        player.amplifier_pos = 0.5
        player.bass_crescendo_vacuum = player.max_vacuum
        player.treble_crescendo_vacuum = player.max_vacuum
        player.bass_intensity_lock = [True, True, True]
        player.treble_intensity_lock = [True, True, True]
        player.bass_vacuum = player.max_vacuum
        player.treble_vacuum = player.max_vacuum
        player.emulate_off()
        assert player.amplifier_pos == 0
        assert player.bass_crescendo_vacuum == player.min_vacuum
        assert player.treble_crescendo_vacuum == player.min_vacuum
        assert player.bass_intensity_lock == [False, False, False]
        assert player.treble_intensity_lock == [False, False, False]
        assert player.bass_vacuum == player.min_vacuum
        assert player.treble_vacuum == player.min_vacuum

    def test_emulate_intensity(self, player):
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

    # amplifier test. Each intensity triggers different level of amplifier position
    @pytest.mark.parametrize("bass_intensities, treble_intensities, amplifier_pos_0sec, amplifier_pos_500msec, amplifier_pos_1sec", [
        # bass
        ((), (), (0), (0), (0)),
        ((2,), (), (0), (0), (0)),
        ((4,), (), (0), (0), (0)),
        ((2, 4), (), (0), (0), (0)),
        ((6,), (), (0), (0.2), (0.2)),
        ((2, 6), (), (0), (0.5), (0.5)),
        ((4, 6), (), (0), (1.0), (1.0)),
        ((2, 4, 6), (), (0), (1.0), (1.0)),
        # treble
        ((), (2,), (0), (0), (0)),
        ((), (4,), (0), (0), (0)),
        ((), (2, 4), (0), (0), (0)),
        ((), (6,), (0), (0.2), (0.2)),
        ((), (2, 6), (0), (0.5), (0.5)),
        ((), (4, 6), (0), (1.0), (1.0)),
        ((), (2, 4, 6), (0), (1.0), (1.0)),
        # combine
        ((2,), (6,), (0), (0.2), (0.2)),
        ((4,), (6,), (0), (0.2), (0.2)),
        ((6,), (6,), (0), (0.2), (0.2)),
        ((2, 6), (2,), (0), (0.5), (0.5)),
        ((2, 6), (4,), (0), (0.5), (0.5)),
        ((2, 6), (6,), (0), (0.5), (0.5)),
        ((2, 6), (2, 6), (0), (0.5), (0.5)),
        ((2, 6), (4, 6), (0), (1.0), (1.0)),
        ((4, 6), (2,), (0), (1.0), (1.0)),
        ((4, 6), (4,), (0), (1.0), (1.0)),
        ((4, 6), (6,), (0), (1.0), (1.0)),
        ((4, 6), (2, 6), (0), (1.0), (1.0)),
        ((4, 6), (4, 6), (0), (1.0), (1.0)),
    ])
    def test_emulate_amplifier(self, bass_intensities, treble_intensities, amplifier_pos_0sec, amplifier_pos_500msec, amplifier_pos_1sec, player):
        player.emulate_off()
        frame = np.full((600, 800, 3), 0, np.uint8)

        for port in bass_intensities:
            port_map = {2: 0, 4: 1, 6: 2}
            x1, y1, x2, y2 = player.holes["bass_intensity"]["pos"][port_map[port]]
            frame[y1:y2, x1:x2, :] = 255

        for port in treble_intensities:
            port_map = {2: 2, 4: 1, 6: 0}
            x1, y1, x2, y2 = player.holes["treble_intensity"]["pos"][port_map[port]]
            frame[y1:y2, x1:x2, :] = 255

        player.holes.set_frame(frame, 0)
        player.emulate_expression(0)
        assert math.isclose(player.amplifier_pos, amplifier_pos_0sec)
        player.emulate_expression(0.5)
        assert math.isclose(player.amplifier_pos, amplifier_pos_500msec)
        player.emulate_expression(1)
        assert math.isclose(player.amplifier_pos, amplifier_pos_1sec)

    def test_emulate_amplifier2(self, player):
        # crescendo also activates amplifier
        for part in ("bass", "treble"):
            player.emulate_off()
            player.delay_ratio = 1  # disable delay for test
            frame = np.full((600, 800, 3), 0, np.uint8)
            x1, y1, x2, y2 = player.holes[f"{part}_slow_cresc"]["pos"][0]
            frame[y1:y2, x1:x2, :] = 255
            player.holes.set_frame(frame, 0)
            player.pre_time = 0

            # crescendo to max
            player.calc_expression(8)
            player.emulate_expression(8)
            assert math.isclose(player.amplifier_pos, 1.0)

            # decrescendo to min
            frame[y1:y2, x1:x2, :] = 0
            player.holes.set_frame(frame, 0)
            player.calc_expression(16)
            player.emulate_expression(16)
            assert math.isclose(player.amplifier_pos, 0)

    def test_calc_crescendo(self, player):

        for part in ("bass", "treble"):
            player.emulate_off()
            # slow crescendo. 8sec min to max with no intensity
            frame = np.full((600, 800, 3), 0, np.uint8)
            x1, y1, x2, y2 = player.holes[f"{part}_slow_cresc"]["pos"][0]
            frame[y1:y2, x1:x2, :] = 255
            player.holes.set_frame(frame, 0)
            player.pre_time = 0
            player.calc_expression(8)
            if part == "bass":
                assert math.isclose(player.bass_crescendo_vacuum, player.max_vacuum)
                assert math.isclose(player.treble_crescendo_vacuum, player.min_vacuum)
            else:
                assert math.isclose(player.bass_crescendo_vacuum, player.min_vacuum)
                assert math.isclose(player.treble_crescendo_vacuum, player.max_vacuum)

            # slow decrescendo. 8sec max to min with no intensity
            x1, y1, x2, y2 = player.holes[f"{part}_slow_cresc"]["pos"][0]
            frame[y1:y2, x1:x2, :] = 0
            player.holes.set_frame(frame, 0)
            player.calc_expression(8)
            if part == "bass":
                assert math.isclose(player.bass_crescendo_vacuum, player.min_vacuum)
                assert math.isclose(player.treble_crescendo_vacuum, player.min_vacuum)
            else:
                assert math.isclose(player.bass_crescendo_vacuum, player.min_vacuum)
                assert math.isclose(player.treble_crescendo_vacuum, player.min_vacuum)

            # fast crescendo. 2 sec min to max
            player.emulate_off()
            frame = np.full((600, 800, 3), 0, np.uint8)
            x1, y1, x2, y2 = player.holes[f"{part}_slow_cresc"]["pos"][0]
            frame[y1:y2, x1:x2, :] = 255
            x1, y1, x2, y2 = player.holes[f"{part}_fast_cresc"]["pos"][0]
            frame[y1:y2, x1:x2, :] = 255
            player.holes.set_frame(frame, 0)
            player.calc_expression(2)
            if part == "bass":
                assert math.isclose(player.bass_crescendo_vacuum, player.max_vacuum)
                assert math.isclose(player.treble_crescendo_vacuum, player.min_vacuum)
            else:
                assert math.isclose(player.bass_crescendo_vacuum, player.min_vacuum)
                assert math.isclose(player.treble_crescendo_vacuum, player.max_vacuum)

            # fast decrescendo. 2 sec max to min
            x1, y1, x2, y2 = player.holes[f"{part}_slow_cresc"]["pos"][0]
            frame[y1:y2, x1:x2, :] = 0
            x1, y1, x2, y2 = player.holes[f"{part}_fast_cresc"]["pos"][0]
            frame[y1:y2, x1:x2, :] = 255
            player.holes.set_frame(frame, 0)
            player.calc_expression(2)
            if part == "bass":
                assert math.isclose(player.bass_crescendo_vacuum, player.min_vacuum)
                assert math.isclose(player.treble_crescendo_vacuum, player.min_vacuum)
            else:
                assert math.isclose(player.bass_crescendo_vacuum, player.min_vacuum)
                assert math.isclose(player.treble_crescendo_vacuum, player.min_vacuum)
