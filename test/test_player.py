import glob
import json
import sys

import numpy as np
import pytest

sys.path.append("src/")
from src.player import Player, TrackerHoles


class TestTrackerHoles():
    def test_tracker_holes(self):
        for path in glob.glob("src/config/*.json"):
            if path.endswith("config.json"):
                continue
            with open(path, encoding="utf-8") as f:
                conf = json.load(f)
            holes = TrackerHoles(conf)

            # holes are off
            th = holes.th_bright + 1 if holes.is_dark_hole else holes.th_bright - 1
            frame = np.full((600, 800, 3), th, np.uint8)
            holes.set_frame(frame, 0)
            for v in holes.group_by_size.values():
                assert (~v["to_open"]).all()
                assert (~v["to_close"]).all()
                assert (~v["is_open"]).all()

            # holes are off -> on
            th = holes.th_bright - 1 if holes.is_dark_hole else holes.th_bright + 1
            frame = np.full((600, 800, 3), th, np.uint8)
            holes.set_frame(frame, 0)
            for v in holes.group_by_size.values():
                assert v["to_open"].all()
                assert (~v["to_close"]).all()
                assert v["is_open"].all()

            # holes are on
            th = holes.th_bright - 1 if holes.is_dark_hole else holes.th_bright + 1
            frame = np.full((600, 800, 3), th, np.uint8)
            holes.set_frame(frame, 0)
            for v in holes.group_by_size.values():
                assert (~v["to_open"]).all()
                assert (~v["to_close"]).all()
                assert v["is_open"].all()

            # holes are on -> off
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
