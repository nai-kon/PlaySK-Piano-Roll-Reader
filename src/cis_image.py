import wx
import cv2
import math
import numpy as np
import time
from cis_decoder.cis_decoder import get_outimg_size, decode_cis
from enum import Enum, IntEnum, auto


class ScannerType(Enum):
    UNKNOWN = "Unknown"
    FREERUN = "Free Run Scanner"
    WHEELRUN = "Wheel Encoder Scanner"
    SHAFTRUN = "Shaft Encoder Scanner"
    STEPPER = "Stepper Scanner"
    DELTA4 = "Delta 4 Scanner"


class CisImage:
    """
    Decode .CIS file to numpy array. Support bi-color, twin-array, encoder scanner, stepper scanner.
    The encoder scanner file will re-clocked to stepper scanner. Finally the vertical lpi will resize to same size of horizontal dpi.
    """
    def __init__(self) -> None:
        self.desc = ""
        self.scanner_type = ScannerType.UNKNOWN
        self.doubler = False
        self.twin_array = False
        self.bicolor = False
        self.encoder_division = 0
        self.mirror = False
        self.reverse = False
        self.vert_sep_twin = 0
        self.hol_dpi = 0
        self.hol_px = 0
        self.tempo = 0
        self.vert_res = 0  # lpi in stepper scanner. tpi in encoder wheel
        self.vert_px = 0
        self.img = None
        self.lpt = 0  # lines per tick. only for re-clock
        self.need_reclock = False  # reposition line

    def load(self, path):
        self._load_inner(path)
        return True
        try:
            self._load_inner(path)
            return True
        except Exception as e:
            wx.MessageBox(f"Failed to load a CIS image\n{e}", ".CIS Load error", style=wx.ICON_ERROR)

        return False

    def get_outimg_size(self, data):
        reclock_map: list[int, int] = []

        # width
        width = self.hol_px
        if self.twin_array:
            width = self.hol_px * 2 - self.overlap_twin

        # height
        height = self.vert_px
        if self.need_reclock:
            # calc height after reposition
            height = 0
            cur_idx = 0
            buf_lines = []
            pre_state = None
            chs = 1 + int(self.twin_array) + int(self.bicolor)
            for cur_line in range(self.vert_px - 1, 0, -1):
                for _ in range(chs):
                    last_pos = 0
                    while last_pos != self.hol_px:
                        change_len = data[cur_idx]
                        cur_idx += 1
                        last_pos += change_len

                encoder_val = data[cur_idx]
                # clock = bool(encoder_val & 32)
                state = bool(encoder_val & 128)
                if pre_state != state or cur_line == 0:
                    if buf_lines:
                        si = min(buf_lines)
                        ei = max(buf_lines)
                        # make re-clock map
                        for i in np.linspace(ei, si, self.lpt):
                            reclock_map.append([round(i), height])  # [src, dest]
                            height += 1
                        buf_lines = []

                buf_lines.append(cur_line)
                pre_state = state
                cur_idx += 1

            # adjust re-clock map
            for v in reclock_map:
                v[1] = height - v[1]

            if not reclock_map:
                raise ValueError("No encoder clock signal found")

            if height < self.vert_px:
                raise ValueError("Not support this type")

        print(width, height, self.vert_px)
        return width, height, reclock_map

    # slow python version. only used for debugging
    def decode_cis_py(self, data, out_img, vert_px, hol_px, bicolor, twin, twin_overlap, twin_vsep, reclock_map):
        class CurColor(IntEnum):
            BG = auto()
            ROLL = auto()
            MARK = auto()

        # decode CIS
        bg_color = (255, 255, 255)
        black_color = (0, 0, 0)
        cur_idx = 0
        twin_offset_x = hol_px - twin_overlap
        for cur_line in range(vert_px - 1, 0, -1):
            # decode holes
            last_pos = 0
            cur_pix = CurColor.ROLL
            while last_pos != hol_px:
                change_len = data[cur_idx]
                if cur_pix == CurColor.BG:
                    out_img[cur_line, last_pos:last_pos + change_len] = bg_color
                    cur_pix = CurColor.ROLL
                elif cur_pix == CurColor.ROLL:
                    cur_pix = CurColor.BG

                cur_idx += 1
                last_pos += change_len

            # decode twin-array right
            if twin:
                last_pos = 0
                cur_pix = CurColor.ROLL
                cur_line_twin = min(cur_line + twin_vsep, vert_px - 1)
                while last_pos != hol_px:
                    change_len = data[cur_idx]
                    if cur_pix == CurColor.BG:
                        sx = 2 * twin_offset_x - min(last_pos + change_len, twin_offset_x)
                        ex = 2 * twin_offset_x - min(last_pos, twin_offset_x)
                        out_img[cur_line_twin, sx:ex] = bg_color
                        cur_pix = CurColor.ROLL
                    elif cur_pix == CurColor.ROLL:
                        cur_pix = CurColor.BG

                    cur_idx += 1
                    last_pos += change_len

            # decode lyrics
            if bicolor:
                last_pos = 0
                cur_pix = CurColor.MARK
                while last_pos != hol_px:
                    change_len = data[cur_idx]
                    if cur_pix == CurColor.MARK:
                        out_img[cur_line, last_pos:last_pos + change_len] = black_color
                        cur_pix = CurColor.BG
                    elif cur_pix == CurColor.BG:
                        cur_pix = CurColor.MARK

                    cur_idx += 1
                    last_pos += change_len

            # encoder_val = data[cur_idx]  # not used
            cur_idx += 1

        if self.need_reclock:
            # reposition lines
            for src, dest in reclock_map:
                out_img[dest] = out_img[src]

    def _load_inner(self, path):
        # CIS file format
        # http://semitone440.co.uk/rolls/utils/cisheader/cis-format.htm#scantype

        with open(path, "rb") as f:
            bytes = f.read()

        self.desc = bytes[:32]
        status_flags = bytes[34:36]
        scanner_types = [
            ScannerType.UNKNOWN,
            ScannerType.FREERUN,
            ScannerType.WHEELRUN,
            ScannerType.SHAFTRUN,
            ScannerType.STEPPER,
            ScannerType.DELTA4,
        ]
        scanner_idx = int(status_flags[0] & 15)
        scanner_idx = scanner_idx if scanner_idx < len(scanner_types) else 0
        self.scanner_type = scanner_types[scanner_idx]
        self.need_reclock = self.scanner_type in [ScannerType.WHEELRUN, ScannerType.SHAFTRUN]
        self.doubler = bool(status_flags[0] & 16)
        self.twin_array = bool(status_flags[0] & 32)

        self.bicolor = bool(status_flags[0] & 64)
        self.encoder_division = 2 ** int(status_flags[1] & 15)
        self.mirror = bool(status_flags[1] & 16)
        self.reverse = bool(status_flags[1] & 32)
        self.vert_sep_twin = int.from_bytes(bytes[36:38], byteorder="little")
        self.hol_dpi = int.from_bytes(bytes[38:40], byteorder="little")
        self.hol_px = int.from_bytes(bytes[40:42], byteorder="little")
        self.overlap_twin = int.from_bytes(bytes[42:44], byteorder="little")
        self.tempo = int.from_bytes(bytes[44:46], byteorder="little")
        self.vert_res = int.from_bytes(bytes[46:48], byteorder="little")
        self.vert_px = int.from_bytes(bytes[48:52], byteorder="little")
        scan_data = np.frombuffer(bytes[52:], np.uint16)

        # for reclock
        division = self.vert_res / self.encoder_division
        self.lpt = round(self.hol_dpi / division)
        self.vert_res = round(self.lpt * division)

        # reserve output image
        out_w, out_h, reclock_map = get_outimg_size(scan_data, self.vert_px, self.hol_px, self.overlap_twin, self.lpt, self.bicolor, self.twin_array, self.need_reclock)
        # out_w, out_h, reclock_map = self.get_outimg_size(scan_data)

        start_padding_y = out_w // 2
        self.img = np.full((out_h + start_padding_y, out_w, 3), 120, np.uint8)
        self.img[self.vert_px:] = 255

        # decode scan data
        twin_overlap = self.overlap_twin // 2
        twin_vsep = math.ceil(self.vert_sep_twin * self.vert_res / 1000)
        decode_cis(scan_data, self.img, self.vert_px, self.hol_px, twin_overlap, twin_vsep, self.bicolor, self.twin_array, self.need_reclock, reclock_map)
        # self.decode_cis_py(scan_data, self.img, self.vert_px, self.hol_px, self.bicolor, self.twin_array, twin_overlap, twin_vsep, reclock_map)

        if len(self.img) == 0:
            raise BufferError

        self.hol_px = self.img.shape[1]

        # Resize horizontal and vertical to the same dpi
        if self.vert_res != self.hol_dpi:
            self.img = cv2.resize(self.img, dsize=None, fx=1, fy=self.hol_dpi / self.vert_res)


if __name__ == "__main__":
    app = wx.App()
    s = time.time()
    obj = CisImage()
    if obj.load("../72013A.CIS"):
        print(time.time() - s)
        cv2.imwrite("decoded_cis.png", obj.img)
