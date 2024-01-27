import sys

import pytest

sys.path.append("src/")
from midi_controller import MidiWrap
from RecordoA import RecordoA


class TestRecordoA:
    @pytest.fixture
    def player(self):
        midiobj = MidiWrap()
        obj = RecordoA("src/config/Recordo A (rare) white back.json", midiobj)
        return obj

    def test_emulate_off(self, player):
        player.bass_vacuum = 40
        player.treble_vacuum = 40
        player.emulate_off()
        assert player.bass_vacuum == player.intensities[0]
        assert player.treble_vacuum == player.intensities[0]
