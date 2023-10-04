# cython: language_level=3

cimport cython
cimport numpy as cnp

cdef enum CurColor:
    BG = 0
    ROLL = 1
    MARK = 2

@cython.boundscheck(False)
@cython.wraparound(False)
def decode_cis(cnp.ndarray[cnp.uint16_t, ndim=1] data, cnp.ndarray[cnp.uint8_t, ndim=3] out_img, int vert_px, int hol_px, bint bicolor, bint twin, int twin_overlap, int twin_vsep):

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

    for cur_line in range(vert_px - 1, 0, -1):

        # decode holes
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