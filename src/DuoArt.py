from collections import deque

from player import Player


class DuoArt(Player):
    def __init__(self, confpath, midiobj):
        super().__init__(confpath, midiobj)

        self.pre_time = None
        self.accomp_min = 5  # none
        self.accomp_max = 28  # 1-2-4-8
        self.theme_min = 5.5  # none
        self.theme_max = 33  # 1-2-4-8
        self.crash_valve = 40

        # 1->2->4->8
        self.accomp_poss = [0, 0, 0, 0]
        self.accomp_delay_rates = (
            1 / 0.05,
            1 / 0.06,
            1 / 0.08,
            1 / 0.12
        )

        # 8->4->2->1
        self.theme_poss = [0, 0, 0, 0]
        self.theme_delay_rates = (
            1 / 0.12,
            1 / 0.08,
            1 / 0.06,
            1 / 0.05,
        )

        self.bass_vacuum = self.accomp_min
        self.treble_vacuum = self.accomp_min
        self.accomp_delay_que = deque([self.accomp_min] * 10, maxlen=10)
        self.theme_delay_que = deque([self.theme_min] * 10, maxlen=10)

    def emulate_off(self):
        super().emulate_off()
        self.accomp_poss = [0, 0, 0, 0]
        self.theme_poss = [0, 0, 0, 0]
        self.bass_vacuum = self.accomp_min
        self.treble_vacuum = self.accomp_min

    def emulate_expression(self, curtime):
        if self.pre_time is None:
            self.pre_time = curtime
        delta_time = curtime - self.pre_time

        # accomp 1->2->4->8
        for i, (size, open, delay_rate) in enumerate(zip((1, 2, 4, 8), self.holes["accomp"]["is_open"], self.accomp_delay_rates)):
            if open:
                self.accomp_poss[i] += (delta_time * delay_rate) * size
            else:
                self.accomp_poss[i] -= (delta_time * delay_rate) * size
            self.accomp_poss[i] = max(self.accomp_poss[i], 0)
            self.accomp_poss[i] = min(self.accomp_poss[i], size)

        accomp_pos = sum(self.accomp_poss)
        accomp_vacuum = self.accomp_min + (self.accomp_max - self.accomp_min) * (accomp_pos / 15)

        # theme 8->4->2->1
        for i, (size, open, delay_rate) in enumerate(zip((8, 4, 2, 1), self.holes["theme"]["is_open"], self.theme_delay_rates)):
            if open:
                self.theme_poss[i] += (delta_time * delay_rate) * size
            else:
                self.theme_poss[i] -= (delta_time * delay_rate) * size
            self.theme_poss[i] = max(self.theme_poss[i], 0)
            self.theme_poss[i] = min(self.theme_poss[i], size)

        theme_pos = sum(self.theme_poss)
        theme_vacuum = self.theme_min + (self.theme_max - self.theme_min) * (theme_pos / 15)

        if theme_vacuum < accomp_vacuum:
            theme_vacuum = accomp_vacuum + 0.5

        if theme_vacuum == self.theme_max:
            theme_vacuum = self.crash_valve

        # delay
        cur_accomp = self.accomp_delay_que.popleft()
        self.accomp_delay_que.append(accomp_vacuum)
        cur_theme = self.theme_delay_que.popleft()
        self.theme_delay_que.append(theme_vacuum)

        self.bass_vacuum = cur_theme if self.holes["bass_snakebite"]["is_open"] else cur_accomp
        self.treble_vacuum = cur_theme if self.holes["treble_snakebite"]["is_open"] else cur_accomp


if __name__ == "__main__":
    import numpy as np
    import time
    import os
    from midi_controller import MidiWrap
    midiobj = MidiWrap()
    player = DuoArt(os.path.join("config", "Duo-Art white background.json"), midiobj)
    frame = np.full((600, 800, 3), 100, np.uint8)
    start = time.perf_counter()
    for _ in range(10000):
        player.emulate(frame, time.perf_counter())
    end = time.perf_counter()
    t = end - start
    print(t, "per", (t / 10000) * 1000, "ms")
