from player import Player


class RecordoA(Player):
    def __init__(self, confpath, midiobj):
        super().__init__(confpath, midiobj)

        # hammer rail halfway between next level.
        self.pp_with_hammer_rail = 7
        self.intensities = [
            8,      # no port
            9,      # port1
            10,     # port2
            11.5,   # port1-2
            13,     # port3
            14.5,   # port3-1
            16,     # port3-2
            18,     # port3-2-1
            20.5,   # port4
            27,     # port4-1
            35,     # port4-2 above
        ]

        self.delay_ratio = 0.15
        self.bass_vacuum_pre = self.treble_vacuum_pre = self.intensities[0]
        self.bass_vacuum = self.treble_vacuum = self.intensities[0]

    def emulate_off(self):
        super().emulate_off()
        self.bass_vacuum_pre = self.treble_vacuum_pre = self.intensities[0]
        self.bass_vacuum = self.treble_vacuum = self.intensities[0]

    def emulate_pedals(self):
        # sustain pedal
        sustain = self.holes["sustain"]
        if sustain["to_open"]:
            self.midi.sustain_on()

        elif sustain["to_close"]:
            self.midi.sustain_off()

        # no soft pedal

    def emulate_expression(self, curtime):

        vac_lv = 0
        if self.holes["ff"]["is_open"]:
            vac_lv += 8
        if self.holes["f"]["is_open"]:
            vac_lv += 4
        if self.holes["mf"]["is_open"]:
            vac_lv += 2
        if self.holes["p"]["is_open"]:
            vac_lv += 1

        vac_lv = min(10, vac_lv)  # more than lv10 is 35 inches (full pump vacuum)

        # The hammer rail ports reduced the playing level to midway to the next lower intensity
        if self.holes["bass_hammer_rail"]["is_open"]:
            if vac_lv > 0:
                bass_target_vac = (self.intensities[vac_lv] + self.intensities[vac_lv - 1]) / 2
            else:
                bass_target_vac = self.pp_with_hammer_rail
        else:
            bass_target_vac = self.intensities[vac_lv]

        if self.holes["treble_hammer_rail"]["is_open"]:
            if vac_lv > 0:
                treble_target_vac = (self.intensities[vac_lv] + self.intensities[vac_lv - 1]) / 2
            else:
                treble_target_vac = self.pp_with_hammer_rail
        else:
            treble_target_vac = self.intensities[vac_lv]

        # delay function
        self.bass_vacuum = self.bass_vacuum_pre + (bass_target_vac - self.bass_vacuum_pre) * self.delay_ratio
        self.treble_vacuum = self.treble_vacuum_pre + (treble_target_vac - self.treble_vacuum_pre) * self.delay_ratio
        self.bass_vacuum_pre = self.bass_vacuum
        self.treble_vacuum_pre = self.treble_vacuum


if __name__ == "__main__":
    import itertools
    import os

    import numpy as np
    from midi_controller import MidiWrap

    midiobj = MidiWrap()
    obj = RecordoA(os.path.join("playsk_config", "Recordo A (rare) white back.json"), midiobj)
    obj.delay_ratio = 1

    # expression check
    ff = [False, True]
    f = [False, True]
    mf = [False, True]
    p = [False, True]
    hammer_rail = [True, False]
    res = list(itertools.product(ff, f, mf, p, hammer_rail))

    for ports in itertools.product(ff, f, mf, p, hammer_rail):
        exp_ports = ports[:-1]
        hammer_rail = ports[-1]
        frame = np.full((600, 800, 3), 0, np.uint8)

        for port, is_open in zip(("ff", "f", "mf", "p"), exp_ports):
            if is_open:
                pos = obj.holes[port]["pos"][0]
                frame[pos[1]: pos[3], pos[0]: pos[2]] = 255

        if hammer_rail:
            pos = obj.holes["bass_hammer_rail"]["pos"][0]
            frame[pos[1]: pos[3], pos[0]: pos[2]] = 255

        obj.holes.set_frame(frame, 0)
        obj.emulate_expression(0)

        print(obj.bass_vacuum, ports)
