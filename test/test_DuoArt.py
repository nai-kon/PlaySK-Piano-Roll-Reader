import sys

import pytest

sys.path.append("src/")
from collections import deque

from DuoArt import DuoArt
from midi_controller import MidiWrap


class TestDuoArt:
    @pytest.fixture
    def player(self):
        midiobj = MidiWrap()
        obj = DuoArt("src/config/Duo-Art white background.json", midiobj)
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
