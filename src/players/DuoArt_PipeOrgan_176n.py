from collections import deque

from .base_player import BasePlayer


class DuoArtOrgan(BasePlayer):
    def __init__(self, confpath, midiobj):
        super().__init__(confpath, midiobj)

    def emulate_notes(self):
        note = self.holes["swell_note"]
        offset = 15 + 21

        on_notes = note["to_open"].nonzero()[0]
        if on_notes.size > 0:
            bass_velo, treble_velo = self.calc_velocity()
            for key in on_notes:
                velo = bass_velo if key < self.stack_split else treble_velo
                self.midi.note_on(key + offset, velo, channel=0)

        for key in note["to_close"].nonzero()[0]:
            self.midi.note_off(key + offset, channel=0)

        note = self.holes["great_note"]
        offset = 15 + 21

        on_notes = note["to_open"].nonzero()[0]
        if on_notes.size > 0:
            bass_velo, treble_velo = self.calc_velocity()
            for key in on_notes:
                velo = bass_velo if key < self.stack_split else treble_velo
                self.midi.note_on(key + offset, velo, channel=1)

        for key in note["to_close"].nonzero()[0]:
            self.midi.note_off(key + offset, channel=1)

    def emulate_controls(self):
        pass



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
