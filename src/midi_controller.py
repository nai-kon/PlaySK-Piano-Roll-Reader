import mido
import mido.backends.rtmidi
from mido import Message


class MidiWrap:
    """wrapper of mido library"""

    def __init__(self) -> None:
        self.output = None
        self.enable: bool = False
        self.hammer_lift: bool = False

    @property
    def port_list(self) -> list[str]:
        return mido.get_output_names()

    def open_port(self, name: str) -> bool:
        self.close_port()
        try:
            self.output = mido.open_output(name, autoreset=True)
            self.enable = True
        except Exception as e:
            print(e)

        return self.enable

    def __del__(self) -> None:
        self.close_port()

    def close_port(self) -> None:
        if self.enable:
            self.enable = False
            self.all_off()
            self.output.close()

    def all_off(self) -> None:
        if self.enable:
            # some device not support all note off message
            self.sustain_off()
            self.soft_off()
            self.hammer_lift_off()
            [self.note_off(k) for k in range(128)]

            self.output.reset()

    def note_on(self, note: int, velocity: int) -> None:
        if self.enable:
            if self.hammer_lift:
                velocity -= 8
            self.output.send(Message("note_on", note=note, velocity=velocity))

    def note_off(self, note: int, velocity: int = 90) -> None:
        if self.enable:
            self.output.send(Message("note_off", note=note, velocity=velocity))

    def sustain_on(self) -> None:
        if self.enable:
            self.output.send(Message("control_change", control=64, value=127))

    def sustain_off(self) -> None:
        if self.enable:
            self.output.send(Message("control_change", control=64, value=0))

    def soft_on(self) -> None:
        if self.enable:
            self.output.send(Message("control_change", control=67, value=127))

    def soft_off(self) -> None:
        if self.enable:
            self.output.send(Message("control_change", control=67, value=0))

    def hammer_lift_on(self) -> None:
        self.hammer_lift = True

    def hammer_lift_off(self) -> None:
        self.hammer_lift = False


if __name__ == "__main__":
    import time

    obj = MidiWrap()
    print(obj.port_list)
    assert not obj.open_port("not_exists"), "error at opening not exists port"
    assert obj.open_port(None), "failed to open default midi port"

    obj.note_on(60, 120)
    time.sleep(1)
    print("before all off")
    obj.all_off()

    time.sleep(1)
    obj.note_on(60, 120)
    time.sleep(1)
    print("before close")
    obj.close_port()

    time.sleep(1)
    obj.open_port(None)
    obj.note_on(60, 120)
    time.sleep(1)
    print("before destruct")
    obj = None
