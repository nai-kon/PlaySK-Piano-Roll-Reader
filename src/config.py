import json
import os

from pydantic import BaseModel

CONFIG_PATH = os.path.join("playsk_config", "config.json")

class ConfigMng(BaseModel):
    last_midi_port: str = ""
    last_tracker: str = ""
    enable_evalve: bool = False
    update_notified_version: str = ""
    window_scale: str = "100%"

    def __init__(self):
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        super().__init__(**data)

    def save_config(self):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=4))

    @property
    def window_scale_ratio(self):
        # return scale ratio. ex) 125% -> 1.25
        return float(self.window_scale.replace("%", "")) / 100

if __name__ == "__main__":
    obj = ConfigMng()
    print(obj.__dict__)

    obj.last_midi_port = "hoge日本語"
    obj.last_tracker = "fuga"
    obj.save_config()

    obj = ConfigMng()
    print(obj.__dict__)
