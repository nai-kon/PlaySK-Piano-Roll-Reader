import json

from .base_player import BasePlayer


class DuoArtOrgan(BasePlayer):
    def __init__(self, confpath, midiobj):
        super().__init__(confpath, midiobj)

        with open(confpath, encoding="utf-8") as f:
            conf = json.load(f)
        self.shade = conf["expression"]["expression_shade"]
        self.pre_time = None
        self.init_controls()

    def init_controls(self):
        # Aeolian Duo-Art Organ tracker bar
        # https://www.mmdigest.com/Gallery/Tech/Scales/Aeo176.html

        # expression shade. swell shade: ch=0 ctrl=11. great shade: ch=1 ctrl=11
        self.shade_change_rate = (self.shade["shade6"] - self.shade["shade0"]) / self.shade["min_to_max_second"]
        self.swell_shade_val = self.shade["shade6"]
        self.great_shade_val = self.shade["shade6"]
        self.midi.expression(self.swell_shade_val, 0)
        self.midi.expression(self.great_shade_val, 1)

        # upper control holes of tracker bar
        self.swell_echo = False
        self.swell_chimes = False
        self.swell_tremolo = False
        self.swell_harp = False
        self.swell_trumpet = False
        self.swell_oboe = False
        self.swell_vox_humana = False
        self.swell_diapason_mf = False
        self.swell_flute16 = False
        self.swell_flute4 = False
        self.swell_fluteP = False
        self.swell_string_vibrato_f = False
        self.swell_string_f = False
        self.swell_string_mf = False
        self.swell_string_p = False
        self.swell_string_pp = False
        self.swell_shade1 = True
        self.swell_shade2 = True
        self.swell_shade3 = True
        self.swell_shade4 = True
        self.swell_shade5 = True
        self.swell_shade6 = True
        self.swell_extension = False
        self.LCW1 = False
        self.LCW2 = False
        self.swell_soft_chimes = False
        self.reroll = False
        self.swell_ventil = False
        self.normal = False
        self.pedal_to_upper = False

        # lower control holes of tracker bar
        self.great_tremolo = False
        self.great_tonal = False
        self.great_harp = False
        self.great_extension = False
        self.great_pedal_2nd_oct = False
        self.great_pedal_3rd_oct = False
        self.great_shade1 = True
        self.great_shade2 = True
        self.great_shade3 = True
        self.great_shade4 = True
        self.great_shade5 = True
        self.great_shade6 = True
        self.great_pedal_bassoon16 = False
        self.great_pedal_string16 = False
        self.great_pedal_flute_f16 = False
        self.great_pedal_flute_p16 = False
        self.great_string_pp = False
        self.great_string_p = False
        self.great_string_f = False
        self.great_flute_p = False
        self.great_flute_f = False
        self.great_flute_4 = False
        self.great_diapason_f = False
        self.great_piccolo = False
        self.great_clarinet = False
        self.great_trumpet = False
        self.chimes_dampers_off = False
        self.LCW3 = False
        self.LCW4 = False
        self.great_ventil = False

    def emulate_off(self):
        super().emulate_off()
        self.init_controls()

    def emulate_notes(self):
        offset = 15 + 21
        velocity = 60

        # swell notes
        note = self.holes["swell_note"]
        for key in note["to_open"].nonzero()[0]:
            self.midi.note_on(key + offset, velocity, channel=0)
            # if self.swell_extension:
            #     self.midi.note_on(key + offset + 12, velocity, channel=0)

        for key in note["to_close"].nonzero()[0]:
            self.midi.note_off(key + offset, channel=0)
            # if self.swell_extension:
            #     self.midi.note_off(key + offset + 12, channel=0)

        # great notes
        note = self.holes["great_note"]
        for key in note["to_open"].nonzero()[0]:
            self.midi.note_on(key + offset, velocity, channel=1)

        for key in note["to_close"].nonzero()[0]:
            self.midi.note_off(key + offset, channel=1)

        # pedal notes
        if self.great_pedal_bassoon16 or self.great_pedal_flute_f16 or \
            self.great_pedal_flute_p16 or self.great_pedal_string16:
            note = self.holes["swell_note"] if self.pedal_to_upper else self.holes["great_note"]
            for key in note["to_open"].nonzero()[0]:
                self.midi.note_on(key + offset, velocity, channel=2)

            for key in note["to_close"].nonzero()[0]:
                self.midi.note_off(key + offset, channel=2)

    def emulate_controls(self, curtime):
        if self.pre_time is None:
            self.pre_time = curtime
        delta_time = curtime - self.pre_time

        # swell controls
        controls = self.holes["swell_controls"]
        if controls["to_open"][0]:
            self.swell_echo = not self.swell_echo
            print("swell_echo", self.swell_echo)
            if self.swell_echo:
                self.midi.note_on(0, 64, channel=3)
            else:
                self.midi.note_off(0, channel=3)

        if controls["to_open"][1]:
            self.swell_chimes = not self.swell_chimes
            print("swell_chimes", self.swell_chimes)
            if self.swell_chimes:
                self.midi.note_on(1, 64, channel=3)
            else:
                self.midi.note_off(1, channel=3)

        if controls["to_open"][2]:
            self.swell_tremolo = not self.swell_tremolo
            print("swell_tremolo", self.swell_tremolo)
            if self.swell_tremolo:
                self.midi.note_on(2, 64, channel=3)
            else:
                self.midi.note_off(2, channel=3)

        if controls["to_open"][3]:
            self.swell_harp = not self.swell_harp
            print("swell_harp", self.swell_harp)
            if self.swell_harp:
                self.midi.note_on(3, 64, channel=3)
            else:
                self.midi.note_off(3, channel=3)

        if controls["to_open"][4]:
            self.swell_trumpet = not self.swell_trumpet
            print("swell_trumpet", self.swell_trumpet)
            if self.swell_trumpet:
                self.midi.note_on(4, 64, channel=3)
            else:
                self.midi.note_off(4, channel=3)

        if controls["to_open"][5]:
            self.swell_oboe = not self.swell_oboe
            print("swell_oboe", self.swell_oboe)
            if self.swell_oboe:
                self.midi.note_on(5, 64, channel=3)
            else:
                self.midi.note_off(5, channel=3)

        if controls["to_open"][6]:
            self.swell_vox_humana = not self.swell_vox_humana
            print("swell_vox_humana", self.swell_vox_humana)
            if self.swell_vox_humana:
                self.midi.note_on(6, 64, channel=3)
            else:
                self.midi.note_off(6, channel=3)

        if controls["to_open"][7]:
            self.swell_diapason_mf = not self.swell_diapason_mf
            print("swell_diapason_mf", self.swell_diapason_mf)
            if self.swell_diapason_mf:
                self.midi.note_on(7, 64, channel=3)
            else:
                self.midi.note_off(7, channel=3)

        if controls["to_open"][8]:
            self.swell_flute16 = not self.swell_flute16
            print("swell_flute16", self.swell_flute16)
            if self.swell_flute16:
                self.midi.note_on(8, 64, channel=3)
            else:
                self.midi.note_off(8, channel=3)

        if controls["to_open"][9]:
            self.swell_flute4 = not self.swell_flute4
            print("swell_flute4", self.swell_flute4)
            if self.swell_flute4:
                self.midi.note_on(9, 64, channel=3)
            else:
                self.midi.note_off(9, channel=3)

        if controls["to_open"][10]:
            self.swell_fluteP = not self.swell_fluteP
            print("swell_fluteP", self.swell_fluteP)
            if self.swell_fluteP:
                self.midi.note_on(10, 64, channel=3)
            else:
                self.midi.note_off(10, channel=3)

        if controls["to_open"][11]:
            self.swell_string_vibrato_f = not self.swell_string_vibrato_f
            print("swell_string_vibrato_f", self.swell_string_vibrato_f)
            if self.swell_string_vibrato_f:
                self.midi.note_on(11, 64, channel=3)
            else:
                self.midi.note_off(11, channel=3)

        if controls["to_open"][12]:
            self.swell_string_f = not self.swell_string_f
            print("swell_string_f", self.swell_string_f)
            if self.swell_string_f:
                self.midi.note_on(12, 64, channel=3)
            else:
                self.midi.note_off(12, channel=3)

        if controls["to_open"][13]:
            self.swell_string_mf = not self.swell_string_mf
            print("swell_string_mf", self.swell_string_mf)
            if self.swell_string_mf:
                self.midi.note_on(13, 64, channel=3)
            else:
                self.midi.note_off(13, channel=3)

        if controls["to_open"][14]:
            self.swell_string_p = not self.swell_string_p
            print("swell_string_p", self.swell_string_p)
            if self.swell_string_p:
                self.midi.note_on(14, 64, channel=3)
            else:
                self.midi.note_off(14, channel=3)

        if controls["to_open"][15]:
            self.swell_string_pp = not self.swell_string_pp
            print("swell_string_pp", self.swell_string_pp)
            if self.swell_string_pp:
                self.midi.note_on(15, 64, channel=3)
            else:
                self.midi.note_off(15, channel=3)

        if controls["to_open"][16]:
            self.swell_shade1 = not self.swell_shade1
        if controls["to_open"][17]:
            self.swell_shade2 = not self.swell_shade2
        if controls["to_open"][18]:
            self.swell_shade3 = not self.swell_shade3
        if controls["to_open"][19]:
            self.swell_shade4 = not self.swell_shade4
        if controls["to_open"][20]:
            self.swell_shade5 = not self.swell_shade5
        if controls["to_open"][21]:
            self.swell_shade6 = not self.swell_shade6

        target_val = self.shade["shade0"]
        if self.swell_shade1:
            target_val = self.shade["shade1"]
        if self.swell_shade2:
            target_val = self.shade["shade2"]
        if self.swell_shade3:
            target_val = self.shade["shade3"]
        if self.swell_shade4:
            target_val = self.shade["shade4"]
        if self.swell_shade5:
            target_val = self.shade["shade5"]
        if self.swell_shade6:
            target_val = self.shade["shade6"]

        if target_val > self.swell_shade_val:
            self.swell_shade_val += delta_time * self.shade_change_rate
            self.swell_shade_val = min(self.swell_shade_val, target_val)
            self.midi.expression(int(self.swell_shade_val), 0)
        elif target_val < self.swell_shade_val:
            self.swell_shade_val -= delta_time * self.shade_change_rate
            self.swell_shade_val = max(self.swell_shade_val, target_val)
            self.midi.expression(int(self.swell_shade_val), 0)

        self.swell_extension = controls["is_open"][22]

        if controls["to_open"][25]:
            self.swell_soft_chimes = not self.swell_soft_chimes
            print("swell_soft_chimes", self.swell_soft_chimes)
            if self.swell_soft_chimes:
                self.midi.note_on(17, 64, channel=3)
            else:
                self.midi.note_off(17, channel=3)

        if controls["to_open"][26]:
            self.reroll = not self.reroll
            print("reroll", self.reroll)

        if controls["to_open"][27]:
            self.swell_ventil = not self.swell_ventil
            print("swell_ventil", self.swell_ventil)
        if controls["to_open"][29]:
            self.pedal_to_upper = not self.pedal_to_upper
            print("pedal_to_upper", self.pedal_to_upper)

        # great controls
        controls = self.holes["great_controls"]
        if controls["to_open"][0]:
            self.great_tremolo = not self.great_tremolo
            print("great_tremolo", self.great_tremolo)
            if self.great_tremolo:
                self.midi.note_on(18, 64, channel=3)
            else:
                self.midi.note_off(18, channel=3)

        if controls["to_open"][1]:
            self.great_tonal = not self.great_tonal
            print("great_tonal", self.great_tonal)
            if self.great_tonal:
                self.midi.note_on(19, 64, channel=3)
            else:
                self.midi.note_off(19, channel=3)

        if controls["to_open"][2]:
            self.great_harp = not self.great_harp
            print("great_harp", self.great_harp)
            if self.great_harp:
                self.midi.note_on(20, 64, channel=3)
            else:
                self.midi.note_off(20, channel=3)

        self.great_extension = controls["is_open"][3]

        if controls["to_open"][4]:
            self.great_pedal_2nd_oct = not self.great_pedal_2nd_oct
            print("great_pedal_2nd_oct", self.great_pedal_2nd_oct)
            if self.great_pedal_2nd_oct:
                self.midi.note_on(22, 64, channel=3)
            else:
                self.midi.note_off(22, channel=3)

        if controls["to_open"][5]:
            self.great_pedal_3rd_oct = not self.great_pedal_3rd_oct
            print("great_pedal_3rd_oct", self.great_pedal_3rd_oct)
            if self.great_pedal_3rd_oct:
                self.midi.note_on(23, 64, channel=3)
            else:
                self.midi.note_off(23, channel=3)

        if controls["to_open"][6]:
            self.great_shade1 = not self.great_shade1
        if controls["to_open"][7]:
            self.great_shade2 = not self.great_shade2
        if controls["to_open"][8]:
            self.great_shade3 = not self.great_shade3
        if controls["to_open"][9]:
            self.great_shade4 = not self.great_shade4
        if controls["to_open"][10]:
            self.great_shade5 = not self.great_shade5
        if controls["to_open"][11]:
            self.great_shade6 = not self.great_shade6

        target_val = self.shade["shade0"]
        if self.great_shade1:
            target_val = self.shade["shade1"]
        if self.great_shade2:
            target_val = self.shade["shade2"]
        if self.great_shade3:
            target_val = self.shade["shade3"]
        if self.great_shade4:
            target_val = self.shade["shade4"]
        if self.great_shade5:
            target_val = self.shade["shade5"]
        if self.great_shade6:
            target_val = self.shade["shade6"]

        if target_val > self.great_shade_val:
            self.great_shade_val += delta_time * self.shade_change_rate
            self.great_shade_val = min(self.great_shade_val, target_val)
            self.midi.expression(int(self.great_shade_val), 1)
        elif target_val < self.great_shade_val:
            self.great_shade_val -= delta_time * self.shade_change_rate
            self.great_shade_val = max(self.great_shade_val, target_val)
            self.midi.expression(int(self.great_shade_val), 1)

        if controls["to_open"][12]:
            self.great_pedal_bassoon16 = not self.great_pedal_bassoon16
            print("great_pedal_bassoon16", self.great_pedal_bassoon16)
            if self.great_pedal_bassoon16:
                self.midi.note_on(24, 64, channel=3)
            else:
                self.midi.note_off(24, channel=3)

        if controls["to_open"][13]:
            self.great_pedal_string16 = not self.great_pedal_string16
            print("great_pedal_string16", self.great_pedal_string16)
            if self.great_pedal_string16:
                self.midi.note_on(25, 64, channel=3)
            else:
                self.midi.note_off(25, channel=3)

        if controls["to_open"][14]:
            self.great_pedal_flute_f16 = not self.great_pedal_flute_f16
            print("great_pedal_flute_f16", self.great_pedal_flute_f16)
            if self.great_pedal_flute_f16:
                self.midi.note_on(26, 64, channel=3)
            else:
                self.midi.note_off(26, channel=3)

        if controls["to_open"][15]:
            self.great_pedal_flute_p16 = not self.great_pedal_flute_p16
            print("great_pedal_flute_p16", self.great_pedal_flute_p16)
            if self.great_pedal_flute_p16:
                self.midi.note_on(27, 64, channel=3)
            else:
                self.midi.note_off(27, channel=3)

        if controls["to_open"][16]:
            self.great_string_pp = not self.great_string_pp
            print("great_string_pp", self.great_string_pp)
            if self.great_string_pp:
                self.midi.note_on(28, 64, channel=3)
            else:
                self.midi.note_off(28, channel=3)

        if controls["to_open"][17]:
            self.great_string_p = not self.great_string_p
            print("great_string_p", self.great_string_p)
            if self.great_string_p:
                self.midi.note_on(29, 64, channel=3)
            else:
                self.midi.note_off(29, channel=3)

        if controls["to_open"][18]:
            self.great_string_f = not self.great_string_f
            print("great_string_f", self.great_string_f)
            if self.great_string_f:
                self.midi.note_on(30, 64, channel=3)
            else:
                self.midi.note_off(30, channel=3)

        if controls["to_open"][19]:
            self.great_flute_p = not self.great_flute_p
            print("great_flute_p", self.great_flute_p)
            if self.great_flute_p:
                self.midi.note_on(31, 64, channel=3)
            else:
                self.midi.note_off(31, channel=3)

        if controls["to_open"][20]:
            self.great_flute_f = not self.great_flute_f
            print("great_flute_f", self.great_flute_f)
            if self.great_flute_f:
                self.midi.note_on(32, 64, channel=3)
            else:
                self.midi.note_off(32, channel=3)

        if controls["to_open"][21]:
            self.great_flute_4 = not self.great_flute_4
            print("great_flute_4", self.great_flute_4)
            if self.great_flute_4:
                self.midi.note_on(33, 64, channel=3)
            else:
                self.midi.note_off(33, channel=3)

        if controls["to_open"][22]:
            self.great_diapason_f = not self.great_diapason_f
            print("great_diapason_f", self.great_diapason_f)
            if self.great_diapason_f:
                self.midi.note_on(34, 64, channel=3)
            else:
                self.midi.note_off(34, channel=3)

        if controls["to_open"][23]:
            self.great_piccolo = not self.great_piccolo
            print("great_piccolo", self.great_piccolo)
            if self.great_piccolo:
                self.midi.note_on(35, 64, channel=3)
            else:
                self.midi.note_off(35, channel=3)

        if controls["to_open"][24]:
            self.great_clarinet = not self.great_clarinet
            print("great_clarinet", self.great_clarinet)
            if self.great_clarinet:
                self.midi.note_on(36, 64, channel=3)
            else:
                self.midi.note_off(36, channel=3)

        if controls["to_open"][25]:
            self.great_trumpet = not self.great_trumpet
            print("great_trumpet", self.great_trumpet)
            if self.great_trumpet:
                self.midi.note_on(37, 64, channel=3)
            else:
                self.midi.note_off(37, channel=3)

        if controls["to_open"][26]:
            self.chimes_dampers_off = not self.chimes_dampers_off
            print("chimes_dampers_off", self.chimes_dampers_off)
            if self.chimes_dampers_off:
                self.midi.note_on(38, 64, channel=3)
            else:
                self.midi.note_off(38, channel=3)

        if controls["to_open"][29]:
            self.great_ventil = not self.great_ventil
            print("great_ventil", self.great_ventil)

        self.pre_time = curtime

    def emulate(self, frame, curtime):
        if self.emulate_enable:
            self.during_emulate_evt.clear()

            self.auto_track(frame)
            self.holes.set_frame(frame, self.tracker_offset)
            self.emulate_controls(curtime)
            self.emulate_notes()

            self.during_emulate_evt.set()

if __name__ == "__main__":
    import os
    import time

    import numpy as np
    from midi_controller import MidiWrap
    midiobj = MidiWrap()
    player = DuoArtOrgan(os.path.join("playsk_config", "Aeolian Duo-Art Pipe Organ.json"), midiobj)
    frame = np.full((600, 800, 3), 100, np.uint8)
    start = time.perf_counter()
    for _ in range(10000):
        player.emulate(frame, time.perf_counter())
    end = time.perf_counter()
    t = end - start
    print(t, "per", (t / 10000) * 1000, "ms")
