import glob
import json
import os

import tracker_bars
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

    def get_player_obj(self, player_name: str, midiobj: MidiWrap) -> None | tracker_bars.BasePlayer:
        cls_name = self.player_conf_map.get(player_name, None)
        cls_map = {
            "Player": tracker_bars.BasePlayer,
            "AmpicoB": tracker_bars.AmpicoB,
            "Duo-Art": tracker_bars.DuoArt,
            "WelteT100": tracker_bars.WelteT100,
            "WelteT98": tracker_bars.WelteT98,
            "WelteLicensee": tracker_bars.WelteLicensee,
            "PhillipsDuca": tracker_bars.PhilippsDuca,
            "RecordoA": tracker_bars.RecordoA,
            "RecordoB": tracker_bars.RecordoB,
            "Artecho": tracker_bars.Artecho,
            "Themodist": tracker_bars.Themodist,
            "Themodist_eValve": tracker_bars.Themodist_eValve,
            "Aeolian176note": tracker_bars.Aeolian176note,
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
    assert type(obj.get_player_obj("88 Note white back", None)) is tracker_bars.Player
    assert type(obj.get_player_obj("Ampico B white back", None)) is tracker_bars.AmpicoB
