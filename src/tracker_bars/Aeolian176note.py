import json

from .base_player import BasePlayer


class Aeolian176note(BasePlayer):
    def __init__(self, confpath, midiobj):
        super().__init__(confpath, midiobj)

        with open(confpath, encoding="utf-8") as f:
            conf = json.load(f)
        self.shade = conf["expression"]["expression_shade"]
        self.pre_time = None
        self.prevent_chattering_wait = 0.2  # toggle switch reaction threshold seconds to prevent chattering
        self.stop_indicator = None
        self.init_controls()

    def init_stop_indicator(self, stop_indicator) -> None:
        self.stop_indicator = stop_indicator

        stops = {
            "Swell Stops": {k: v["is_on"] for k, v in self.ctrls["swell"].items() if "Pedal" not in k and "Shade" not in k},
            "Great Stops": {k: v["is_on"] for k, v in self.ctrls["great"].items() if "Pedal" not in k and "Shade" not in k},
            "Pedal Stops": {k.lstrip("Pedal "): v["is_on"] for part in self.ctrls for k, v in self.ctrls[part].items() if "Pedal" in k},
        }
        self.stop_indicator.init_stop(stops)

    def init_controls(self):
        # Aeolian Duo-Art Organ tracker bar
        # https://www.mmdigest.com/Gallery/Tech/Scales/Aeo176.html

        # expression shade. MIDI assignment is swell shade: ch=3 cc=14. great shade: ch=3 cc=15
        self.shade_change_rate = (self.shade["shade6"] - self.shade["shade0"]) / self.shade["min_to_max_second"]
        self.swell_shade_val = self.shade["shade6"]
        self.great_shade_val = self.shade["shade6"]
        self.shade_error_detector = {"swell": [], "great": []}

        self.midi.control_change(14, self.swell_shade_val, 3)
        self.midi.control_change(15, self.great_shade_val, 3)

        # toggle switch controls. MIDI assignment is switch ON: ch=3, CC=20, value:{midi_val}, switch OFF: ch=3, CC=110, value={midi_val}
        self.ctrls = {
            # upper control holes of tracker bar
            "swell":{
                "Echo" : {"hole_no": 0, "is_on": False, "last_time": 0, "midi_val": 0},
                "Chime" : {"hole_no":  1, "is_on": False, "last_time": 0, "midi_val": 1},
                "Tremolo" : {"hole_no": 2, "is_on": False, "last_time": 0, "midi_val": 2},
                "Harp" : {"hole_no": 3, "is_on": False, "last_time": 0, "midi_val": 3},
                "Trumpet" : {"hole_no": 4, "is_on": False, "last_time": 0, "midi_val": 4},
                "Oboe" : {"hole_no": 5, "is_on": False, "last_time": 0, "midi_val": 5},
                "Vox Humana" : {"hole_no": 6, "is_on": False, "last_time": 0, "midi_val": 6},
                "Diapason mf" : {"hole_no": 7, "is_on": False, "last_time": 0, "midi_val": 7},
                "Flute 16" : {"hole_no": 8, "is_on": False, "last_time": 0, "midi_val": 8},
                "Flute 4" : {"hole_no": 9, "is_on": False, "last_time": 0, "midi_val": 9},
                "Flute p" : {"hole_no": 10, "is_on": False, "last_time": 0, "midi_val": 9},
                "String Vibrato f" : {"hole_no": 11, "is_on": False, "last_time": 0, "midi_val": 11},
                "String f" : {"hole_no": 12, "is_on": False, "last_time": 0, "midi_val": 11},
                "String mf" : {"hole_no": 13, "is_on": False, "last_time": 0, "midi_val": 11},
                "String p" : {"hole_no": 14, "is_on": False, "last_time": 0, "midi_val": 12},
                "String pp" : {"hole_no": 15, "is_on": False, "last_time": 0, "midi_val": 12},
                "Shade1" : {"hole_no": 16, "is_on": True},
                "Shade2" : {"hole_no": 17, "is_on": True},
                "Shade3" : {"hole_no": 18, "is_on": True},
                "Shade4" : {"hole_no": 19, "is_on": True},
                "Shade5" : {"hole_no": 20, "is_on": True},
                "Shade6" : {"hole_no": 21, "is_on": True},
                # "extension" : {"hole_no": 22, "is_on": False},
                # "LCW1" : {"hole_no": 23, "is_on": False, "last_time": 0, "midi_val": },
                # "LCW2" : {"hole_no": 24, "is_on": False, "last_time": 0, "midi_val": },
                "Soft Chime" : {"hole_no": 25, "is_on": False, "last_time": 0, "midi_val": 17},
                # "reroll" : {"hole_no": , "is_on": False, "last_time": 0, "midi_val": },
                # "ventil" : {"hole_no": , "is_on": False, "last_time": 0, "midi_val": },
                # "normal" : {"hole_no": , "is_on": False, "last_time": 0, "midi_val": },
                "Pedal to Swell" : {"hole_no": 29, "is_on": False},
            },
            "great":{
                # lower control holes of tracker bar
                "Tremolo" : {"hole_no": 0, "is_on": False, "last_time": 0, "midi_val": 18},
                "Tonal" : {"hole_no": 1, "is_on": False, "last_time": 0, "midi_val": 19},
                "Harp" : {"hole_no": 2, "is_on": False, "last_time": 0, "midi_val": 20},
                # "extension" : {"hole_no": 3, "is_on": False},
                # "pedal_2nd_oct" : {"hole_no": 4, "is_on": False},
                # "pedal_3rd_oct" : {"hole_no": 5, "is_on": False},
                "Shade1" : {"hole_no": 6, "is_on": True},
                "Shade2" : {"hole_no": 7, "is_on": True},
                "Shade3" : {"hole_no": 8, "is_on": True},
                "Shade4" : {"hole_no": 9, "is_on": True},
                "Shade5" : {"hole_no": 10, "is_on": True},
                "Shade6" : {"hole_no": 11, "is_on": True},
                "Pedal Bassoon 16" : {"hole_no": 12, "is_on": False, "last_time": 0, "midi_val": 24},
                "Pedal String 16" : {"hole_no": 13, "is_on": False, "last_time": 0, "midi_val": 25},
                "Pedal Flute f16" : {"hole_no": 14, "is_on": False, "last_time": 0, "midi_val": 26},
                "Pedal Flute p16" : {"hole_no": 15, "is_on": False, "last_time": 0, "midi_val": 26},
                "String pp" : {"hole_no": 16, "is_on": False, "last_time": 0, "midi_val": 28},
                "String p" : {"hole_no": 17, "is_on": False, "last_time": 0, "midi_val": 29},
                "String f" : {"hole_no": 18, "is_on": False, "last_time": 0, "midi_val": 30},
                "Flute p" : {"hole_no": 19, "is_on": False, "last_time": 0, "midi_val": 31},
                "Flute f" : {"hole_no": 20, "is_on": False, "last_time": 0, "midi_val": 31},
                "Flute 4" : {"hole_no": 21, "is_on": False, "last_time": 0, "midi_val": 33},
                "Diapason f" : {"hole_no": 22, "is_on": False, "last_time": 0, "midi_val": 34},
                "Piccolo" : {"hole_no": 23, "is_on": False, "last_time": 0, "midi_val": 35},
                "Clarinet" : {"hole_no": 24, "is_on": False, "last_time": 0, "midi_val": 36},
                "Trumpet" : {"hole_no": 25, "is_on": False, "last_time": 0, "midi_val": 37},
                "Chime Damper" : {"hole_no": 26, "is_on": False, "last_time": 0, "midi_val": 38},
                # "LCW3" : {"hole_no": , "is_on": False, "last_time": 0, "midi_val": },
                # "LCW4" : {"hole_no": , "is_on": False, "last_time": 0, "midi_val": },
                # "ventil" : {"hole_no": , "is_on": False, "last_time": 0, "midi_val": }
            },
        }

        [self.midi.control_change(110, v, 3) for v in range(128)]
        self.pedal_all_off = True

        if self.stop_indicator is not None:
            stops = {
                "Swell Stops": {k: v["is_on"] for k, v in self.ctrls["swell"].items() if "Pedal" not in k and "Shade" not in k},
                "Great Stops": {k: v["is_on"] for k, v in self.ctrls["great"].items() if "Pedal" not in k and "Shade" not in k},
                "Pedal Stops": {k.lstrip("Pedal "): v["is_on"] for part in self.ctrls for k, v in self.ctrls[part].items() if "Pedal" in k},
            }
            self.stop_indicator.change_stop(stops)

    def emulate_off(self):
        super().emulate_off()
        self.init_controls()

    def emulate_notes(self):
        offset = 15 + 21
        velocity = 64

        # notes
        for part, extension_port, midi_ch in zip(("swell", "great"), (22, 3), (0, 1)):
            note = self.holes[f"{part}_note"]
            notes_on = [key + offset for key in note["to_open"].nonzero()[0]]
            notes_off = [key + offset for key in note["to_close"].nonzero()[0]]

            # extension
            if self.holes[f"{part}_controls"]["to_open"][extension_port]:
                # already ON notes when extension begin
                notes_on.extend([key + offset + 12 for key in note["is_open"].nonzero()[0] if key in (46, 47, 48)])
            elif self.holes[f"{part}_controls"]["is_open"][extension_port]:
                notes_on.extend([key + offset + 12 for key in note["to_open"].nonzero()[0] if key in (46, 47, 48)])
                notes_off.extend([key + offset + 12 for key in note["to_close"].nonzero()[0] if key in (46, 47, 48)])
            elif self.holes[f"{part}_controls"]["to_close"][extension_port]:
                notes_off.extend([key + offset for key in range(58, 61)])

            # send MIDI signal
            [self.midi.note_on(note, velocity, midi_ch) for note in notes_on]
            [self.midi.note_off(note, channel=midi_ch) for note in notes_off]

        # pedal notes
        if self.ctrls["great"]["Pedal Bassoon 16"]["is_on"] or \
            self.ctrls["great"]["Pedal Flute f16"]["is_on"] or \
            self.ctrls["great"]["Pedal Flute p16"]["is_on"] or \
            self.ctrls["great"]["Pedal String 16"]["is_on"]:

            self.pedal_all_off = False
            note = self.holes["great_note"]
            if self.ctrls["swell"]["Pedal to Swell"]["is_on"]:
                note = self.holes["swell_note"]

            # pedal notes ON
            pedal_notes_on = [key + offset for key in note["to_open"].nonzero()[0] if key < 13]
            pedal_notes_off = [key + offset for key in note["to_close"].nonzero()[0] if key < 13]

            # pedal 2nd octave notes
            if self.holes["great_controls"]["to_open"][4] or self.holes["great_controls"]["to_open"][5]:
                # already ON notes when extension begin
                pedal_notes_on.extend([key + offset + 12 for key in note["is_open"].nonzero()[0] if key < 13])
            elif self.holes["great_controls"]["is_open"][4] or self.holes["great_controls"]["is_open"][5]:
                pedal_notes_on.extend([key + offset + 12 for key in note["to_open"].nonzero()[0] if key < 13])
                pedal_notes_off.extend([key + offset + 12 for key in note["to_close"].nonzero()[0] if key < 13])
            elif self.holes["great_controls"]["to_close"][4] or self.holes["great_controls"]["to_close"][5]:
                pedal_notes_off.extend([key + offset for key in range(13, 25)])

            # pedal 3rd octave notes
            if self.holes["great_controls"]["to_open"][5]:
                # already ON notes when extension begin
                pedal_notes_on.extend([key + offset + 24 for key in note["is_open"].nonzero()[0] if key < 8])
            elif self.holes["great_controls"]["is_open"][5]:
                pedal_notes_on.extend([key + offset + 24 for key in note["to_open"].nonzero()[0] if key < 8])
                pedal_notes_off.extend([key + offset + 24 for key in note["to_close"].nonzero()[0] if key < 8])
            elif self.holes["great_controls"]["to_close"][5]:
                pedal_notes_off.extend([key + offset for key in range(25, 32)])

            # send MIDI signal
            [self.midi.note_on(note, velocity, channel=2) for note in pedal_notes_on]
            [self.midi.note_off(note, channel=2) for note in pedal_notes_off]

        elif not self.pedal_all_off:
            # all off 32 notes
            [self.midi.note_off(k + offset, channel=2) for k in range(0, 32)]
            self.pedal_all_off = True

    def emulate_controls(self, curtime):
        if self.pre_time is None:
            self.pre_time = curtime
        delta_time = curtime - self.pre_time

        # check toggle switch holes
        for part, ctrls in self.ctrls.items():
            for key, val in ctrls.items():
                controls = self.holes[f"{part}_controls"]
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

                # update stop panel
                if self.stop_indicator is not None and "Shade" not in key:
                    part_name = "Swell Stops" if part == "swell" else "Great Stops"
                    part_name = "Pedal Stops" if "Pedal" in key else part_name
                    self.stop_indicator.change_stop({part_name: {key.lstrip("Pedal "): val["is_on"]}})

                note_no = val.get("midi_val")
                if note_no is not None:
                    if val["is_on"]:
                        self.midi.control_change(20, note_no, channel=3)
                    else:
                        # When treating multiple stops with the same note number, note-off after all stops is off
                        if part == "swell" and key in ("String Vibrato f", "String f", "String mf") and \
                            (self.ctrls["swell"]["String Vibrato f"]["is_on"] or \
                            self.ctrls["swell"]["String f"]["is_on"] or \
                            self.ctrls["swell"]["String mf"]["is_on"]):
                                continue

                        if part == "swell" and key in ("String p", "String pp") and \
                            (self.ctrls["swell"]["String p"]["is_on"] or \
                            self.ctrls["swell"]["String pp"]["is_on"]):
                                continue

                        if part == "swell" and key in ("Flute 4" , "Flute p") and \
                            (self.ctrls["swell"]["Flute 4"]["is_on"] or \
                            self.ctrls["swell"]["Flute p"]["is_on"]):
                                continue

                        if part == "great" and key in ("Flute p", "Flute f") and \
                            (self.ctrls["great"]["Flute p"]["is_on"] or \
                            self.ctrls["great"]["Flute f"]["is_on"]):
                                continue

                        if part == "great" and "Pedal Flute" in key and \
                            (self.ctrls["great"]["Pedal Flute f16"]["is_on"] or \
                            self.ctrls["great"]["Pedal Flute p16"]["is_on"]):
                                continue

                        self.midi.control_change(110, note_no, channel=3)

                if key == "Pedal to Swell":
                    # reset all pedal note
                    [self.midi.note_off(k, channel=2) for k in range(128)]

        # fix shade error
        self.fix_shade_error()

        # swell expression shade position
        target_val = self.shade["shade0"]
        for no in range(1, 6 + 1):
            if self.ctrls["swell"][f"Shade{no}"]["is_on"]:
                target_val = self.shade[f"shade{no}"]

        if target_val > self.swell_shade_val:
            self.swell_shade_val += delta_time * self.shade_change_rate
            self.swell_shade_val = min(self.swell_shade_val, target_val)
            self.midi.control_change(14, int(self.swell_shade_val), 3)
        elif target_val < self.swell_shade_val:
            self.swell_shade_val -= delta_time * self.shade_change_rate
            self.swell_shade_val = max(self.swell_shade_val, target_val)
            self.midi.control_change(14, int(self.swell_shade_val), 3)

        # great expression shade position
        target_val = self.shade["shade0"]
        for no in range(1, 6 + 1):
            if self.ctrls["great"][f"Shade{no}"]["is_on"]:
                target_val = self.shade[f"shade{no}"]

        if target_val > self.great_shade_val:
            self.great_shade_val += delta_time * self.shade_change_rate
            self.great_shade_val = min(self.great_shade_val, target_val)
            self.midi.control_change(15, int(self.great_shade_val), 3)
        elif target_val < self.great_shade_val:
            self.great_shade_val -= delta_time * self.shade_change_rate
            self.great_shade_val = max(self.great_shade_val, target_val)
            self.midi.control_change(15, int(self.great_shade_val), 3)

        self.pre_time = curtime

    def fix_shade_error(self):
        # Sometimes, shade errors occurs due to inconsistent on/off for each shade caused by perforation error etc...
        # So if the shade perforations are in order 3→2→1 to close, force reset all shade off
        for part in ("swell", "great"):
            for no in range(1, 3 + 1):
                hole_no = self.ctrls[part][f"Shade{no}"]["hole_no"]
                if self.holes[f"{part}_controls"]["to_close"][hole_no]:
                    if no == 3:
                        self.shade_error_detector[part] = []  # reset list
                    self.shade_error_detector[part].append(no)

                    # There were perforations in order 3, 2, 1 → shade is fully closed
                    if self.shade_error_detector[part] == [3, 2, 1]:
                        self.shade_error_detector[part] = []
                        # set all shade to off to fix error
                        for no in range(1, 6 + 1):
                            self.ctrls[part][f"Shade{no}"]["is_on"] = False

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
