import os
import json


class ConfigMng():
    _path = os.path.join("config", "config.json")

    def __init__(self):
        self.last_midi_port = ""
        self.last_tracker = ""
        self.skip_notify_ver = ""

        self.load_config()

    def load_config(self):
        if not os.path.exists(ConfigMng._path):
            return

        with open(ConfigMng._path, encoding="utf-8") as f:
            v = json.load(f)
            self.last_midi_port = v.get("last_midi_port", "")
            self.last_tracker = v.get("last_tracker", "")
            self.skip_notify_ver = v.get("skip_notify_ver", "")

    def save_config(self):
        with open(ConfigMng._path, "w", encoding="utf-8") as f:
            json.dump(self.__dict__, f, indent=4)


if __name__ == "__main__":
    obj = ConfigMng()
    print(obj.__dict__)

    obj.last_midi_port = "hoge"
    obj.last_tracker = "fuga"
    obj = None

    obj = ConfigMng()
    print(obj.__dict__)
