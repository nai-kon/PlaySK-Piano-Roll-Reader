import sys

import pytest

sys.path.append("src/")

from midi_controller import MidiWrap
from WelteT100 import WelteT100


class TestWelteT100:
    @pytest.fixture
    def player(self):
        midiobj = MidiWrap()
        obj = WelteT100("src/config/Welte T100 white back.json", midiobj)
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
