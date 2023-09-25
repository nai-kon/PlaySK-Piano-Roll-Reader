import cv2
import numpy as np
import time
from enum import IntEnum, auto


def read_cis(path):
    # CIS file format are written in below
    # https://github.com/KerwoodDerby/flatbed-roll-scanner/blob/master/rollstitch/rollstitch.c

    with open(path, "rb") as f:
        bytes = f.read()

    descript = bytes[:32]
    status_flags = bytes[34:36]
    twin_array_sep = bytes[36:38]
    dpi = int.from_bytes(bytes[38:40], byteorder="little")
    width = int.from_bytes(bytes[40:42], byteorder="little")
    tempo = int.from_bytes(bytes[44:46], byteorder="little")
    lpi = int.from_bytes(bytes[46:48], byteorder="little")
    lines = int.from_bytes(bytes[48:52], byteorder="little")
    roll_data = bytes[52:]

    bicolor = bool(status_flags[0] & 0b01000000)

    class CurColor(IntEnum):
        NONE = auto()
        BG = auto()
        ROLL = auto()
        MARK = auto()

    # decode CIS
    roll_color = (90, 90, 90)
    bg_color = (255, 255, 255)
    black_color = (0, 0, 0)
    img_data = np.full((lines, width, 3), roll_color, np.uint8)
    cur_byte = 0
    for cur_line in range(lines - 1, 0, -1):
        # decode holes
        last_pos = 0
        cur_pix = CurColor.NONE
        none_end_pos = 0
        while True:
            change_len = int.from_bytes(roll_data[cur_byte:cur_byte + 2], byteorder="little")
            match cur_pix:
                case CurColor.NONE:
                    img_data[cur_line, last_pos:last_pos + change_len] = black_color
                    cur_pix = CurColor.BG
                    none_end_pos = change_len
                case CurColor.BG:
                    img_data[cur_line, last_pos:last_pos + change_len] = bg_color
                    cur_pix = CurColor.ROLL
                case CurColor.ROLL:
                    cur_pix = CurColor.BG

            cur_byte += 2
            last_pos += change_len
            if last_pos == width:
                cur_byte += 2
                break

        # decode lyrics
        last_pos = none_end_pos
        cur_pix = CurColor.BG
        while bicolor:
            change_len = int.from_bytes(roll_data[cur_byte:cur_byte + 2], byteorder="little")
            cur_byte += 2
            if change_len == 0:
                break

            if cur_pix == CurColor.MARK:
                img_data[cur_line, last_pos:last_pos + change_len] = black_color
            cur_pix = CurColor.MARK if cur_pix == CurColor.BG else CurColor.BG
            last_pos += change_len

    img_data = cv2.resize(img_data, dsize=None, fx=1, fy=lpi / dpi)

    return img_data, tempo


if __name__ == "__main__":
    s = time.time()
    img_data, _ = read_cis("../72013A.CIS")
    print(time.time() - s)
    cv2.imwrite("decoded_cis.tif", img_data)
