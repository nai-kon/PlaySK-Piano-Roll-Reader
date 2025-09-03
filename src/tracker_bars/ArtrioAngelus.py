import math

from .base_player import BasePlayer


class ArtrioAngelus(BasePlayer):
    def __init__(self, confpath, midiobj):
        super().__init__(confpath, midiobj)
        self.solo_base = 6.5
        self.solo_adds = [
            10,     # port 104, solo forzando
            2.5,    # port 105, solo 4
            2.5,    # port 108, solo 3
            2.5,    # port 109, solo 2
            2.5,    # port 111, solo 1
        ]
        # if not open hole, reduce vacuum by multiply solo vacuum
        self.accomp_multiply = [
            0.9,
            0.9,
            0.9,
        ]
        self.leaker_multiply = 1.3
        self.bass_vacuum = self.treble_vacuum = self.solo_base - 1

    def emulate_off(self):
        super().emulate_off()
        self.bass_vacuum = self.treble_vacuum = self.solo_base - 1

    def emulate_expression(self, curtime):
        solo_vacuum = self.solo_base + sum([v * b for v, b in zip(self.solo_adds, self.holes["solo"]["is_open"])])
        accomp_vaccum = solo_vacuum * math.prod([max(v, int(b)) for v, b in zip(self.accomp_multiply, self.holes["accomp"]["is_open"])])
        accomp_vaccum = max(accomp_vaccum, self.solo_base - 1)

        self.bass_vacuum = solo_vacuum if self.holes["bass_melodant"]["is_open"] else accomp_vaccum
        self.treble_vacuum = solo_vacuum if self.holes["treble_melodant"]["is_open"] else accomp_vaccum
        if self.holes["leaker"]["is_open"]:
            self.bass_vacuum *= self.leaker_multiply
            self.treble_vacuum *= self.leaker_multiply


if __name__ == "__main__":
    import os
    import time

    import numpy as np

    from midi_controller import MidiWrap

    midiobj = MidiWrap()
    player = ArtrioAngelus(os.path.join("playsk_config", "Artrio Angelus.json"), midiobj)
    frame = np.full((600, 800, 3), 100, np.uint8)
    start = time.perf_counter()
    for _ in range(10000):
        player.emulate(frame, time.perf_counter())
    end = time.perf_counter()
    t = end - start
    print(t, "per", (t / 10000) * 1000, "ms")
