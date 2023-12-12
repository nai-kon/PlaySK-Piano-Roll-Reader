import math
import time
from enum import Enum, IntEnum, auto
import cv2
import numpy as np
import wx

from cis_decoder.cis_decoder import _decode_cis, _get_decode_params


class ScannerType(Enum):
    UNKNOWN = "Unknown"
    FREERUN = "Free Run Scanner"
    WHEELENCODER = "Wheel Encoder Scanner"
    SHAFTENCODER = "Shaft Encoder Scanner"
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
        self.is_clocked = False
        self.is_twin_array = False
        self.is_bicolor = False
        self.encoder_division = 1
        # self.mirror = False  # not used now
        # self.reverse = False
        # self.clock_doubler = False
        self.vert_sep_twin = 0
        self.overlap_twin = 0
        self.hol_dpi = 0
        self.hol_px = 0
        self.tempo = 0
        self.vert_res = 0  # lpi in stepper scanner. tpi in encoder wheel
        self.vert_px = 0
        self.raw_img = None
        self.decode_img = None
        self.lpt = 0  # lines per tick. only for re-clock

    def load(self, path: str) -> bool:
        try:
            self._load_file(path)
            self._decode()
            return True
        except Exception as e:
            wx.MessageBox(f"Failed to load the CIS image\n{e}", ".CIS Load error", style=wx.ICON_ERROR)

        return False

    def _get_decode_params_py(self, data: np.ndarray) -> tuple[int, int, list[int, int]]:
        """
        Experimentally decode file and get output image size and re-clock position map.
        Python version.
        """
        reclock_map: list[int, int] = []  # src line idx, dest line idx

        # width
        width = self.hol_px
        if self.is_twin_array:
            width = self.hol_px * 2 - self.overlap_twin

        # height
        height = self.vert_px
        if self.is_clocked:
            # calc height after reposition
            height = 0
            cur_idx = 0
            buf_lines = []
            pre_state = None
            chs = 1 + int(self.is_twin_array) + int(self.is_bicolor)
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
                            reclock_map.append([round(i), height])
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
    def _decode_cis_py(self, data, out_img, vert_px, hol_px, twin_overlap, twin_vsep, end_padding_y, bicolor, twin, reclock_map) -> None:
        class CurColor(IntEnum):
            BG = auto()
            ROLL = auto()
            MARK = auto()

        # decode CIS
        bg_color = (255, 255, 255)
        black_color = (0, 0, 0)
        cur_idx = 0
        twin_offset_x = hol_px - twin_overlap
        for cur_line in range(vert_px + end_padding_y - 1, end_padding_y, -1):
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
                cur_line_twin = cur_line + twin_vsep
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

        if self.is_clocked:
            # reposition lines
            for src, dest in reclock_map:
                out_img[dest + end_padding_y] = out_img[src + end_padding_y]

    def _load_file(self, path: str) -> None:
        # CIS file format
        # http://semitone440.co.uk/rolls/utils/cisheader/cis-format.htm#scantype

        with open(path, "rb") as f:
            bytes = f.read()

        self.desc = bytes[:32]
        status_flags = bytes[34:36]
        scanner_types = [
            ScannerType.UNKNOWN,
            ScannerType.FREERUN,
            ScannerType.WHEELENCODER,
            ScannerType.SHAFTENCODER,
            ScannerType.STEPPER,
            ScannerType.DELTA4,
        ]
        scanner_idx = int(status_flags[0] & 15)
        scanner_idx = scanner_idx if scanner_idx < len(scanner_types) else 0
        self.scanner_type = scanner_types[scanner_idx]
        if self.scanner_type == ScannerType.UNKNOWN:
            self.hol_dpi = 200  # most of unknown type scanner is 200DPI
        else:
            self.is_clocked = self.scanner_type in [ScannerType.WHEELENCODER, ScannerType.SHAFTENCODER]
            self.is_twin_array = bool(status_flags[0] & 32)
            self.is_bicolor = bool(status_flags[0] & 64)
            self.encoder_division = 2 ** int(status_flags[1] & 15)
            # self.clock_doubler = bool(status_flags[0] & 16)  # not used now
            # self.mirror = bool(status_flags[1] & 16)
            # self.reverse = bool(status_flags[1] & 32)
            self.vert_sep_twin = int.from_bytes(bytes[36:38], byteorder="little")
            self.hol_dpi = int.from_bytes(bytes[38:40], byteorder="little")

        self.hol_px = int.from_bytes(bytes[40:42], byteorder="little")
        self.overlap_twin = int.from_bytes(bytes[42:44], byteorder="little")
        self.tempo = int.from_bytes(bytes[44:46], byteorder="little")
        self.vert_res = int.from_bytes(bytes[46:48], byteorder="little")
        self.vert_px = int.from_bytes(bytes[48:52], byteorder="little")
        self.raw_img = np.frombuffer(bytes[52:], np.uint16)

        # reclock parameters
        if self.is_clocked:
            division = self.vert_res / self.encoder_division
            self.lpt = round(self.hol_dpi / division)
            self.vert_res = round(self.lpt * division)

    def _decode(self) -> None:
        # get output image params
        out_w, out_h, reclock_map = _get_decode_params(self.raw_img, self.vert_px, self.hol_px, self.overlap_twin, self.lpt, self.is_bicolor, self.is_twin_array, self.is_clocked)
        # out_w, out_h, reclock_map = self.get_decode_params_py(self.raw_img)

        twin_overlap = self.overlap_twin // 2
        twin_vsep = math.ceil(self.vert_sep_twin * self.vert_res / 1000)

        # reserve decoded image with padding on start/end
        start_padding_y = out_w // 2
        end_padding_y = out_w // 2
        self.decode_img = np.full((out_h + start_padding_y + end_padding_y, out_w, 3), 120, np.uint8)
        self.decode_img[out_h + end_padding_y:] = 255

        # decode
        _decode_cis(self.raw_img, self.decode_img, self.vert_px, self.hol_px, twin_overlap, twin_vsep, end_padding_y, self.is_bicolor, self.is_twin_array, self.is_clocked, reclock_map)
        # self._decode_cis_py(self.raw_img, self.img, self.vert_px, self.hol_px, twin_overlap, twin_vsep, end_padding_y, self.bicolor, self.twin_array, reclock_map)

        if len(self.decode_img) == 0:
            raise BufferError

        # Resize horizontal and vertical to the same dpi
        self.hol_px = self.decode_img.shape[1]
        if self.vert_res != self.hol_dpi:
            self.decode_img = cv2.resize(self.decode_img, dsize=None, fx=1, fy=self.hol_dpi / self.vert_res)


if __name__ == "__main__":
    app = wx.App()
    s = time.time()
    obj = CisImage()
    if obj.load("../sample_Scans/Ampico B 68991 Papillons.CIS"):
        print(time.time() - s)
        cv2.imwrite("decoded_cis.png", obj.decode_img)
