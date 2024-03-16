import sys

import numpy as np
import pytest

sys.path.append("src/")
from collections import deque

import players
from midi_controller import MidiWrap


class TestDuoArt:
    @pytest.fixture
    def player(self):
        midiobj = MidiWrap()
        obj = players.DuoArt("src/playsk_config/Duo-Art white back.json", midiobj)
        return obj

    def test_emulate_off(self, player):
        player.bass_vacuum = 40
        player.treble_vacuum = 40
        player.theme_vacuum_pre = 30
        player.accomp_vacuum_pre = 30
        player.theme_delay_que = deque([40] * 10, maxlen=10)
        player.accomp_delay_que = deque([40] * 10, maxlen=10)
        player.emulate_off()
        assert player.bass_vacuum == player.accomp_min
        assert player.treble_vacuum == player.accomp_min
        assert player.theme_vacuum_pre == player.theme_min
        assert player.accomp_vacuum_pre == player.accomp_min
        assert player.theme_delay_que == deque([player.theme_min] * 10, maxlen=10)
        assert player.accomp_delay_que == deque([player.accomp_min] * 10, maxlen=10)

    @pytest.mark.parametrize("accomp_ports, theme_ports, snake_bites, expect", [
        # ((accomp open ports), (theme open ports), (bass_snakebite, treble_snakebite), (bass expect vacuum, treble expect vacuum))
        ((), (), (False, True), (5, 5.5)),
        ((0,), (3,), (False, True), (6.5, 7.3)),
        ((0,), (), (False, True), (6.5, 7)),
        ((1,), (2,), (False, True), (8, 9.1)),
        ((1, 0), (3, 2), (False, True), (9.6, 11)),
        ((2,), (1,), (False, True), (11.1, 12.8)),
        ((2, 0), (1, 3), (False, True), (12.6, 14.6)),
        ((2, 1), (1, 2), (False, True), (14.2, 16.5)),
        ((2, 1, 0), (1, 2, 3), (False, True), (15.7, 18.3)),
        ((3,), (0,), (False, True), (17.2, 20.1)),
        ((3, 0), (0, 3), (False, True), (18.8, 22)),
        ((3, 1), (0, 2), (False, True), (20.3, 23.8)),
        ((3, 1, 0), (0, 2, 3), (False, True), (21.8, 25.6)),
        ((3, 2), (0, 1), (False, True), (23.4, 27.5)),
        ((3, 2, 0), (0, 1, 3), (False, True), (24.9, 29.3)),
        ((3, 2, 1), (0, 1, 2), (False, True), (26.4, 31.1)),
        ((3, 2, 1, 0), (0, 1, 2, 3), (False, True), (28, 40)),
    ])
    def test_expression(self, accomp_ports, theme_ports, snake_bites, expect, player):
        player.delay_ratio = 1
        frame = np.full((600, 800, 3), 0, np.uint8)
        for accomp_port in accomp_ports:
            pos = player.holes["accomp"]["pos"][accomp_port]
            frame[pos[1]: pos[3], pos[0]: pos[2]] = 255
        for theme_port in theme_ports:
            pos = player.holes["theme"]["pos"][theme_port]
            frame[pos[1]: pos[3], pos[0]: pos[2]] = 255

        bass_snake, treble_snake = snake_bites
        if bass_snake:
            pos = player.holes["bass_snakebite"]["pos"][0]
            frame[pos[1]: pos[3], pos[0]: pos[2]] = 255
        if treble_snake:
            pos = player.holes["treble_snakebite"]["pos"][0]
            frame[pos[1]: pos[3], pos[0]: pos[2]] = 255

        for _ in range(len(player.theme_delay_que) + 1):
            player.holes.set_frame(frame, 0)
            player.emulate_expression(0)

        assert expect[0] - 0.1 <  player.bass_vacuum < expect[0] + 0.1
        assert expect[1] - 0.1 <  player.treble_vacuum < expect[1] + 0.1


