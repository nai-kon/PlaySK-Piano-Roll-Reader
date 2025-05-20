import json

from .base_player import BasePlayer


class Themodist(BasePlayer):
    def __init__(self, confpath, midiobj):
        super().__init__(confpath, midiobj)
        with open(confpath, encoding="utf-8") as f:
            conf = json.load(f)
        self.base_vacuum = conf["expression"]["base"]
        self.accent_vacuum = conf["expression"]["accent"]
        self.bass_vacuum = self.treble_vacuum = self.base_vacuum

    def emulate_off(self):
        super().emulate_off()
        self.bass_vacuum = self.treble_vacuum = self.base_vacuum

    def emulate_expression(self, curtime):
        self.bass_vacuum = self.treble_vacuum = self.base_vacuum
        if self.holes["bass_snakebite"]["is_open"]:
            self.bass_vacuum = self.accent_vacuum

        if self.holes["treble_snakebite"]["is_open"]:
            self.treble_vacuum = self.accent_vacuum


if __name__ == "__main__":
    import os
    import time

    import numpy as np

    from midi_controller import MidiWrap

    midiobj = MidiWrap()
    player = Themodist(os.path.join("playsk_config", "Themodist.json"), midiobj)
    frame = np.full((600, 800, 3), 100, np.uint8)
    start = time.perf_counter()
    for _ in range(10000):
        player.emulate(frame, time.perf_counter())
    end = time.perf_counter()
    t = end - start
    print(t, "per", (t / 10000) * 1000, "ms")
