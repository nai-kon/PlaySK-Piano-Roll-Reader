import glob
import json
import sys
import threading
import time

import numpy as np
import pytest

sys.path.append("src/")
from midi_controller import MidiWrap
from tracker_bars.base_player import BasePlayer, TrackerHoles


class TestTrackerHoles:
    def test_tracker_holes(self):
        for path in glob.glob("src/playsk_config/*.json"):
            if path.endswith("config.json"):
                continue
            with open(path, encoding="utf-8") as f:
                conf = json.load(f)
            holes = TrackerHoles(conf)

            # off
            th = holes.th_bright + 1 if holes.is_dark_hole else holes.th_bright - 1
            frame = np.full((600, 800, 3), th, np.uint8)
            holes.set_frame(frame, 0)
            for v in holes.group_by_size.values():
                assert (~v["to_open"]).all()
                assert (~v["to_close"]).all()
                assert (~v["is_open"]).all()

            # off -> on
            th = holes.th_bright - 1 if holes.is_dark_hole else holes.th_bright + 1
            frame = np.full((600, 800, 3), th, np.uint8)
            holes.set_frame(frame, 0)
            for v in holes.group_by_size.values():
                assert v["to_open"].all()
                assert (~v["to_close"]).all()
                assert v["is_open"].all()

            # on
            th = holes.th_bright - 1 if holes.is_dark_hole else holes.th_bright + 1
            frame = np.full((600, 800, 3), th, np.uint8)
            holes.set_frame(frame, 0)
            for v in holes.group_by_size.values():
                assert (~v["to_open"]).all()
                assert (~v["to_close"]).all()
                assert v["is_open"].all()

            # on -> off
            th = holes.th_bright + 1 if holes.is_dark_hole else holes.th_bright - 1
            frame = np.full((600, 800, 3), th, np.uint8)
            holes.set_frame(frame, 0)
            for v in holes.group_by_size.values():
                assert (~v["to_open"]).all()
                assert v["to_close"].all()
                assert (~v["is_open"]).all()

            # all off
            holes.all_off()
            for v in holes.group_by_size.values():
                assert (~v["to_open"]).all()
                assert (~v["to_close"]).all()
                assert (~v["is_open"]).all()

    def test_getitem(self):
        with open("src/playsk_config/88 Note.json", encoding="utf-8") as f:
            conf = json.load(f)
        holes = TrackerHoles(conf)
        frame = np.full((600, 800, 3), 0, np.uint8)
        holes.set_frame(frame, 0)

        # check sustain hole
        sustain_hole = holes["sustain"]
        assert sustain_hole["pos"] == [(34, 294, 42, 304)]
        assert not sustain_hole["is_open"]
        assert not sustain_hole["to_open"]
        assert not sustain_hole["to_close"]

        # open
        frame = np.full((600, 800, 3), 255, np.uint8)
        holes.set_frame(frame, 0)
        sustain_hole = holes["sustain"]
        assert sustain_hole["is_open"]
        assert sustain_hole["to_open"]
        assert not sustain_hole["to_close"]

        with pytest.raises(KeyError):
            sustain_hole = holes["not exists hole"]


class TestPlayer:
    @pytest.fixture
    def player(self):
        midiobj = MidiWrap()
        obj = BasePlayer("src/playsk_config/88 Note.json", midiobj)
        return obj

    def call_emulate_th(self, obj, frame):
        while obj.do_test_th:
            cur_time = time.perf_counter()
            obj.emulate(frame, cur_time)
            time.sleep(0.01)
        return

    def test_calc_velocity(self, player):
        # check bass/treble intensity is correct
        player.bass_vacuum = 4
        player.treble_vacuum = 40
        bass_velo, treble_velo = player.calc_velocity()
        assert player.velocity[0] - 1 < bass_velo < player.velocity[0] + 1
        assert player.velocity[-1] - 1 < treble_velo < player.velocity[-1] + 1

        player.bass_vacuum = 40
        player.treble_vacuum = 4
        bass_velo, treble_velo = player.calc_velocity()
        assert player.velocity[-1] - 1 < bass_velo < player.velocity[-1] + 1
        assert player.velocity[0] - 1 < treble_velo < player.velocity[0] + 1

    def test_emulate_off(self, player):
        player.emulate_on()
        player.do_test_th = True

        # check emulate off works while emulates() is called from another thread
        hole_color = player.holes.th_bright - 1 if player.holes.is_dark_hole else player.holes.th_bright + 1
        frame = np.full((600, 800, 3), hole_color, np.uint8)
        th = threading.Thread(target=self.call_emulate_th, args=(player, frame))
        th.start()
        time.sleep(1)
        player.emulate_off()
        time.sleep(0.1)
        try:
            assert not player.emulate_enable
            assert player.during_emulate_evt.is_set()
            for v in player.holes.group_by_size.values():
                assert (~v["to_open"]).all()
                assert (~v["to_close"]).all()
                assert (~v["is_open"]).all()
        except Exception as e:
            # stop test thread firstly
            player.do_test_th = False
            th.join()
            raise e
        else:
            player.do_test_th = False
            th.join()

    def test_emulate_off_timeout(self, monkeypatch, player):
        # test emulate_off will timeout in 1sec
        def heavy_emulate_notes(self):
            time.sleep(2)

        player.emulate_on()
        player.do_test_th = True

        hole_color = player.holes.th_bright - 1 if player.holes.is_dark_hole else player.holes.th_bright + 1
        frame = np.full((600, 800, 3), hole_color, np.uint8)
        monkeypatch.setattr(BasePlayer, "emulate_notes", heavy_emulate_notes)
        th = threading.Thread(target=self.call_emulate_th, args=(player, frame))
        th.start()
        time.sleep(1)
        start_time = time.time()
        player.emulate_off()  # this will time out in 1sec
        time.sleep(0.1)
        elapsed_time = time.time() - start_time
        try:
            assert 1.0 < elapsed_time < 1.5
            assert not player.emulate_enable
            assert player.during_emulate_evt.is_set()
            for v in player.holes.group_by_size.values():
                assert (~v["to_open"]).all()
                assert (~v["to_close"]).all()
                assert (~v["is_open"]).all()
        except Exception as e:
            # stop test thread firstly
            player.do_test_th = False
            th.join()
            raise e
        else:
            player.do_test_th = False
            th.join()

    def test_emulate_on(self, player):
        player.emulate_off()
        player.emulate_on()
        assert player.emulate_enable

    def test_auto_track(self, player):
        player.tracker_offset = 0
        player.auto_tracking = True
        roll = 130
        bg = player.holes.th_bright - 1 if player.holes.is_dark_hole else player.holes.th_bright + 1

        # no offset
        frame = np.full((600, 800, 3), bg, np.uint8)
        frame[:, 10:790] = roll
        pre_offset = player.tracker_offset
        player.auto_track(frame)
        assert pre_offset == player.tracker_offset

        # right offset
        frame = np.full((600, 800, 3), bg, np.uint8)
        frame[:, 15:798] = roll
        player.auto_track(frame)
        print(player.tracker_offset)
        assert player.tracker_offset == 5

        # left offset
        frame = np.full((600, 800, 3), bg, np.uint8)
        frame[:, 2:785] = roll
        player.auto_track(frame)
        print(player.tracker_offset)
        assert player.tracker_offset == -5

        # auto tracking off
        player.auto_tracking = False
        frame = np.full((600, 800, 3), bg, np.uint8)
        frame[:, 15:798] = roll
        pre_offset = player.tracker_offset
        player.auto_track(frame)
        assert pre_offset == player.tracker_offset

    def test_emulate_expression(self, player):
        pre_vacuum = [player.bass_vacuum, player.treble_vacuum]
        player.emulate_expression(0)
        cur_vacuum  = [player.bass_vacuum, player.treble_vacuum]
        assert pre_vacuum == cur_vacuum  # nothing changes on 88-notes

    def test_emulate_pedals(self, player, mocker):
        hole_color = player.holes.th_bright - 1 if player.holes.is_dark_hole else player.holes.th_bright + 1
        roll_color = 130
        frame = np.full((600, 800, 3), roll_color, np.uint8)

        # sustain on
        sustain_on_mock = mocker.patch("midi_controller.MidiWrap.sustain_on")
        x1, y1, x2, y2 = player.holes["sustain"]["pos"][0]
        frame[y1:y2, x1:x2, :] = hole_color
        player.holes.set_frame(frame, 0)
        player.emulate_pedals()
        sustain_on_mock.assert_called_once()

        # sustain off
        sustain_off_mock = mocker.patch("midi_controller.MidiWrap.sustain_off")
        frame[y1:y2, x1:x2, :] = roll_color
        player.holes.set_frame(frame, 0)
        player.emulate_pedals()
        sustain_off_mock.assert_called_once()

        # hammer rail on
        hammer_on_mock = mocker.patch("midi_controller.MidiWrap.hammer_lift_on")
        x1, y1, x2, y2 = player.holes["soft"]["pos"][0]
        frame[y1:y2, x1:x2, :] = hole_color
        player.holes.set_frame(frame, 0)
        player.emulate_pedals()
        hammer_on_mock.assert_called_once()

        # hammer rail off
        hammer_off_mock = mocker.patch("midi_controller.MidiWrap.hammer_lift_off")
        frame[y1:y2, x1:x2, :] = roll_color
        player.holes.set_frame(frame, 0)
        player.emulate_pedals()
        hammer_off_mock.assert_called_once()

    def test_emulate_notes(self, player, mocker):
        hole_color = player.holes.th_bright - 1 if player.holes.is_dark_hole else player.holes.th_bright + 1
        roll_color = 130
        note_offset = 21
        player.bass_vacuum = 5
        player.treble_vacuum = 40
        bass_velocity, treble_velocity = player.calc_velocity()

        # note on
        frame = np.full((600, 800, 3), roll_color, np.uint8)
        noteon_mock = mocker.patch("midi_controller.MidiWrap.note_on")
        for key, (x1, y1, x2, y2) in enumerate(player.holes["note"]["pos"]):
            frame[y1:y2, x1:x2, :] = hole_color
            player.holes.set_frame(frame, 0)
            player.emulate_notes()
            gtvelo = bass_velocity if key < player.stack_split else treble_velocity
            noteon_mock.assert_called_with(key + note_offset, gtvelo)

        # note off
        noteoff_mock = mocker.patch("midi_controller.MidiWrap.note_off")
        for key, (x1, y1, x2, y2) in enumerate(player.holes["note"]["pos"]):
            frame[y1:y2, x1:x2, :] = roll_color
            player.holes.set_frame(frame, 0)
            player.emulate_notes()
            noteoff_mock.assert_called_with(key + note_offset)
