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
        if cls_name is not None:
            confpath = os.path.join("config", f"{player_name}.json")
            match cls_name:
                case "Player":
                    return Player(confpath, midiobj)
                case "AmpicoB":
                    return AmpicoB(confpath, midiobj)
                case "Duo-Art":
                    return DuoArt(confpath, midiobj)
                case "WelteT100":
                    return WelteT100(confpath, midiobj)
                case "WelteLicensee":
                    return WelteLicensee(confpath, midiobj)
                case "PhillipsDuca":
                    return PhilippsDuca(confpath, midiobj)

        return None


if __name__ == "__main__":
    obj = PlayerMng()
    print(obj.player_list)
    assert obj.get_player_obj("not exists", None) is None
    assert type(obj.get_player_obj("88Note white background", None)) is Player
    assert type(obj.get_player_obj("AmpicoB white background", None)) is AmpicoB
