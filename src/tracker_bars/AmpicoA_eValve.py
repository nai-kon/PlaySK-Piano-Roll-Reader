from .AmpicoA import AmpicoA


class AmpicoA_eValve(AmpicoA):

    def emulate_expression(self, curtime):
        super().emulate_expression(curtime)

        # send e-valve signal
        if self.holes["bass_slow_cresc"]["to_open"]:
            self.midi.note_on(16, velocity=64)
        elif self.holes["bass_slow_cresc"]["to_close"]:
            self.midi.note_off(16, velocity=64)

        if self.holes["bass_intensity"]["to_open"][0]:
            self.midi.note_on(17, velocity=64)
        elif self.holes["bass_intensity"]["to_close"][0]:
            self.midi.note_off(17, velocity=64)

        if self.holes["sustain"]["to_open"]:
            self.midi.note_on(18, velocity=64)
        elif self.holes["sustain"]["to_close"]:
            self.midi.note_off(18, velocity=64)

        if self.holes["bass_intensity"]["to_open"][1]:
            self.midi.note_on(19, velocity=64)
        elif self.holes["bass_intensity"]["to_close"][1]:
            self.midi.note_off(19, velocity=64)

        if self.holes["bass_fast_cresc"]["to_open"]:
            self.midi.note_on(20, velocity=64)
        elif self.holes["bass_fast_cresc"]["to_close"]:
            self.midi.note_off(20, velocity=64)

        if self.holes["bass_intensity"]["to_open"][2]:
            self.midi.note_on(21, velocity=64)
        elif self.holes["bass_intensity"]["to_close"][2]:
            self.midi.note_off(21, velocity=64)

        if self.holes["bass_cancel"]["to_open"]:
            self.midi.note_on(22, velocity=64)
        elif self.holes["bass_cancel"]["to_close"]:
            self.midi.note_off(22, velocity=64)

        if self.holes["treble_cancel"]["to_open"]:
            self.midi.note_on(107, velocity=64)
        elif self.holes["treble_cancel"]["to_close"]:
            self.midi.note_off(107, velocity=64)

        if self.holes["treble_intensity"]["to_open"][0]:
            self.midi.note_on(108, velocity=64)
        elif self.holes["treble_intensity"]["to_close"][0]:
            self.midi.note_off(108, velocity=64)

        if self.holes["treble_fast_cresc"]["to_open"]:
            self.midi.note_on(109, velocity=64)
        elif self.holes["treble_fast_cresc"]["to_close"]:
            self.midi.note_off(109, velocity=64)

        if self.holes["treble_intensity"]["to_open"][1]:
            self.midi.note_on(110, velocity=64)
        elif self.holes["treble_intensity"]["to_close"][1]:
            self.midi.note_off(110, velocity=64)

        if self.holes["soft"]["to_open"]:
            self.midi.note_on(111, velocity=64)
        elif self.holes["soft"]["to_close"]:
            self.midi.note_off(111, velocity=64)

        if self.holes["treble_intensity"]["to_open"][2]:
            self.midi.note_on(112, velocity=64)
        elif self.holes["treble_intensity"]["to_close"][2]:
            self.midi.note_off(112, velocity=64)

        if self.holes["treble_slow_cresc"]["to_open"]:
            self.midi.note_on(113, velocity=64)
        elif self.holes["treble_slow_cresc"]["to_close"]:
            self.midi.note_off(113, velocity=64)

if __name__ == "__main__":
    import os
    import time

    import numpy as np

    from midi_controller import MidiWrap

    midiobj = MidiWrap()
    player = AmpicoA(os.path.join("playsk_config", "Ampico A Brilliant.json"), midiobj)
    frame = np.full((600, 800, 3), 100, np.uint8)
    start = time.perf_counter()
    for _ in range(10000):
        player.emulate(frame, time.perf_counter())
    end = time.perf_counter()
    t = end - start
    print(t, "per", (t / 10000) * 1000, "ms")
