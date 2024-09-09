import sys

import pytest

sys.path.append("src/")
import players
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
        ])
        assert player_names == gt_names

    def test_get_player_obj(self, player_mng):
        assert player_mng.get_player_obj("not exists player", None) is None
        assert type(player_mng.get_player_obj("Ampico B white back", None)) is players.AmpicoB
        assert type(player_mng.get_player_obj("Duo-Art white back", None)) is players.DuoArt
        assert type(player_mng.get_player_obj("Philipps Duca (no expression)", None)) is players.PhilippsDuca
        assert type(player_mng.get_player_obj("88 Note white back", None)) is players.BasePlayer
        assert type(player_mng.get_player_obj("Welte Licensee white back", None)) is players.WelteLicensee
        assert type(player_mng.get_player_obj("Welte T100 white back", None)) is players.WelteT100
        assert type(player_mng.get_player_obj("Recordo A (rare) white back", None)) is players.RecordoA
        assert type(player_mng.get_player_obj("Recordo B white back", None)) is players.RecordoB
        assert type(player_mng.get_player_obj("Artecho white back (experimental)", None)) is players.Artecho
        assert type(player_mng.get_player_obj("Welte T98 white back", None)) is players.WelteT98
