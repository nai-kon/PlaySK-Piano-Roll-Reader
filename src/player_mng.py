import glob
import os
import json
from player import Player
from AmpicoB import AmpicoB
from WelteT100 import WelteT100
from WelteLicensee import WelteLicensee


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
            if cls_name == "AmpicoB":
                return AmpicoB(confpath, midiobj)

            elif cls_name == "Player":
                return Player(confpath, midiobj)

            elif cls_name == "WelteT100":
                return WelteT100(confpath, midiobj)

            elif cls_name == "WelteLicensee":
                return WelteLicensee(confpath, midiobj)



        return None


if __name__ == "__main__":
    obj = PlayerMng()
    print(obj.player_list)
    assert obj.get_player_obj("not exists", None) is None
    assert type(obj.get_player_obj("88Note white background", None)) is Player
    assert type(obj.get_player_obj("AmpicoB white background", None)) is AmpicoB
