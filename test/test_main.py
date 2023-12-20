import sys
from multiprocessing import Event, Pipe, Process

import pytest

sys.path.append("src/")
from main import SingleInstWin


class TestSingleInstWin():
    def inst_proc(self, sender, event):
        single_inst = SingleInstWin()
        is_exists = single_inst.is_exists()
        if sender is not None:
            sender.send(is_exists)
            sender.close()

        if event is not None:
            event.wait()

    def test_single_inst(self):
        # no prior instance
        event = Event()
        reciver, sender = Pipe(False)
        p = Process(target=self.inst_proc, args=(sender, event))
        p.start()
        is_exists = reciver.recv()
        assert not is_exists

        # already exists
        p2 = Process(target=self.inst_proc, args=(sender, None))
        p2.start()
        is_exists = reciver.recv()
        p2.join()
        assert is_exists
        event.set()
        p.join()
