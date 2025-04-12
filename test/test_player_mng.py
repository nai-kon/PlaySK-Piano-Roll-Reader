import sys

import pytest

sys.path.append("src/")
import tracker_bars
from midi_controller import MidiWrap
from player_mng import PlayerMng


class TestPlayerMng:
    @pytest.fixture
    def player_mng(self):
        obj = PlayerMng()
        obj.conf_dir = "src/playsk_config/"
        obj.player_conf_map = obj.init_player_map()
        return obj

    def test_init_player_map(self):
        obj = PlayerMng()
        obj.conf_dir = "test/dummy_player_json/"  # includes two file, but one has no base_class key
        player_map = obj.init_player_map()
        assert player_map == {"Ampico B white back": "AmpicoB"}

    def test_player_list(self, player_mng):
        player_names = sorted(player_mng.player_list)
        gt_names = sorted([
            "88 Note white back",
            "Ampico A white back",
            "Ampico B white back",
            "Duo-Art white back",
            "Philipps Duca (no expression)",
            "Welte Licensee white back",
            "Welte T100 white back",
            "Recordo A (rare) white back",
            "Recordo B white back",
            "Artecho white back (experimental)",
            "Welte T98 white back",
            "Themodist white back",
            "Themodist e-Valve",
            "Aeolian 176-note Pipe Organ",
        ])
        assert player_names == gt_names

    def test_get_player_obj(self, player_mng):
        midiobj = MidiWrap()
        assert player_mng.get_player_obj("not exists player", midiobj) is None
        assert type(player_mng.get_player_obj("Ampico B white back", midiobj)) is tracker_bars.AmpicoB
        assert type(player_mng.get_player_obj("Duo-Art white back", midiobj)) is tracker_bars.DuoArt
        assert type(player_mng.get_player_obj("Philipps Duca (no expression)", midiobj)) is tracker_bars.PhilippsDuca
        assert type(player_mng.get_player_obj("88 Note white back", midiobj)) is tracker_bars.BasePlayer
        assert type(player_mng.get_player_obj("Welte Licensee white back", midiobj)) is tracker_bars.WelteLicensee
        assert type(player_mng.get_player_obj("Welte T100 white back", midiobj)) is tracker_bars.WelteT100
        assert type(player_mng.get_player_obj("Recordo A (rare) white back", midiobj)) is tracker_bars.RecordoA
        assert type(player_mng.get_player_obj("Recordo B white back", midiobj)) is tracker_bars.RecordoB
        assert type(player_mng.get_player_obj("Artecho white back (experimental)", midiobj)) is tracker_bars.Artecho
        assert type(player_mng.get_player_obj("Welte T98 white back", midiobj)) is tracker_bars.WelteT98
        assert type(player_mng.get_player_obj("Themodist white back", midiobj)) is tracker_bars.Themodist
        assert type(player_mng.get_player_obj("Themodist e-Valve", midiobj)) is tracker_bars.Themodist_eValve
        assert type(player_mng.get_player_obj("Aeolian 176-note Pipe Organ", midiobj)) is tracker_bars.Aeolian176note
