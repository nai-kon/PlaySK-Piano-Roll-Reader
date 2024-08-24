import sys

import cv2
import numpy as np
import pytest

sys.path.append("src/")
from cis_decoder.cis_decoder import _get_decode_params
from cis_image import CisImage, ScannerType


class TestCisImage:
    @pytest.mark.parametrize("cis_path, expect", [
        # expect is (tempo, scanner_type, hol_dpi, hol_px, vert_res, vert_px, is_clocked, is_twin_array, is_bicolor, encoder_division, vert_sep_twin, overlap_twin, lpt)
        ("clocked_single.CIS", (90, ScannerType.WHEELENCODER, 300, 3648, 309, 34128, True, False, False, 16, 0, 0, 10)),
        ("stepper_single.CIS", (90, ScannerType.STEPPER, 200, 2432, 180, 59425, False, False, False, 1, 0, 0, 0)),
        ("stepper_bicolor.CIS", (90, ScannerType.STEPPER, 300, 3648, 300, 116858, False, False, True, 1, 0, 0, 0)),
        ("stepper_twin.CIS", (90, ScannerType.STEPPER, 300, 2600, 204, 63661, False, True, False, 1, 490, 244, 0)),
        ("unknown_scanner.CIS", (70, ScannerType.UNKNOWN, 200, 2432, 180, 187151, False, False, False, 1, 0, 0, 0)),
    ])
    def test_load_file(self, cis_path, expect):
        obj = CisImage()
        obj._load_file("test/test_images/" + cis_path)
        res = (obj.tempo, obj.scanner_type, obj.hol_dpi, obj.hol_px, obj.vert_res, obj.vert_px, obj.is_clocked,
               obj.is_twin_array, obj.is_bicolor, obj.encoder_division, obj.twin_array_vert_sep, obj.twin_array_overlap, obj.lpt)
        assert res == expect

    @pytest.mark.parametrize("cis_path, expect", [
        # expect is (decoded_width, decoded_height)
        ("clocked_single.CIS", (3648, 89790)),
        ("stepper_single.CIS", (2432, 59425)),
        ("stepper_bicolor.CIS", (3648, 116858)),
        ("stepper_twin.CIS", (4956, 63661)),
        ("unknown_scanner.CIS", (2432, 187151)),
    ])
    def test_get_decoded_params(self, cis_path, expect):
        # python version
        obj = CisImage()
        obj._load_file("test/test_images/" + cis_path)
        # reclock map will be checked in output image comparesion test
        width, height, _ = obj._get_decode_params_py()
        assert (width, height) == expect

        # cython version
        obj = CisImage()
        obj._load_file("test/test_images/" + cis_path)
        # reclock map will be checked in output image comparesion test
        width, height, _ = _get_decode_params(obj.raw_img, obj.vert_px, obj.hol_px, obj.lpt, obj.is_bicolor, obj.is_twin_array, obj.is_clocked, obj.twin_array_overlap)
        assert (width, height) == expect

    @pytest.mark.parametrize("cis_path, gt_path", [
        ("clocked_single.CIS", "clocked_single_gt.png"),
        ("stepper_single.CIS", "stepper_single_gt.png"),
        ("stepper_bicolor.CIS", "stepper_bicolor_gt.png"),
        ("stepper_twin.CIS", "stepper_twin_gt.png"),
        ("unknown_scanner.CIS", "unknown_scanner_gt.png"),
    ])
    def test_decode_cis(self, cis_path, gt_path):
        # check pixel values are same to gt
        for use_cython in (True, False):
            gt_img = cv2.imread("test/test_images/" + gt_path)
            obj = CisImage()
            obj._load_file("test/test_images/" + cis_path)
            obj._decode(use_cython)
            assert np.array_equal(obj.decoded_img, gt_img)

    def test_decode_error_cis(self):
        for use_cython in (True, False):
            obj = CisImage()
            obj._load_file("test/test_images/broken_data.CIS")
            with pytest.raises(BufferError):
                obj._decode(use_cython)

            obj = CisImage()
            obj._load_file("test/test_images/no_encoder_signal.CIS")
            with pytest.raises(ValueError) as e:
                obj._decode(use_cython)
            assert str(e.value) == "No encoder clock signal found"

    def test_load(self, mocker):
        # load success test
        obj = CisImage()
        ret = obj.load("test/test_images/clocked_single.CIS")
        assert ret

        # load fail test
        obj = CisImage()
        wxmsg_mocker = mocker.patch("wx.MessageBox")
        ret = obj.load("test/test_images/broken_data.CIS")
        assert not ret
        wxmsg_mocker.assert_called_once()

    def test_convert_bw(self):
        obj = CisImage()

        # nothing happens
        obj.convert_bw()

        # convert black pixel to white
        obj.decoded_img = np.zeros((100, 100, 3), dtype=np.uint8)
        obj.convert_bw()
        assert (obj.decoded_img == 255).all()
