import json

from .base_player import BasePlayer


class Aeolian176note(BasePlayer):
    def __init__(self, confpath, midiobj):
        super().__init__(confpath, midiobj)

        with open(confpath, encoding="utf-8") as f:
            conf = json.load(f)
        self.shade = conf["expression"]["expression_shade"]
        self.pre_time = None
        self.prevent_chattering_wait = 0.3  # toggle switch reaction threshold seconds to prevent chattering
        self.init_controls()

    def init_controls(self):
        # Aeolian Duo-Art Organ tracker bar
        # https://www.mmdigest.com/Gallery/Tech/Scales/Aeo176.html

        # expression shade. swell shade: ch=0 ctrl=11. great shade: ch=1 ctrl=11
        self.shade_change_rate = (self.shade["shade6"] - self.shade["shade0"]) / self.shade["min_to_max_second"]
        self.swell_shade_val = self.shade["shade6"]
        self.great_shade_val = self.shade["shade6"]
        self.shade_error_detector = {"swell": [], "great": []}

        self.midi.expression(self.swell_shade_val, 0)
        self.midi.expression(self.great_shade_val, 1)

        self.ctrls = {
            # upper control holes of tracker bar
            "swell_echo" : {"part": "swell", "hole_no": 0, "is_on": False, "last_time": 0, "note_no": 0},
            "swell_chimes" : {"part": "swell", "hole_no":  1, "is_on": False, "last_time": 0, "note_no": 1},
            "swell_tremolo" : {"part": "swell", "hole_no": 2, "is_on": False, "last_time": 0, "note_no": 2},
            "swell_harp" : {"part": "swell", "hole_no": 3, "is_on": False, "last_time": 0, "note_no": 3},
            "swell_trumpet" : {"part": "swell", "hole_no": 4, "is_on": False, "last_time": 0, "note_no": 4},
            "swell_oboe" : {"part": "swell", "hole_no": 5, "is_on": False, "last_time": 0, "note_no": 5},
            "swell_vox_humana" : {"part": "swell", "hole_no": 6, "is_on": False, "last_time": 0, "note_no": 6},
            "swell_diapason_mf" : {"part": "swell", "hole_no": 7, "is_on": False, "last_time": 0, "note_no": 7},
            "swell_flute16" : {"part": "swell", "hole_no": 8, "is_on": False, "last_time": 0, "note_no": 8},
            "swell_flute4" : {"part": "swell", "hole_no": 9, "is_on": False, "last_time": 0, "note_no": 9},
            "swell_fluteP" : {"part": "swell", "hole_no": 10, "is_on": False, "last_time": 0, "note_no": 9},
            "swell_string_vibrato_f" : {"part": "swell", "hole_no": 11, "is_on": False, "last_time": 0, "note_no": 11},
            "swell_string_f" : {"part": "swell", "hole_no": 12, "is_on": False, "last_time": 0, "note_no": 11},
            "swell_string_mf" : {"part": "swell", "hole_no": 13, "is_on": False, "last_time": 0, "note_no": 11},
            "swell_string_p" : {"part": "swell", "hole_no": 14, "is_on": False, "last_time": 0, "note_no": 12},
            "swell_string_pp" : {"part": "swell", "hole_no": 15, "is_on": False, "last_time": 0, "note_no": 12},
            "swell_shade1" : {"part": "swell", "hole_no": 16, "is_on": True},
            "swell_shade2" : {"part": "swell", "hole_no": 17, "is_on": True},
            "swell_shade3" : {"part": "swell", "hole_no": 18, "is_on": True},
            "swell_shade4" : {"part": "swell", "hole_no": 19, "is_on": True},
            "swell_shade5" : {"part": "swell", "hole_no": 20, "is_on": True},
            "swell_shade6" : {"part": "swell", "hole_no": 21, "is_on": True},
            # "swell_extension" : {"part": "swell", "hole_no": 22, "is_on": False},
            # "LCW1" : {"part": "swell", "hole_no": 23, "is_on": False, "last_time": 0, "note_no": },
            # "LCW2" : {"part": "swell", "hole_no": 24, "is_on": False, "last_time": 0, "note_no": },
            "swell_soft_chimes" : {"part": "swell", "hole_no": 25, "is_on": False, "last_time": 0, "note_no": 17},
            # "reroll" : {"part": "swell", "hole_no": , "is_on": False, "last_time": 0, "note_no": },
            # "swell_ventil" : {"part": "swell", "hole_no": , "is_on": False, "last_time": 0, "note_no": },
            # "normal" : {"part": "swell", "hole_no": , "is_on": False, "last_time": 0, "note_no": },
            "pedal_to_upper" : {"part": "swell", "hole_no": 29, "is_on": False},

            # lower control holes of tracker bar
            "great_tremolo" : {"part": "great", "hole_no": 0, "is_on": False, "last_time": 0, "note_no": 18},
            "great_tonal" : {"part": "great", "hole_no": 1, "is_on": False, "last_time": 0, "note_no": 19},
            "great_harp" : {"part": "great", "hole_no": 2, "is_on": False, "last_time": 0, "note_no": 20},
            # "great_extension" : {"part": "great", "hole_no": 3, "is_on": False},
            # "great_pedal_2nd_oct" : {"part": "great", "hole_no": 4, "is_on": False},
            # "great_pedal_3rd_oct" : {"part": "great", "hole_no": 5, "is_on": False},
            "great_shade1" : {"part": "great", "hole_no": 6, "is_on": True},
            "great_shade2" : {"part": "great", "hole_no": 7, "is_on": True},
            "great_shade3" : {"part": "great", "hole_no": 8, "is_on": True},
            "great_shade4" : {"part": "great", "hole_no": 9, "is_on": True},
            "great_shade5" : {"part": "great", "hole_no": 10, "is_on": True},
            "great_shade6" : {"part": "great", "hole_no": 11, "is_on": True},
            "great_pedal_bassoon16" : {"part": "great", "hole_no": 12, "is_on": False, "last_time": 0, "note_no": 24},
            "great_pedal_string16" : {"part": "great", "hole_no": 13, "is_on": False, "last_time": 0, "note_no": 25},
            "great_pedal_flute_f16" : {"part": "great", "hole_no": 14, "is_on": False, "last_time": 0, "note_no": 26},
            "great_pedal_flute_p16" : {"part": "great", "hole_no": 15, "is_on": False, "last_time": 0, "note_no": 26},
            "great_string_pp" : {"part": "great", "hole_no": 16, "is_on": False, "last_time": 0, "note_no": 28},
            "great_string_p" : {"part": "great", "hole_no": 17, "is_on": False, "last_time": 0, "note_no": 29},
            "great_string_f" : {"part": "great", "hole_no": 18, "is_on": False, "last_time": 0, "note_no": 30},
            "great_flute_p" : {"part": "great", "hole_no": 19, "is_on": False, "last_time": 0, "note_no": 33},
            "great_flute_f" : {"part": "great", "hole_no": 20, "is_on": False, "last_time": 0, "note_no": 33},
            "great_flute_4" : {"part": "great", "hole_no": 21, "is_on": False, "last_time": 0, "note_no": 33},
            "great_diapason_f" : {"part": "great", "hole_no": 22, "is_on": False, "last_time": 0, "note_no": 34},
            "great_piccolo" : {"part": "great", "hole_no": 23, "is_on": False, "last_time": 0, "note_no": 35},
            "great_clarinet" : {"part": "great", "hole_no": 24, "is_on": False, "last_time": 0, "note_no": 36},
            "great_trumpet" : {"part": "great", "hole_no": 25, "is_on": False, "last_time": 0, "note_no": 37},
            "chimes_dampers_off" : {"part": "great", "hole_no": 26, "is_on": False, "last_time": 0, "note_no": 38},
            # "LCW3" : {"part": "great", "hole_no": , "is_on": False, "last_time": 0, "note_no": },
            # "LCW4" : {"part": "great", "hole_no": , "is_on": False, "last_time": 0, "note_no": },
            # "great_ventil" : {"part": "great", "hole_no": , "is_on": False, "last_time": 0, "note_no": }
        }

        self.pedal_all_off = True

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
            if key in [46, 47, 48] and self.holes["swell_controls"]["is_open"][22]:
                # swell extension of 59, 60, 61 note
                self.midi.note_on(key + offset + 12, velocity, channel=0)

        for key in note["to_close"].nonzero()[0]:
            self.midi.note_off(key + offset, channel=0)
            if key in [46, 47, 48] and self.holes["swell_controls"]["is_open"][22]:
                # swell extension of 59, 60, 61 note
                self.midi.note_off(key + offset + 12, channel=0)

        # cancel swell extension notes when extension perforation is end
        if self.holes["swell_controls"]["to_close"][22]:
            [self.midi.note_off(k + offset, channel=0) for k in range(58, 61)]

        # great notes
        note = self.holes["great_note"]
        for key in note["to_open"].nonzero()[0]:
            self.midi.note_on(key + offset, velocity, channel=1)
            if key in [46, 47, 48] and self.holes["great_controls"]["is_open"][3]:
                # great extension of 59, 60, 61 note
                self.midi.note_on(key + offset + 12, velocity, channel=1)

        for key in note["to_close"].nonzero()[0]:
            self.midi.note_off(key + offset, channel=1)
            if key in [46, 47, 48] and self.holes["great_controls"]["is_open"][3]:
                # great extension of 59, 60, 61 note
                self.midi.note_off(key + offset + 12, channel=1)

        # cancel great extension notes when extension perforation is end
        if self.holes["great_controls"]["to_close"][3]:
            [self.midi.note_off(k + offset, channel=1) for k in range(58, 61)]

        # pedal notes
        if self.ctrls["great_pedal_bassoon16"]["is_on"] or \
            self.ctrls["great_pedal_flute_f16"]["is_on"] or \
            self.ctrls["great_pedal_flute_p16"]["is_on"] or \
            self.ctrls["great_pedal_string16"]["is_on"]:

            self.pedal_all_off = False
            note = self.holes["great_note"]
            if self.ctrls["pedal_to_upper"]["is_on"]:
                note = self.holes["swell_note"]
            for key in note["to_open"].nonzero()[0]:
                if key >= 13:
                    # pedal only takes lower 13 notes of great or swell
                    continue

                self.midi.note_on(key + offset, velocity, channel=2)

                if self.holes["great_controls"]["is_open"][4]:
                    # add one octave upper note
                    self.midi.note_on(key + offset + 12, velocity, channel=2)

                if self.holes["great_controls"]["is_open"][5] and key + 24 < 30:
                    # add two octave upper note, but limit to 30th notes
                    pedal_note = key + offset + 24
                    self.midi.note_on(pedal_note, velocity, channel=2)

            for key in note["to_close"].nonzero()[0]:
                if key >= 13:
                    # pedal only takes lower 13 notes of great or swell
                    continue

                self.midi.note_off(key + offset, channel=2)

                if self.holes["great_controls"]["is_open"][4]:
                    # add one octave upper note
                    self.midi.note_off(key + offset + 12, channel=2)

                if self.holes["great_controls"]["is_open"][5] and key + 24 < 30:
                    # add two octave upper note, but limit to 30th notes
                    pedal_note = key + offset + 24
                    self.midi.note_off(pedal_note, channel=2)

            # cancel all pedal extension notes when extension perforation is end
            if not self.holes["great_controls"]["to_close"][4]:
                [self.midi.note_off(k + offset, channel=2) for k in range(13, 24)]

            if not self.holes["great_controls"]["to_close"][5]:
                [self.midi.note_off(k + offset, channel=2) for k in range(24, 30)]

        elif not self.pedal_all_off:
            [self.midi.note_off(k, channel=2) for k in range(128)]
            self.pedal_all_off = True

    def emulate_controls(self, curtime):
        if self.pre_time is None:
            self.pre_time = curtime
        delta_time = curtime - self.pre_time

        # check toggle switch holes
        for key, val in self.ctrls.items():
            controls = self.holes[f"{val['part']}_controls"]
            hole_no = val["hole_no"]
            if not controls["to_open"][hole_no]:
                continue

            if "last_time" in val:
                if curtime - val["last_time"] < self.prevent_chattering_wait:
                    # skip to prevent toggle switch chattering
                    print("prevent chattering")
                    continue
                else:
                    val["last_time"] = curtime

            # toggle switch function
            val["is_on"] = not val["is_on"]
            # print(key, val["is_on"])

            note_no = val.get("note_no")
            if note_no is not None:
                if val["is_on"]:
                    self.midi.note_on(note_no, 64, channel=3)
                else:
                    # When treating multiple stops with the same note number, note-off after all stops is off
                    if key in ("swell_string_vibrato_f", "swell_string_f", "swell_string_mf") and \
                        (self.ctrls["swell_string_vibrato_f"]["is_on"] or \
                        self.ctrls["swell_string_f"]["is_on"] or \
                        self.ctrls["swell_string_mf"]["is_on"]):
                            continue

                    if key in ("swell_string_p", "swell_string_pp") and \
                        (self.ctrls["swell_string_p"]["is_on"] or \
                        self.ctrls["swell_string_pp"]["is_on"]):
                            continue

                    if key in ("swell_flute4" , "swell_flutep") and \
                        (self.ctrls["swell_flute4"]["is_on"] or \
                        self.ctrls["swell_fluteP"]["is_on"]):
                            continue

                    if "great_flute" in key and \
                        (self.ctrls["great_flute_p"]["is_on"] or \
                        self.ctrls["great_flute_f"]["is_on"] or \
                        self.ctrls["great_flute_4"]["is_on"]):
                            continue

                    if "great_pedal_flute" in key and \
                        (self.ctrls["great_pedal_flute_f16"]["is_on"] or \
                        self.ctrls["great_pedal_flute_p16"]["is_on"]):
                            continue

                    self.midi.note_off(note_no, channel=3)

            if key == "pedal_to_upper":
                # reset all pedal note
                [self.midi.note_off(k, channel=2) for k in range(128)]

        # fix shade error
        self.fix_shade_error()

        # swell expression shade position
        target_val = self.shade["shade0"]
        for no in range(1, 6 + 1):
            if self.ctrls[f"swell_shade{no}"]["is_on"]:
                target_val = self.shade[f"shade{no}"]

        if target_val > self.swell_shade_val:
            self.swell_shade_val += delta_time * self.shade_change_rate
            self.swell_shade_val = min(self.swell_shade_val, target_val)
            self.midi.expression(int(self.swell_shade_val), 0)
        elif target_val < self.swell_shade_val:
            self.swell_shade_val -= delta_time * self.shade_change_rate
            self.swell_shade_val = max(self.swell_shade_val, target_val)
            self.midi.expression(int(self.swell_shade_val), 0)

        # great expression shade position
        target_val = self.shade["shade0"]
        for no in range(1, 6 + 1):
            if self.ctrls[f"great_shade{no}"]["is_on"]:
                target_val = self.shade[f"shade{no}"]

        if target_val > self.great_shade_val:
            self.great_shade_val += delta_time * self.shade_change_rate
            self.great_shade_val = min(self.great_shade_val, target_val)
            self.midi.expression(int(self.great_shade_val), 1)
        elif target_val < self.great_shade_val:
            self.great_shade_val -= delta_time * self.shade_change_rate
            self.great_shade_val = max(self.great_shade_val, target_val)
            self.midi.expression(int(self.great_shade_val), 1)

        self.pre_time = curtime

    def fix_shade_error(self):
        # Sometimes, shade errors occurs due to inconsistent on/off for each shade by the perforation error etc...
        # So if the shade perforations are in order 3→2→1, force reset all shade off
        for part in ("swell", "great"):
            for no in range(1, 3 + 1):
                hole_no = self.ctrls[f"{part}_shade{no}"]["hole_no"]
                if self.holes[f"{part}_controls"]["to_close"][hole_no]:
                    if no == 3:
                        self.shade_error_detector[part] = []  # reset list
                    self.shade_error_detector[part].append(no)

                    # There were perforations in order 3, 2, 1 → shade is fully closed
                    if self.shade_error_detector[part] == [3, 2, 1]:
                        self.shade_error_detector[part] = []
                        # set all shade to off to fix error
                        for no in range(1, 6 + 1):
                            self.ctrls[f"{part}_shade{no}"]["is_on"] = False

                    if len(self.shade_error_detector[part]) > 3:
                        # if list length is too much, reset
                        self.shade_error_detector[part] = []

    def emulate(self, frame, curtime):
        if self.emulate_enable:
            self.during_emulate_evt.clear()

            self.auto_track(frame)
            self.holes.set_frame(frame, self.tracker_offset)
            self.emulate_controls(curtime)
            self.emulate_notes()

            self.during_emulate_evt.set()

if __name__ == "__main__":#
    import os
    import time

    import numpy as np
    from midi_controller import MidiWrap
    midiobj = MidiWrap()
    player = Aeolian176note(os.path.join("playsk_config", "Aeolian Duo-Art Pipe Organ.json"), midiobj)
    frame = np.full((600, 800, 3), 100, np.uint8)
    start = time.perf_counter()
    for _ in range(10000):
        player.emulate(frame, time.perf_counter())
    end = time.perf_counter()
    t = end - start
    print(t, "per", (t / 10000) * 1000, "ms")
