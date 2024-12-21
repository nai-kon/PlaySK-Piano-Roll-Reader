from .Themodist import Themodist


class Themodist_eValve(Themodist):
    def __init__(self, confpath, midiobj):
        super().__init__(confpath, midiobj)
        self.sustein_midi_no = 18
        self.bass_snake_midi_no = 19
        self.treble_snake_midi_no = 109

    def emulate_expression(self, curtime):
        super().emulate_expression(curtime)

        # send e-valve midi signal
        if self.holes["bass_snakebite"]["to_open"]:
            self.midi.note_on(self.bass_snake_midi_no, velocity=64)
        elif self.holes["bass_snakebite"]["to_close"]:
            self.midi.note_off(self.bass_snake_midi_no, velocity=64)

        if self.holes["treble_snakebite"]["to_open"]:
            self.midi.note_on(self.treble_snake_midi_no, velocity=64)
        elif self.holes["treble_snakebite"]["to_close"]:
            self.midi.note_off(self.treble_snake_midi_no, velocity=64)

    def emulate_pedals(self):
        super().emulate_pedals()

        # send e-valve midi signal
        sustain = self.holes["sustain"]
        if sustain["to_open"]:
            self.midi.note_on(self.sustein_midi_no, velocity=64)
        elif sustain["to_close"]:
            self.midi.note_off(self.sustein_midi_no, velocity=64)


if __name__ == "__main__":
    import os
    import time

    import numpy as np
    from midi_controller import MidiWrap
    midiobj = MidiWrap()
    player = Themodist(os.path.join("playsk_config", "Themodist e-Valve.json"), midiobj)
    frame = np.full((600, 800, 3), 100, np.uint8)
    start = time.perf_counter()
    for _ in range(10000):
        player.emulate(frame, time.perf_counter())
    end = time.perf_counter()
    t = end - start
    print(t, "per", (t / 10000) * 1000, "ms")
