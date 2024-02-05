import sys

import pytest

sys.path.append("src/")
from AmpicoB import AmpicoB
from midi_controller import MidiWrap


class TestAmpicoB:
    @pytest.fixture
    def player(self):
        midiobj = MidiWrap()
        obj = AmpicoB("src/config/Ampico B white back.json", midiobj)
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
