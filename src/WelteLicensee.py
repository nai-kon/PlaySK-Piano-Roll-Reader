from WelteT100 import WelteT100


class WelteLicensee(WelteT100):
    def __init__(self, confpath, midiobj):
        super().__init__(confpath, midiobj)

        self.bass_slow_cres_sec = 4.92   # min to max
        self.bass_slow_decres_sec = 5.6  # max to min
        self.bass_fast_cres_sec = 0.5
        self.bass_fast_decres_sec = 0.15

        self.treble_slow_cres_sec = 4.92   # min to max
        self.treble_slow_decres_sec = 5.6  # max to min
        self.treble_fast_cres_sec = 0.5
        self.treble_fast_decres_sec = 0.15

        self.mf_hook_pos = 0.47
        self.pre_time = None
        self.min_vacuum = 6     # in W.G
        self.max_vacuum = 35    # in W.G

        self.bass_vacuum = self.min_vacuum
        self.treble_vacuum = self.min_vacuum


if __name__ == "__main__":
    import numpy as np
    import time
    import os
    from midi_controller import MidiWrap
    midiobj = MidiWrap()
    player = WelteLicensee(os.path.join("config", "Ampico B white background.json"), midiobj)
    frame = np.full((600, 800, 3), 100, np.uint8)
    start = time.perf_counter()
    for _ in range(10000):
        player.emulate(frame, time.perf_counter())
    end = time.perf_counter()
    t = end - start
    print(t, "per", (t / 10000) * 1000, "ms")
