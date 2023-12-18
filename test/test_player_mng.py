import sys

import pytest

sys.path.append("src/")
from src.AmpicoB import AmpicoB
from src.DuoArt import DuoArt
from src.PhilippsDuca import PhilippsDuca
from src.player import Player
from src.player_mng import PlayerMng
from src.WelteLicensee import WelteLicensee
from src.WelteT100 import WelteT100


class TestPlayerMng():
    @pytest.fixture
    def player_mng(self):
        obj = PlayerMng()
        obj.conf_dir = "src/config/"
        obj.player_conf_map = obj.init_player_map()
        return obj

    def test_player_list(self, player_mng):
        player_names = sorted(player_mng.player_list)
        gt_names = sorted([
            "88 Note white background",
            "Ampico B white background",
            "Duo-Art white background",
            "Philipps Duca (no expression)",
            "Welte Licensee white back",
            "Welte T100 white back"
        ])
        print(player_names)
        assert player_names == gt_names

    # def test_get_player_obj(self, player_mng):
    #     assert player_mng.get_player_obj("not exists player", None) is None
    #     assert isinstance(player_mng.get_player_obj("Ampico B white background", None), AmpicoB)
    #     assert type(player_mng.get_player_obj("Duo-Art white background", None)) is DuoArt
    #     assert type(player_mng.get_player_obj("Philipps Duca (no expression)", None)) is PhilippsDuca
    #     assert type(player_mng.get_player_obj("88 Note white background", None)) is Player
    #     assert type(player_mng.get_player_obj("Welte Licensee white back", None)) is WelteLicensee
    #     assert type(player_mng.get_player_obj("Welte T100 white back", None)) is WelteT100
