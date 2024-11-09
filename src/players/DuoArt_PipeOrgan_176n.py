from collections import deque

from .base_player import BasePlayer


class DuoArtOrgan(BasePlayer):
    def __init__(self, confpath, midiobj):
        super().__init__(confpath, midiobj)
        self.init_controls()

    def init_controls(self):
        # Aeolian Duo-Art Organ tracker bar
        # https://www.mmdigest.com/Gallery/Tech/Scales/Aeo176.html

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
        self.swell_shade1 = False
        self.swell_shade2 = False
        self.swell_shade3 = False
        self.swell_shade4 = False
        self.swell_shade5 = False
        self.swell_shade6 = False
        self.swell_extension = False
        self.LCW1 = False
        self.LCW2 = False
        self.swell_soft_chimes = False
        self.reroll = False
        self.swell_ventil = False
        self.normal = False
        self.pedal = False

        # lower control holes of tracker bar
        self.great_tremolo = False
        self.great_tonal = False
        self.great_harp = False
        self.great_extension = False
        self.great_pedal_2nd_oct = False
        self.great_pedal_3rd_oct = False
        self.great_shade1 = False
        self.great_shade2 = False
        self.great_shade3 = False
        self.great_shade4 = False
        self.great_shade5 = False
        self.great_shade6 = False
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

        for key in note["to_close"].nonzero()[0]:
            self.midi.note_off(key + offset, channel=0)

        # great notes
        note = self.holes["great_note"]
        for key in note["to_open"].nonzero()[0]:
            self.midi.note_on(key + offset, velocity, channel=1)

        for key in note["to_close"].nonzero()[0]:
            self.midi.note_off(key + offset, channel=1)

    def emulate_controls(self):
        # swell controls
        controls = self.holes["swell_controls"]
        if controls["to_open"][0]:
            self.swell_echo = not self.swell_echo
            print("swell_echo", self.swell_echo)
        if controls["to_open"][1]:
            self.swell_chimes = not self.swell_chimes
            print("swell_chimes", self.swell_chimes)
        if controls["to_open"][2]:
            self.swell_tremolo = not self.swell_tremolo
            print("swell_tremolo", self.swell_tremolo)
        if controls["to_open"][3]:
            self.swell_harp = not self.swell_harp
            print("swell_harp", self.swell_harp)
        if controls["to_open"][4]:
            self.swell_trumpet = not self.swell_trumpet
            print("swell_trumpet", self.swell_trumpet)
        if controls["to_open"][5]:
            self.swell_oboe = not self.swell_oboe
            print("swell_oboe", self.swell_oboe)
        if controls["to_open"][6]:
            self.swell_vox_humana = not self.swell_vox_humana
            print("swell_vox_humana", self.swell_vox_humana)
        if controls["to_open"][7]:
            self.swell_diapason_mf = not self.swell_diapason_mf
            print("swell_diapason_mf", self.swell_diapason_mf)
        if controls["to_open"][8]:
            self.swell_flute16 = not self.swell_flute16
            print("swell_flute16", self.swell_flute16)
        if controls["to_open"][9]:
            self.swell_flute4 = not self.swell_flute4
            print("swell_flute4", self.swell_flute4)
        if controls["to_open"][10]:
            self.swell_fluteP = not self.swell_fluteP
            print("swell_fluteP", self.swell_fluteP)
        if controls["to_open"][11]:
            self.swell_string_vibrato_f = not self.swell_string_vibrato_f
            print("swell_string_vibrato_f", self.swell_string_vibrato_f)
        if controls["to_open"][12]:
            self.swell_string_f = not self.swell_string_f
            print("swell_string_f", self.swell_string_f)
        if controls["to_open"][13]:
            self.swell_string_mf = not self.swell_string_mf
            print("swell_string_mf", self.swell_string_mf)
        if controls["to_open"][14]:
            self.swell_string_p = not self.swell_string_p
            print("swell_string_p", self.swell_string_p)
        if controls["to_open"][15]:
            self.swell_string_pp = not self.swell_string_pp
            print("swell_string_pp", self.swell_string_pp)
        if controls["to_open"][16]:
            print("swell_shade1")
        if controls["to_open"][17]:
            print("swell_shade2")
        if controls["to_open"][18]:
            print("swell_shade3")
        if controls["to_open"][19]:
            print("swell_shade4")
        if controls["to_open"][20]:
            print("swell_shade5")
        if controls["to_open"][21]:
            print("swell_shade6")
        if controls["to_open"][22]:
            self.swell_extension = not self.swell_extension
            print("swell_extension", self.swell_extension)
        if controls["to_open"][25]:
            self.swell_soft_chimes = not self.swell_soft_chimes
            print("swell_soft_chimes", self.swell_soft_chimes)
        if controls["to_open"][26]:
            self.reroll = not self.reroll
            print("reroll", self.reroll)
        if controls["to_open"][27]:
            self.swell_ventil = not self.swell_ventil
            print("swell_ventil", self.swell_ventil)
        if controls["to_open"][29]:
            self.pedal = not self.pedal
            print("pedal", self.pedal)

        # great controls
        controls = self.holes["great_controls"]
        if controls["to_open"][0]:
            self.great_tremolo = not self.great_tremolo
            print("great_tremolo", self.great_tremolo)
        if controls["to_open"][1]:
            self.great_tonal = not self.great_tonal
            print("great_tonal", self.great_tonal)
        if controls["to_open"][2]:
            self.great_harp = not self.great_harp
            print("great_harp", self.great_harp)
        if controls["to_open"][3]:
            self.great_extension = not self.great_extension
            print("great_extension", self.great_extension)
        if controls["to_open"][4]:
            self.great_pedal_2nd_oct = not self.great_pedal_2nd_oct
            print("great_pedal_2nd_oct", self.great_pedal_2nd_oct)
        if controls["to_open"][5]:
            self.great_pedal_3rd_oct = not self.great_pedal_3rd_oct
            print("great_pedal_3rd_oct", self.great_pedal_3rd_oct)
        if controls["to_open"][6]:
            print("great_shade1")
        if controls["to_open"][7]:
            print("great_shade2")
        if controls["to_open"][8]:
            print("great_shade3")
        if controls["to_open"][9]:
            print("great_shade4")
        if controls["to_open"][10]:
            print("great_shade5")
        if controls["to_open"][11]:
            print("great_shade6")
        if controls["to_open"][12]:
            self.great_pedal_bassoon16 = not self.great_pedal_bassoon16
            print("great_pedal_bassoon16", self.great_pedal_bassoon16)
        if controls["to_open"][13]:
            self.great_pedal_string16 = not self.great_pedal_string16
            print("great_pedal_string16", self.great_pedal_string16)
        if controls["to_open"][14]:
            self.great_pedal_flute_f16 = not self.great_pedal_flute_f16
            print("great_pedal_flute_f16", self.great_pedal_flute_f16)
        if controls["to_open"][15]:
            self.great_pedal_flute_p16 = not self.great_pedal_flute_p16
            print("great_pedal_flute_p16", self.great_pedal_flute_p16)
        if controls["to_open"][16]:
            self.great_string_pp = not self.great_string_pp
            print("great_string_pp", self.great_string_pp)
        if controls["to_open"][17]:
            self.great_string_p = not self.great_string_p
            print("great_string_p", self.great_string_p)
        if controls["to_open"][18]:
            self.great_string_f = not self.great_string_f
            print("great_string_f", self.great_string_f)
        if controls["to_open"][19]:
            self.great_flute_p = not self.great_flute_p
            print("great_flute_p", self.great_flute_p)
        if controls["to_open"][20]:
            self.great_flute_f = not self.great_flute_f
            print("great_flute_f", self.great_flute_f)
        if controls["to_open"][21]:
            self.great_flute_4 = not self.great_flute_4
            print("great_flute_4", self.great_flute_4)
        if controls["to_open"][22]:
            self.great_diapason_f = not self.great_diapason_f
            print("great_diapason_f", self.great_diapason_f)
        if controls["to_open"][23]:
            self.great_piccolo = not self.great_piccolo
            print("great_piccolo", self.great_piccolo)
        if controls["to_open"][24]:
            self.great_clarinet = not self.great_clarinet
            print("great_clarinet", self.great_clarinet)
        if controls["to_open"][25]:
            self.great_trumpet = not self.great_trumpet
            print("great_trumpet", self.great_trumpet)
        if controls["to_open"][26]:
            self.chimes_dampers_off = not self.chimes_dampers_off
            print("chimes_dampers_off", self.chimes_dampers_off)
        if controls["to_open"][29]:
            self.great_ventil = not self.great_ventil
            print("great_ventil", self.great_ventil)

    def emulate(self, frame, curtime):
        if self.emulate_enable:
            self.during_emulate_evt.clear()

            self.auto_track(frame)
            self.holes.set_frame(frame, self.tracker_offset)
            self.emulate_controls()
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
