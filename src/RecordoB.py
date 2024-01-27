from RecordoA import RecordoA


class RecordoB(RecordoA):
    def __init__(self, confpath, midiobj):
        super().__init__(confpath, midiobj)

        # from Robert Billings's notebook  (US Music Co.)
        self.pp_with_hammer_rail = 8
        self.intensities = [
            9,      # pp
            11.25,  # p
            15.5,   # mf
            19.5,   # f
            35,     # ff
        ]


    def emulate_expression(self, curtime):
        vac_lv = 0
        if self.holes["ff"]["is_open"]:
            vac_lv = 4
        elif self.holes["f"]["is_open"]:
            vac_lv = 3
        elif self.holes["mf"]["is_open"]:
            vac_lv = 2
        elif self.holes["p"]["is_open"]:
            vac_lv = 1

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
