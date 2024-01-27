from player import Player


class RecordoA(Player):
    def __init__(self, confpath, midiobj):
        super().__init__(confpath, midiobj)

        # from Robert Billings's notebook  (US Music Co.)
        # "-hr" with hammer rail
        self.intensities = {
            "p1-hr": 8, 
            "": 11,
            "p-hr": 10.125,
            "p": 11.25,
            "mf-hr": 13.375,
            "mf": 15.5,
            "f-hr": 17.5,
            "f": 19.5,
            "ff-hr": 27.25,
            "ff": 35,
        }

        self.delay_ratio = 0.15
        self.bass_vacuum_pre = self.intensities["pp"]
        self.treble_vacuum_pre = self.intensities["pp"]
        self.bass_vacuum = self.treble_vacuum = self.intensities["pp"]

    def emulate_off(self):
        super().emulate_off()
        self.bass_vacuum_pre = self.intensities["pp"]
        self.treble_vacuum_pre = self.intensities["pp"]
        self.bass_vacuum = self.treble_vacuum = self.intensities["pp"]
    
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
            vac_lv = "ff"
        elif self.holes["f"]["is_open"]:
            vac_lv = "f"
        elif self.holes["mf"]["is_open"]:
            vac_lv = "mf"
        elif self.holes["p"]["is_open"]:
            vac_lv = "p"
        else:
            vac_lv = "pp"

        bass_vac_lv = treble_vac_lv = vac_lv
        if self.holes["bass_hammer_rail"]["is_open"]:
            bass_vac_lv += "-hr"
        if self.holes["treble_hammer_rail"]["is_open"]:
            treble_vac_lv += "-hr"
    
        # delay function
        self.bass_vacuum = self.bass_vacuum_pre + (self.intensities[bass_vac_lv] - self.bass_vacuum_pre) * self.delay_ratio
        self.treble_vacuum = self.treble_vacuum_pre + (self.intensities[treble_vac_lv] - self.treble_vacuum_pre) * self.delay_ratio
        self.bass_vacuum_pre = self.bass_vacuum
        self.treble_vacuum_pre = self.treble_vacuum
