# cython: language_level=3

cimport cython
cimport numpy as cnp

cdef enum CurColor:
    BG = 0
    ROLL = 1
    MARK = 2

@cython.boundscheck(False)
@cython.wraparound(False)
def decode_cis(cnp.ndarray[cnp.uint16_t, ndim=1] data, cnp.ndarray[cnp.uint8_t, ndim=3] out_img, int vert_px, int hol_px, bint bicolor):

    # CIS file format
    # http://semitone440.co.uk/rolls/utils/cisheader/cis-format.htm#scantype

    cdef:
        cnp.uint8_t bg_color = 255
        cnp.uint8_t black_color = 0
        int cur_idx = 0
        int last_pos = 0
        CurColor cur_pix = ROLL
        int change_len = 0
        int i = 0
        int cur_line = 0

    for cur_line in range(vert_px - 1, 0, -1):
        # decode holes
        last_pos = 0
        cur_pix = ROLL
        while True:
            change_len = data[cur_idx]
            if cur_pix == BG:
                for i in range(change_len):
                    out_img[cur_line, last_pos + i, 0] = bg_color
                    out_img[cur_line, last_pos + i, 1] = bg_color
                    out_img[cur_line, last_pos + i, 2] = bg_color
                cur_pix = ROLL
            elif cur_pix == ROLL:
                cur_pix = BG

            cur_idx += 1
            last_pos += change_len
            if last_pos == hol_px:
                if not bicolor:
                    cur_idx += 1
                break

        # decode lyrics
        last_pos = 0
        cur_pix = MARK
        if bicolor:
            while True:
                change_len = data[cur_idx]
                cur_idx += 1
                if last_pos == hol_px:
                    break

                if cur_pix == MARK:
                    for i in range(change_len):
                        out_img[cur_line, last_pos + i, 0] = black_color
                        out_img[cur_line, last_pos + i, 1] = black_color
                        out_img[cur_line, last_pos + i, 2] = black_color
                    cur_pix = BG
                elif cur_pix == BG:
                    cur_pix = MARK

                last_pos += change_len