import glob
import json
import os

from AmpicoB import AmpicoB
from DuoArt import DuoArt
from player import Player
from WelteLicensee import WelteLicensee
from WelteT100 import WelteT100
from PhilippsDuca import PhilippsDuca


class PlayerMng():
    def __init__(self):
        self._player_conf_map = self.init_player_map()

    def init_player_map(self):
        conf_map = {}
        for path in glob.glob(os.path.join("config", "*.json")):
            with open(path, encoding="utf-8") as f:
                conf = json.load(f)

            cls_name = conf.get("base_class", None)
            if cls_name is not None:
                fname = os.path.basename(path).replace(".json", "")
                conf_map[fname] = cls_name

        return conf_map

    @property
    def player_list(self):
        return list(self._player_conf_map.keys())

    def get_player_obj(self, player_name, midiobj):
        cls_name = self._player_conf_map.get(player_name, None)
        cls_map = {
            "Player": Player,
            "AmpicoB": AmpicoB,
            "Duo-Art": DuoArt,
            "WelteT100": WelteT100,
            "WelteLicensee": WelteLicensee,
            "PhillipsDuca": PhilippsDuca,
        }
        clsobj = cls_map.get(cls_name, None)
        if clsobj is not None:
            confpath = os.path.join("config", f"{player_name}.json")
            return clsobj(confpath, midiobj)
        else:
            return None


if __name__ == "__main__":
    obj = PlayerMng()
    print(obj.player_list)
    assert obj.get_player_obj("not exists", None) is None
    assert type(obj.get_player_obj("88 Note white background", None)) is Player
    assert type(obj.get_player_obj("Ampico B white background", None)) is AmpicoB
