from player import Player


class PhilippsDuca(Player):
    def __init__(self, confpath, midiobj):
        super().__init__(confpath, midiobj)

        self.pre_time = None
        self.bass_vacuum = 12
        self.treble_vacuum = 12

    def emulate_off(self):
        super().emulate_off()

    def emulate_expression(self, curtime):
        pass

    def emulate_pedals(self):
        # sustain pedal
        if self.holes["sustain_on"]["is_open"]:
            self.midi.sustain_on()

        elif self.holes["sustain_off"]["is_open"]:
            self.midi.sustain_off()


if __name__ == "__main__":
    import os
    import time

    import numpy as np
    from midi_controller import MidiWrap

    midiobj = MidiWrap()
    player = PhilippsDuca(os.path.join("config", "Philipps Duca (no expression).json"), midiobj)
    frame = np.full((600, 800, 3), 100, np.uint8)
    start = time.perf_counter()
    for _ in range(10000):
        player.emulate(frame, time.perf_counter())
    end = time.perf_counter()
    t = end - start
    print(t, "per", (t / 10000) * 1000, "ms")
