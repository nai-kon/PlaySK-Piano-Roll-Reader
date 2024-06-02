import glob
import json
import os

import players
from midi_controller import MidiWrap


class PlayerMng:
    def __init__(self) -> None:
        self.conf_dir: str = "playsk_config/"
        self.player_conf_map: dict[str, str] = self.init_player_map()

    def init_player_map(self) -> dict[str, str]:
        conf_map = {}
        for path in glob.glob(self.conf_dir + "*.json"):
            with open(path, encoding="utf-8") as f:
                conf = json.load(f)

            cls_name = conf.get("base_class", None)
            if cls_name is not None:
                fname = os.path.basename(path).replace(".json", "")
                conf_map[fname] = cls_name

        return conf_map

    @property
    def player_list(self) -> list[str]:
        return sorted(self.player_conf_map.keys())

    def get_player_obj(self, player_name: str, midiobj: MidiWrap) -> None | players.BasePlayer:
        cls_name = self.player_conf_map.get(player_name, None)
        cls_map = {
            "Player": players.BasePlayer,
            "AmpicoB": players.AmpicoB,
            "Duo-Art": players.DuoArt,
            "WelteT100": players.WelteT100,
            "WelteT98": players.WelteT98,
            "WelteLicensee": players.WelteLicensee,
            "PhillipsDuca": players.PhilippsDuca,
            "RecordoA": players.RecordoA,
            "RecordoB": players.RecordoB,
            "Artecho": players.Artecho,
            "Themodist": players.Themodist,
        }
        clsobj = cls_map.get(cls_name, None)
        if clsobj is not None:
            confpath = os.path.join(self.conf_dir, f"{player_name}.json")
            return clsobj(confpath, midiobj)
        else:
            return None


if __name__ == "__main__":
    obj = PlayerMng()
    print(obj.player_list)
    print(type(obj.get_player_obj("88 Note white back", None)))
    assert obj.get_player_obj("not exists", None) is None
    assert type(obj.get_player_obj("88 Note white back", None)) is players.Player
    assert type(obj.get_player_obj("Ampico B white back", None)) is players.AmpicoB
