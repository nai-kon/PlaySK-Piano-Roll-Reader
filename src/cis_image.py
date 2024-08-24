import math
import time
from enum import Enum, IntEnum, auto

import cv2
import numpy as np
import wx

try:
    from cis_decoder.cis_decoder import _decode_cis, _get_decode_params
except ModuleNotFoundError as e:
    raise ModuleNotFoundError(
        """
        Can't import cis_decoder. Did you build cis_decoder?
        1. cd cis_decoder/
        2. python setup.py build_ext --inplace
        """,
    ) from e


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
        self.twin_array_vert_sep = 0
        self.twin_array_overlap = 0
        self.hol_dpi = 0
        self.hol_px = 0
        self.tempo = 0
        self.vert_res = 0  # lpi in stepper scanner. tpi in encoder wheel
        self.vert_px = 0
        self.raw_img = None
        self.decoded_img = None
        self.lpt = 0  # lines per tick. only for re-clock

    def load(self, path: str) -> bool:
        try:
            self._load_file(path)
            self._decode()
            return True
        except Exception as e:
            wx.MessageBox(f"Failed to load the CIS image\n{e}", ".CIS Load error", style=wx.ICON_ERROR)

        return False

    def convert_bw(self):
        """
        Some cis files are scanned with a black roll background, so convert it to white
        """

        if self.decoded_img is not None:
            self.decoded_img[self.decoded_img == 0] = 255
        

    def _get_decode_params_py(self) -> tuple[int, int, list[int, int]]:
        """
        Experimentally decode file and get output image size and re-clock position map.
        Python version.
        """
        reclock_map: list[int, int] = []  # src line idx, dest line idx

        # width
        width = self.hol_px
        if self.is_twin_array:
            width = self.hol_px * 2 - self.twin_array_overlap

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
                        change_len = self.raw_img[cur_idx]
                        cur_idx += 1
                        last_pos += change_len

                encoder_val = self.raw_img[cur_idx]
                # clock = bool(encoder_val & 32)
                state = bool(encoder_val & 128)
                if (pre_state != state or cur_line == 0) and buf_lines:
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
    def _decode_cis_py(self, output_img, end_padding_y, twin_array_vert_sep, reclock_map) -> None:
        class CurColor(IntEnum):
            BG = auto()
            ROLL = auto()
            MARK = auto()

        # decode CIS
        bg_color = (255, 255, 255)
        black_color = (0, 0, 0)
        cur_idx = 0
        twin_offset_x = self.hol_px - self.twin_array_overlap // 2
        for cur_line in range(self.vert_px + end_padding_y - 1, end_padding_y, -1):
            # decode holes
            last_pos = 0
            cur_pix = CurColor.ROLL
            while last_pos != self.hol_px:
                change_len = self.raw_img[cur_idx]
                if cur_pix == CurColor.BG:
                    output_img[cur_line, last_pos:last_pos + change_len] = bg_color
                    cur_pix = CurColor.ROLL
                elif cur_pix == CurColor.ROLL:
                    cur_pix = CurColor.BG

                cur_idx += 1
                last_pos += change_len

            # decode twin-array image
            if self.is_twin_array:
                last_pos = 0
                cur_pix = CurColor.ROLL
                cur_line_twin = cur_line + twin_array_vert_sep
                while last_pos != self.hol_px:
                    change_len = self.raw_img[cur_idx]
                    if cur_pix == CurColor.BG:
                        sx = 2 * twin_offset_x - min(last_pos + change_len, twin_offset_x)
                        ex = 2 * twin_offset_x - min(last_pos, twin_offset_x)
                        output_img[cur_line_twin, sx:ex] = bg_color
                        cur_pix = CurColor.ROLL
                    elif cur_pix == CurColor.ROLL:
                        cur_pix = CurColor.BG

                    cur_idx += 1
                    last_pos += change_len

            # decode lyrics
            if self.is_bicolor:
                last_pos = 0
                cur_pix = CurColor.MARK
                while last_pos != self.hol_px:
                    change_len = self.raw_img[cur_idx]
                    if cur_pix == CurColor.MARK:
                        output_img[cur_line, last_pos:last_pos + change_len] = black_color
                        cur_pix = CurColor.BG
                    elif cur_pix == CurColor.BG:
                        cur_pix = CurColor.MARK

                    cur_idx += 1
                    last_pos += change_len

            cur_idx += 1

        if self.is_clocked:
            # reposition lines
            for src, dest in reclock_map:
                output_img[dest + end_padding_y] = output_img[src + end_padding_y]

    def _load_file(self, path: str) -> None:
        # CIS file format
        # http://semitone440.co.uk/rolls/utils/cisheader/cis-format.htm#scantype

        with open(path, "rb") as f:
            data = f.read()

        self.desc = data[:32]
        status_flags = data[34:36]
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
            self.is_clocked = self.scanner_type in (ScannerType.WHEELENCODER, ScannerType.SHAFTENCODER)
            self.is_twin_array = bool(status_flags[0] & 32)
            self.is_bicolor = bool(status_flags[0] & 64)
            self.encoder_division = 2 ** int(status_flags[1] & 15)
            # self.clock_doubler = bool(status_flags[0] & 16)  # not used now
            # self.mirror = bool(status_flags[1] & 16)
            # self.reverse = bool(status_flags[1] & 32)
            self.twin_array_vert_sep = int.from_bytes(data[36:38], byteorder="little")
            self.hol_dpi = int.from_bytes(data[38:40], byteorder="little")

        self.hol_px = int.from_bytes(data[40:42], byteorder="little")
        self.twin_array_overlap = int.from_bytes(data[42:44], byteorder="little")
        self.tempo = int.from_bytes(data[44:46], byteorder="little")
        self.vert_res = int.from_bytes(data[46:48], byteorder="little")
        self.vert_px = int.from_bytes(data[48:52], byteorder="little")
        self.raw_img = np.frombuffer(data[52:], np.uint16)

        # reclock parameters
        if self.is_clocked:
            division = self.vert_res / self.encoder_division
            self.lpt = round(self.hol_dpi / division)
            self.vert_res = round(self.lpt * division)

    def _decode(self, use_cython=True) -> None:
        # get actual output image size and reclock info
        if use_cython:
            out_w, out_h, reclock_map = _get_decode_params(self.raw_img, self.vert_px, self.hol_px, self.lpt, self.is_bicolor, self.is_twin_array, self.is_clocked, self.twin_array_overlap)
        else:
            out_w, out_h, reclock_map = self._get_decode_params_py()

        twin_array_vert_sep = math.ceil(self.twin_array_vert_sep * self.vert_res / 1000)

        # reserve decoded image with padding on start/end
        start_padding_y = out_w // 2
        end_padding_y = out_w // 2
        self.decoded_img = np.full((out_h + start_padding_y + end_padding_y, out_w, 3), 120, np.uint8)
        self.decoded_img[out_h + end_padding_y:] = 255

        # decode
        if use_cython:
            _decode_cis(self.raw_img, self.decoded_img, self.vert_px, self.hol_px, self.is_bicolor, self.is_twin_array, self.is_clocked,
                        self.twin_array_overlap, twin_array_vert_sep, end_padding_y, reclock_map)
        else:
            self._decode_cis_py(self.decoded_img, end_padding_y, twin_array_vert_sep, reclock_map)

        if len(self.decoded_img) == 0:
            raise BufferError

        # Resize horizontal and vertical to the same dpi
        self.hol_px = self.decoded_img.shape[1]
        if self.vert_res != self.hol_dpi:
            self.decoded_img = cv2.resize(self.decoded_img, dsize=None, fx=1, fy=self.hol_dpi / self.vert_res)


if __name__ == "__main__":
    app = wx.App()
    s = time.time()
    obj = CisImage()
    if obj.load("../sample_Scans/Ampico B 68991 Papillons.CIS"):
        print(time.time() - s)
        cv2.imwrite("decoded_cis.png", obj.decoded_img)
