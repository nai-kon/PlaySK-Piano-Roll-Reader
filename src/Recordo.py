import numpy as np
from player import Player


class Recordo(Player):
    def __init__(self, confpath, midiobj):
        super().__init__(confpath, midiobj)

        # from original notebook from Robert Billings of US Music Co
        self.intensities = {
            "pp": 9,
            "p": 11.25,
            "mf": 15.5,
            "f": 19.5,
            "ff": 35,
        }

        self.delay_ratio = 0.15
        self.vacuum_pre = self.intensities["pp"]
        self.bass_vacuum = self.treble_vacuum = self.intensities["pp"]

    def emulate_off(self):
        super().emulate_off()
        self.vacuum_pre = self.intensities["pp"]
        self.bass_vacuum = self.treble_vacuum = self.intensities["pp"]

    def calc_velocity(self):
        idx = np.digitize([self.bass_vacuum, self.treble_vacuum], bins=self.velocity_bins)
        bass_velo, treble_velo = self.velocity[0] + idx

        # emulate bass/treble hammer rail
        if self.holes["bass_hammer_rail"]["is_open"]:
            bass_velo = int(bass_velo * 0.8)
        if self.holes["treble_hammer_rail"]["is_open"]:
            treble_velo = int(treble_velo * 0.8)
        
        return bass_velo, treble_velo
    
    def emulate_pedals(self):
        # sustain pedal
        sustain = self.holes["sustain"]
        if sustain["to_open"]:
            self.midi.sustain_on()

        elif sustain["to_close"]:
            self.midi.sustain_off()

        # no soft pedal

    def emulate_expression(self, curtime):
        if self.holes["ff"]["is_open"]:
            target_vac = self.intensities["ff"]
        elif self.holes["f"]["is_open"]:
            target_vac = self.intensities["f"]
        elif self.holes["mf"]["is_open"]:
            target_vac = self.intensities["mf"]
        elif self.holes["p"]["is_open"]:
            target_vac = self.intensities["p"]
        else:
            target_vac = self.intensities["pp"]

        # delay function
        vacuum = self.vacuum_pre + (target_vac - self.vacuum_pre) * self.delay_ratio
        self.vacuum_pre = vacuum
        self.bass_vacuum = self.treble_vacuum = vacuum
