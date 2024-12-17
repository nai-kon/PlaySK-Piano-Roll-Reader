from collections import deque

from .base_player import BasePlayer


class DuoArt(BasePlayer):
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

        # 8->4->2->1
        self.theme_poss = [0, 0, 0, 0]

        self.bass_vacuum = self.accomp_min
        self.treble_vacuum = self.accomp_min
        self.delay_ratio = 0.25
        self.theme_vacuum_pre = self.theme_min
        self.accomp_vacuum_pre = self.accomp_min
        self.accomp_delay_que = deque([self.accomp_min] * 10, maxlen=10)
        self.theme_delay_que = deque([self.theme_min] * 10, maxlen=10)

    def emulate_off(self):
        super().emulate_off()
        self.accomp_poss = [0, 0, 0, 0]
        self.theme_poss = [0, 0, 0, 0]
        self.bass_vacuum = self.accomp_min
        self.treble_vacuum = self.accomp_min
        self.theme_vacuum_pre = self.theme_min
        self.accomp_vacuum_pre = self.accomp_min
        self.accomp_delay_que = deque([self.accomp_min] * 10, maxlen=10)
        self.theme_delay_que = deque([self.theme_min] * 10, maxlen=10)

    def emulate_expression(self, curtime):
        # accomp 1->2->4->8
        accomp_pos = sum([v * b for v, b in zip((1, 2, 4, 8), self.holes["accomp"]["is_open"])])
        accomp_vacuum = self.accomp_min + (self.accomp_max - self.accomp_min) * (accomp_pos / 15)

        # theme 8->4->2->1
        theme_pos = sum([v * b for v, b in zip((8, 4, 2, 1), self.holes["theme"]["is_open"])])
        theme_vacuum = self.theme_min + (self.theme_max - self.theme_min) * (theme_pos / 15)

        # crash valve
        if theme_vacuum == self.theme_max:
            theme_vacuum = self.crash_valve

        # delay function
        theme_vacuum = self.theme_vacuum_pre + (theme_vacuum - self.theme_vacuum_pre) * self.delay_ratio
        self.theme_vacuum_pre = theme_vacuum
        accomp_vacuum = self.accomp_vacuum_pre + (accomp_vacuum - self.accomp_vacuum_pre) * self.delay_ratio
        self.accomp_vacuum_pre = accomp_vacuum

        if theme_vacuum < accomp_vacuum:
            theme_vacuum = accomp_vacuum + 0.5

        # delay
        cur_accomp = self.accomp_delay_que.popleft()
        self.accomp_delay_que.append(accomp_vacuum)
        cur_theme = self.theme_delay_que.popleft()
        self.theme_delay_que.append(theme_vacuum)

        self.bass_vacuum = cur_theme if self.holes["bass_snakebite"]["is_open"] else cur_accomp
        self.treble_vacuum = cur_theme if self.holes["treble_snakebite"]["is_open"] else cur_accomp


if __name__ == "__main__":
    import os
    import time

    import numpy as np
    from midi_controller import MidiWrap
    midiobj = MidiWrap()
    player = DuoArt(os.path.join("playsk_config", "Duo-Art white back.json"), midiobj)
    frame = np.full((600, 800, 3), 100, np.uint8)
    start = time.perf_counter()
    for _ in range(10000):
        player.emulate(frame, time.perf_counter())
    end = time.perf_counter()
    t = end - start
    print(t, "per", (t / 10000) * 1000, "ms")
