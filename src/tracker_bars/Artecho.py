import numpy as np
import wx

from .base_player import BasePlayer


class Artecho(BasePlayer):
    def __init__(self, confpath, midiobj):
        """
        The intensity vacuum is based on crescendo position like Ampico B.
        So each intensity has min/max vacuum range which is linked with crescendo position.
        For example, Lv1 intensity with non crescendo is 6.5" and full crescendo is 13".
        Lv1-2-3 with non crescendo is 15", full crescendo with 30.
        I don't know this emulation is correct, but there is no detailed information.
        Just my imagination.
        """

        super().__init__(confpath, midiobj)
        self.bass_cres_pos = 0
        self.treble_cres_pos = 0
        self.cres_rate = 1 / 1.10  # 1.10sec to min to max crescendo/decrescendo
        self.pre_time = None

        self.pianissimo_lock = False
        self.bass_intensity_lock = [False, False, False]  # 1->2->3
        self.treble_intensity_lock = [False, False, False]  # 1->2->3
        self.bass_hammer_rail_lock = False
        self.treble_hammer_rail_lock = False
        self.hammer_rail_velocity_ratio = 0.9  # Same ratio with MidiWrap.hammer_lift_on()

        self.delay_ratio = 0.4
        # vacuum range (W.G) of crescendo min to max
        self.intensity_range = {
            "none": [5.5, 11],
            "1": [6.5, 13],
            "2": [8, 16],
            "21": [10, 20],
            "3": [12.5, 25],
            "31": [13, 26],
            "32": [14, 28],
            "321": [15, 30],
        }

        self.pianissimo_reduce = 1
        self.bass_vacuum = self.treble_vacuum = self.intensity_range["none"][0]
        self.bass_vacuum_pre = self.treble_vacuum_pre = self.intensity_range["none"][0]

    def calc_velocity(self):
        idx = np.digitize([self.bass_vacuum, self.treble_vacuum], bins=self.velocity_bins)
        bass_velocity, treble_velocity = self.velocity[0] + idx
        if self.bass_hammer_rail_lock:
            bass_velocity = int(bass_velocity * self.hammer_rail_velocity_ratio)
        if self.treble_hammer_rail_lock:
            treble_velocity = int(treble_velocity * self.hammer_rail_velocity_ratio)

        return bass_velocity, treble_velocity

    def emulate_off(self):
        super().emulate_off()
        self.pianissimo_lock = False
        self.bass_intensity_lock = [False, False, False]
        self.treble_intensity_lock = [False, False, False]
        self.bass_hammer_rail_lock = False
        self.treble_hammer_rail_lock = False
        self.bass_cres_pos = 0
        self.treble_cres_pos = 0
        self.bass_vacuum = self.treble_vacuum = self.intensity_range["none"][0]
        self.bass_vacuum_pre = self.treble_vacuum_pre = self.intensity_range["none"][0]

    def emulate_pedals(self):
        # sustain pedal
        sustain = self.holes["sustain"]
        if sustain["to_open"]:
            self.midi.sustain_on()

        elif sustain["to_close"]:
            self.midi.sustain_off()

        # hammer rail lift emulation is at calc_velocity()
        if self.holes["bass_hammer_rail"]["is_open"]:
            self.bass_hammer_rail_lock = True
        if self.holes["treble_hammer_rail"]["is_open"]:
            self.treble_hammer_rail_lock = True


    def emulate_expression(self, curtime):
        # cancel operations
        if self.holes["bass_cancel"]["is_open"]:
            self.bass_intensity_lock = [False, False, False]

        if self.holes["treble_cancel"]["is_open"]:
            self.treble_intensity_lock = [False, False, False]

        if self.holes["cancel"]["is_open"]:
            self.bass_hammer_rail_lock = False
            self.treble_hammer_rail_lock = False
            self.pianissimo_lock = False

        # trigger intensity holes
        for idx in range(0, 3):
            if self.holes["bass_intensity"]["is_open"][idx]:
                self.bass_intensity_lock[idx] = True

            if self.holes["treble_intensity"]["is_open"][2 - idx]:
                self.treble_intensity_lock[idx] = True

        if self.holes["pianissimo"]["is_open"]:
            self.pianissimo_lock = True

        self.calc_crescendo(curtime)
        self.calc_expression()

    def calc_crescendo(self, curtime):
        if self.pre_time is None:
            self.pre_time = curtime
        delta_time = curtime - self.pre_time
        self.pre_time = curtime

        if self.holes["bass_cres"]["is_open"]:
            self.bass_cres_pos += delta_time * self.cres_rate
        if self.holes["bass_decres"]["is_open"]:
            self.bass_cres_pos -= delta_time * self.cres_rate

        self.bass_cres_pos = max(0, self.bass_cres_pos)
        self.bass_cres_pos = min(1, self.bass_cres_pos)

        if self.holes["treble_cres"]["is_open"]:
            self.treble_cres_pos += delta_time * self.cres_rate
        if self.holes["treble_decres"]["is_open"]:
            self.treble_cres_pos -= delta_time * self.cres_rate

        self.treble_cres_pos = max(0, self.treble_cres_pos)
        self.treble_cres_pos = min(1, self.treble_cres_pos)


    def calc_expression(self):
        def get_intensity_range(intensity_lock):
            opcode = ""
            if not any(intensity_lock):
                opcode = "none"
            if intensity_lock[2]:
                opcode += "3"
            if intensity_lock[1]:
                opcode += "2"
            if intensity_lock[0]:
                opcode += "1"

            vac_min, vac_max = self.intensity_range.get(opcode, [10, 20])
            return vac_min, vac_max

        vac_min, vac_max = get_intensity_range(self.bass_intensity_lock)
        bass_target_vac = vac_min + self.bass_cres_pos * (vac_max - vac_min)

        vac_min, vac_max = get_intensity_range(self.treble_intensity_lock)
        treble_target_vac = vac_min + self.treble_cres_pos * (vac_max - vac_min)

        if self.pianissimo_lock:
            bass_target_vac -= self.pianissimo_reduce
            treble_target_vac -= self.pianissimo_reduce

        # delay function
        self.bass_vacuum = self.bass_vacuum_pre + (bass_target_vac - self.bass_vacuum_pre) * self.delay_ratio
        self.treble_vacuum = self.treble_vacuum_pre + (treble_target_vac - self.treble_vacuum_pre) * self.delay_ratio
        self.bass_vacuum_pre = self.bass_vacuum
        self.treble_vacuum_pre = self.treble_vacuum


    def draw_tracker(self, wxdc: wx.PaintDC):
        # need override for drawing intensity lock
        self.holes["bass_intensity"]["is_open"][:] = self.bass_intensity_lock[:]
        self.holes["treble_intensity"]["is_open"][:] = self.treble_intensity_lock[::-1]
        self.holes["pianissimo"]["is_open"][0] = self.pianissimo_lock
        self.holes["treble_hammer_rail"]["is_open"][0] = self.treble_hammer_rail_lock
        self.holes["bass_hammer_rail"]["is_open"][0] = self.bass_hammer_rail_lock
        super().draw_tracker(wxdc)


if __name__ == "__main__":
    import os
    import time

    import numpy as np

    from midi_controller import MidiWrap

    midiobj = MidiWrap()
    player = Artecho(os.path.join("playsk_config", "Artecho.json"), midiobj)
    frame = np.full((600, 800, 3), 100, np.uint8)
    start = time.perf_counter()
    for _ in range(10000):
        player.emulate(frame, time.perf_counter())
    end = time.perf_counter()
    t = end - start
    print(t, "per", (t / 10000) * 1000, "ms")
