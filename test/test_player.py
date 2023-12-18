import glob
import json
import sys
import threading
import time

import numpy as np
import pytest

sys.path.append("src/")
from midi_controller import MidiWrap
from src.player import Player, TrackerHoles


class TestTrackerHoles():
    def test_tracker_holes(self):
        for path in glob.glob("src/config/*.json"):
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


class TestPlayer():
    @pytest.fixture
    def player(self):
        midiobj = MidiWrap()
        obj = Player("src/config/88 Note white background.json", midiobj)
        return obj

    def call_emulate_th(self, obj, frame):
        while obj.do_test_th:
            cur_time = time.perf_counter()
            obj.emulate(frame, cur_time)
            time.sleep(0.01)
        return

    def test_calc_velocity(self, player):
        # check bass/treble intensity is correct
        player.bass_vacuum = 5
        player.treble_vacuum = 40
        bass_velo, treble_velo = player.calc_velocity()
        assert player.velocity[0] - 1 < bass_velo < player.velocity[0] + 1
        assert player.velocity[-1] - 1 < treble_velo < player.velocity[-1] + 1

        player.bass_vacuum = 40
        player.treble_vacuum = 5
        bass_velo, treble_velo = player.calc_velocity()
        assert player.velocity[-1] - 1 < bass_velo < player.velocity[-1] + 1
        assert player.velocity[0] - 1 < treble_velo < player.velocity[0] + 1

    def test_emulate_off(self, player):
        player.emulate_on()
        player.do_test_th = True

        # check emulate off works while emulates() is called from another thread 
        th = player.holes.th_bright - 1 if player.holes.is_dark_hole else player.holes.th_bright + 1
        frame = np.full((600, 800, 3), th, np.uint8)
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

        th = player.holes.th_bright - 1 if player.holes.is_dark_hole else player.holes.th_bright + 1
        frame = np.full((600, 800, 3), th, np.uint8)
        monkeypatch.setattr(Player, "emulate_notes", heavy_emulate_notes)
        th = threading.Thread(target=self.call_emulate_th, args=(player, frame))
        th.start()
        time.sleep(1)
        start_time = time.time()
        player.emulate_off()  # this will time out in 1sec
        time.sleep(0.1)
        elapsed_time = time.time() - start_time
        try:
            assert 1.1 < elapsed_time < 1.5
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

    def test_auto_track(self, monkeypatch, player):
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
