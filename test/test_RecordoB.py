import sys

import pytest

sys.path.append("src/")
from midi_controller import MidiWrap
from RecordoB import RecordoB


class TestRecordoB:
    @pytest.fixture
    def player(self):
        midiobj = MidiWrap()
        obj = RecordoB("src/config/Recordo B white back.json", midiobj)
        return obj

    def test_emulate_off(self, player):
        player.bass_vacuum = 40
        player.treble_vacuum = 40
        player.emulate_off()
        assert player.bass_vacuum == player.intensities[0]
        assert player.treble_vacuum == player.intensities[0]
