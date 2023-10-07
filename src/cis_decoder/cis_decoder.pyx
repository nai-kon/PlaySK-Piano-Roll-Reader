# cython: language_level=3

cimport cython
cimport numpy as cnp

cdef enum CurColor:
    BG = 0
    ROLL = 1
    MARK = 2


@cython.boundscheck(False)
@cython.wraparound(False)
def get_outimg_size(cnp.ndarray[cnp.uint16_t, ndim=1] data, 
                    int vert_px, int hol_px, int overlap_twin, int lpt, 
                    bint bicolor, bint twin, bint need_reclock):

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
        float src_line
        float step
        int chs = 1 + int(twin) + int(bicolor)
        list buf_lines = []
        list reclock_map = []

    cdef extern from "math.h":
        double rint(double x)

    # width
    if twin:
        width = hol_px * 2 - overlap_twin

    # height
    if need_reclock:
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
                    step = (ei - si) / (lpt - 1)
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
            reclock_map[cur_line][1] = height - reclock_map[cur_line][1]

        if not reclock_map:
            raise ValueError("No encoder clock signal found")

        if height < vert_px:
            raise ValueError("Not support this type")

    return width, height, reclock_map


@cython.boundscheck(False)
@cython.wraparound(False)
def decode_cis(cnp.ndarray[cnp.uint16_t, ndim=1] data, 
                cnp.ndarray[cnp.uint8_t, ndim=3] out_img, 
                int vert_px, int hol_px, int twin_overlap, int twin_vsep,
                bint bicolor, bint twin, bint need_reclock, list reclock_map):

    # CIS file format
    # http://semitone440.co.uk/rolls/utils/cisheader/cis-format.htm#scantype

    cdef:
        cnp.uint8_t bg_color = 255
        cnp.uint8_t black_color = 0
        int cur_idx = 0
        int last_pos = 0
        CurColor cur_pix = ROLL
        int change_len 
        int i
        int cur_line
        int cur_line_twin
        int twin_offset_x = hol_px - twin_overlap
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
                    out_img[cur_line, i, 0] = bg_color
                    out_img[cur_line, i, 1] = bg_color
                    out_img[cur_line, i, 2] = bg_color
                cur_pix = ROLL
            elif cur_pix == ROLL:
                cur_pix = BG

            cur_idx += 1
            last_pos += change_len

        # decode twin-array right
        if twin:
            last_pos = 0
            cur_pix = ROLL
            cur_line_twin = min(cur_line + twin_vsep, vert_px - 1)
            while last_pos != hol_px:
                change_len = data[cur_idx]
                if cur_pix == BG:
                    sx = 2 * twin_offset_x - min(last_pos + change_len, twin_offset_x)
                    ex = 2 * twin_offset_x - min(last_pos, twin_offset_x)
                    for i in range(sx, ex):
                        out_img[cur_line_twin, i, 0] = bg_color
                        out_img[cur_line_twin, i, 1] = bg_color
                        out_img[cur_line_twin, i, 2] = bg_color
                    cur_pix = ROLL
                elif cur_pix == ROLL:
                    cur_pix = BG

                cur_idx += 1
                last_pos += change_len

        # decode lyrics
        if bicolor:
            last_pos = 0
            cur_pix = MARK
            while last_pos != hol_px:
                change_len = data[cur_idx]
                if cur_pix == MARK:
                    for i in range(last_pos, last_pos + change_len):
                        out_img[cur_line, i, 0] = black_color
                        out_img[cur_line, i, 1] = black_color
                        out_img[cur_line, i, 2] = black_color
                    cur_pix = BG
                elif cur_pix == BG:
                    cur_pix = MARK
                cur_idx += 1
                last_pos += change_len

        # encoder_val = data[cur_idx]  # not used
        cur_idx += 1

    if need_reclock:
        # reposition lines
        for sx, ex in reclock_map:
            out_img[ex] = out_img[sx]