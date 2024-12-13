# cython: language_level=3

cimport cython
cimport numpy as cnp

cdef enum CurColor:
    BG = 0
    ROLL = 1
    MARK = 2


@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def _get_decode_params(cnp.ndarray[cnp.uint16_t, ndim=1] data, 
                    int vert_px, int hol_px, int lpt, bint is_bicolor, 
                    bint is_twin_array, bint is_clocked, int twin_array_overlap):

    cdef:
        int width = hol_px
        int height = vert_px
        int cur_idx = 0
        int last_pos = 0
        int val
        int si
        int ei
        int cur_line
        int change_len
        int encoder_val
        int encoder_state
        int pre_encoder_state = -1
        float step
        int chs = 1 + int(is_twin_array) + int(is_bicolor)
        list buf_lines = []
        list reclock_map = []

    cdef extern from "math.h":
        double rint(double x)

    # width
    if is_twin_array:
        width = hol_px * 2 - twin_array_overlap

    # height
    if is_clocked:
        # recalc height after reposition
        height = 0
        for cur_line in range(vert_px - 1, 0, -1):
            for _ in range(chs):
                last_pos = 0
                while last_pos != hol_px:
                    change_len = data[cur_idx]
                    cur_idx += 1
                    last_pos += change_len

            encoder_state = data[cur_idx] & 128
            if pre_encoder_state != encoder_state or cur_line == 0:
                if buf_lines:
                    ei = min(buf_lines)
                    si = max(buf_lines)
                    # make re-clock map
                    step = (ei - si) / float(lpt - 1)
                    for val in range(lpt):
                        val = int(rint(si + val * step))
                        reclock_map.append([val, height])  # [src line, dest line]
                        height += 1
                    buf_lines = []

            buf_lines.append(cur_line)
            pre_encoder_state = encoder_state
            cur_idx += 1

        # adjust re-clock map
        for cur_line in range(len(reclock_map)):
            reclock_map[cur_line][1] = height - reclock_map[cur_line][1] - 1

        if not reclock_map:
            raise ValueError("No encoder clock signal found")

        if height < vert_px:
            raise ValueError("Not support this type")

    return width, height, reclock_map


@cython.boundscheck(False)
@cython.wraparound(False)
def _decode_cis(cnp.ndarray[cnp.uint16_t, ndim=1] data, 
                cnp.ndarray[cnp.uint8_t, ndim=2] out_img, 
                int vert_px, int hol_px, bint is_bicolor, bint is_twin_array, bint is_clocked, 
                int twin_array_overlap, int twin_array_vsep, list reclock_map):

    # CIS file format
    # http://semitone440.co.uk/rolls/utils/cisheader/cis-format.htm#scantype

    cdef:
        cnp.uint8_t bg_color = 255
        cnp.uint8_t lyrics_color = 0
        int cur_idx = 0
        int last_pos = 0
        CurColor cur_pix = ROLL
        int change_len 
        int i
        int cur_line
        int cur_line_twin
        int twin_offset_x = hol_px - int(twin_array_overlap / 2)
        int sx
        int ex

    # decode lines
    for cur_line in range(vert_px - 1, 0, -1):
        last_pos = 0
        cur_pix = ROLL
        while last_pos != hol_px:
            change_len = data[cur_idx]
            if cur_pix == BG:
                for i in range(last_pos, last_pos + change_len):
                    out_img[cur_line, i] = bg_color
                cur_pix = ROLL
            elif cur_pix == ROLL:
                cur_pix = BG

            cur_idx += 1
            last_pos += change_len

        # decode is_twin_array-array right
        if is_twin_array:
            last_pos = 0
            cur_pix = ROLL
            cur_line_twin = cur_line + twin_array_vsep
            while last_pos != hol_px:
                change_len = data[cur_idx]
                if cur_pix == BG:
                    sx = 2 * twin_offset_x - min(last_pos + change_len, twin_offset_x)
                    ex = 2 * twin_offset_x - min(last_pos, twin_offset_x)
                    for i in range(sx, ex):
                        out_img[cur_line_twin, i] = bg_color
                    cur_pix = ROLL
                elif cur_pix == ROLL:
                    cur_pix = BG

                cur_idx += 1
                last_pos += change_len

        # decode lyrics
        if is_bicolor:
            last_pos = 0
            cur_pix = MARK
            while last_pos != hol_px:
                change_len = data[cur_idx]
                if cur_pix == MARK:
                    for i in range(last_pos, last_pos + change_len):
                        out_img[cur_line, i] = lyrics_color
                    cur_pix = BG
                elif cur_pix == BG:
                    cur_pix = MARK
                cur_idx += 1
                last_pos += change_len

        # encoder_val = data[cur_idx]  # not used
        cur_idx += 1

    if is_clocked:
        # reposition lines
        for sx, ex in reclock_map:
            out_img[ex] = out_img[sx]