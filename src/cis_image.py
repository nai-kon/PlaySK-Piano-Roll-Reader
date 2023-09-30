import wx
import cv2
import numpy as np
import time
from cis_decoder.cis_decoder import decode_cis
from enum import Enum, IntEnum, auto


class ScannerType(Enum):
    UNKNOWN = "Unknown"
    FREERUN = "Free Run Scanner"
    WHEELRUN = "Wheel Encoder Scanner"
    SHAFTRUN = "Shaft Encoder Scanner"
    STEPPER = "Stepper Scanner"
    DELTA4 = "Delta 4 Scanner"


class CisImage:
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
        self.img_data = None

    def load(self, path):
        try:
            self._load_inner(path)
            return True
        except NotImplementedError as e:
            wx.MessageBox(str(e), "Load error")
        except Exception:
            wx.MessageBox("Failed to load a CIS image", "Load error")

        return False

    # slow pure python version. cython version is in cis_decoder/cis_decoder.pyx
    def decode_cis_py(self, data, out_img, vert_px, hol_px, bicolor):
        class CurColor(IntEnum):
            NONE = auto()
            BG = auto()
            ROLL = auto()
            MARK = auto()

        # decode CIS
        bg_color = (255, 255, 255)
        black_color = (0, 0, 0)
        cur_idx = 0
        for cur_line in range(vert_px - 1, 0, -1):
            # decode holes
            last_pos = 0
            cur_pix = CurColor.NONE
            none_end_pos = 0
            while True:
                change_len = data[cur_idx]
                match cur_pix:
                    case CurColor.NONE:
                        out_img[cur_line, last_pos:last_pos + change_len] = black_color
                        cur_pix = CurColor.BG
                        none_end_pos = change_len
                    case CurColor.BG:
                        out_img[cur_line, last_pos:last_pos + change_len] = bg_color
                        cur_pix = CurColor.ROLL
                    case CurColor.ROLL:
                        cur_pix = CurColor.BG

                cur_idx += 1
                last_pos += change_len
                if last_pos == hol_px:
                    cur_idx += 1
                    break

            # decode lyrics
            last_pos = none_end_pos
            cur_pix = CurColor.BG
            while bicolor:
                change_len = data[cur_idx]
                cur_idx += 1
                if change_len == 0:
                    break

                if cur_pix == CurColor.MARK:
                    out_img[cur_line, last_pos:last_pos + change_len] = black_color
                cur_pix = CurColor.MARK if cur_pix == CurColor.BG else CurColor.BG
                last_pos += change_len

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
        self.doubler = bool(status_flags[0] & 16)
        self.twin_array = bool(status_flags[0] & 32)
        if self.twin_array:
            raise NotImplementedError("Twin array scanner image is not suppoted")

        self.bicolor = bool(status_flags[0] & 64)
        self.encoder_division = int(status_flags[1] & 15)
        self.mirror = bool(status_flags[1] & 16)
        self.reverse = bool(status_flags[1] & 32)
        self.vert_sep_twin = int.from_bytes(bytes[36:38], byteorder="little")
        self.hol_dpi = int.from_bytes(bytes[38:40], byteorder="little")
        self.hol_px = int.from_bytes(bytes[40:42], byteorder="little")
        self.tempo = int.from_bytes(bytes[44:46], byteorder="little")
        self.vert_res = int.from_bytes(bytes[46:48], byteorder="little")  # lpi in stepper scanner. tpi in encoder wheel
        self.vert_px = int.from_bytes(bytes[48:52], byteorder="little")
        scan_data = np.frombuffer(bytes[52:], np.uint16)

        self.img_data = np.full((self.vert_px, self.hol_px, 3), 120, np.uint8)

        # self.decode_cis(scan_data.tolist(), self.img_data, self.vert_px, self.hol_px, self.bicolor)

        # written in cython for speed up
        decode_cis(scan_data, self.img_data, self.vert_px, self.hol_px, self.bicolor)

        if len(self.img_data) == 0:
            raise BufferError

        if self.scanner_type not in [ScannerType.WHEELRUN, ScannerType.SHAFTRUN] and self.vert_res != self.hol_dpi:
            self.img_data = cv2.resize(self.img_data, dsize=None, fx=1, fy=self.hol_dpi / self.vert_res)


if __name__ == "__main__":
    app = wx.App()
    s = time.time()
    obj = CisImage()
    if obj.load("../Ampico 68383 Appassionate Sonata 3nd mvt.CIS"):
        print(time.time() - s)
        cv2.imwrite("decoded_cis.png", obj.img_data)
