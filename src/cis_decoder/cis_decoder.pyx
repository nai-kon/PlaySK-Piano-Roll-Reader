# cython: language_level=3

cimport cython
cimport numpy as cnp

cdef enum CurColor:
    NONE = 0
    BG = 1
    ROLL = 2
    MARK = 3

@cython.boundscheck(False)
@cython.wraparound(False)
def decode_cis(cnp.ndarray[cnp.uint16_t, ndim=1] data, cnp.ndarray[cnp.uint8_t, ndim=3] out_img, int vert_px, int hol_px, bint bicolor):

    # decode CIS
    cdef:
        cnp.uint8_t bg_color = 255
        cnp.uint8_t black_color = 0
        int cur_idx = 0
        int last_pos = 0
        int none_end_pos = 0
        CurColor cur_pix = NONE
        int change_len = 0
        int i = 0
        int cur_line = 0
    for cur_line in range(vert_px - 1, 0, -1):
        # decode holes
        last_pos = 0
        none_end_pos = 0
        cur_pix = NONE
        while True:
            change_len = data[cur_idx]
            if cur_pix == NONE:
                for i in range(change_len):
                    out_img[cur_line, last_pos + i, 0] = black_color
                    out_img[cur_line, last_pos + i, 1] = black_color
                    out_img[cur_line, last_pos + i, 2] = black_color
                cur_pix = BG
                none_end_pos = change_len
            elif cur_pix == BG:
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
                cur_idx += 1
                break

        # decode lyrics
        last_pos = none_end_pos
        cur_pix = BG
        while bicolor:
            change_len = data[cur_idx]
            cur_idx += 1
            if change_len == 0:
                break

            if cur_pix == MARK:
                change_len = change_len if last_pos + change_len < hol_px else hol_px - last_pos
                for i in range(change_len):
                    out_img[cur_line, last_pos + i, 0] = black_color
                    out_img[cur_line, last_pos + i, 1] = black_color
                    out_img[cur_line, last_pos + i, 2] = black_color
            cur_pix = MARK if cur_pix == BG else BG
            last_pos += change_len