import sys

import cv2
import numpy as np
import pytest

sys.path.append("src/")
from cis_decoder.cis_decoder import _get_decode_params
from cis_image import CisImage, ScannerType


@pytest.mark.parametrize("cis_path, expect", [
    # expect is (tempo, scanner_type, hol_dpi, hol_px, vert_res, vert_px, is_clocked, is_twin_array, is_bicolor, encoder_division, vert_sep_twin, overlap_twin, lpt)
    ("clocked_single.CIS", (90, ScannerType.WHEELENCODER, 300, 3648, 309, 34128, True, False, False, 16, 0, 0, 10)),
    ("stepper_single.CIS", (90, ScannerType.STEPPER, 200, 2432, 180, 59425, False, False, False, 1, 0, 0, 0)),
    ("stepper_bicolor.CIS", (90, ScannerType.STEPPER, 300, 3648, 300, 116858, False, False, True, 1, 0, 0, 0)),
    ("stepper_twin.CIS", (90, ScannerType.STEPPER, 300, 2600, 204, 63661, False, True, False, 1, 490, 244, 0)),
    ("unknown_scanner.CIS", (70, ScannerType.UNKNOWN, 200, 2432, 180, 187151, False, False, False, 1, 0, 0, 0)),
])
def test_load_file(cis_path, expect):
    obj = CisImage()
    obj._load_file("test/cis_test_scans/" + cis_path)
    res = (obj.tempo, obj.scanner_type, obj.hol_dpi, obj.hol_px, obj.vert_res, obj.vert_px, obj.is_clocked,
           obj.is_twin_array, obj.is_bicolor, obj.encoder_division, obj.vert_sep_twin, obj.overlap_twin, obj.lpt)
    assert res == expect


@pytest.mark.parametrize("cis_path, expect", [
    # expect is (decoded_width, decoded_height)
    ("clocked_single.CIS", (3648, 89790)),
    ("stepper_single.CIS", (2432, 59425)),
    ("stepper_bicolor.CIS", (3648, 116858)),
    ("stepper_twin.CIS", (4956, 63661)),
    ("unknown_scanner.CIS", (2432, 187151)),
])
def test_get_decoded_params(cis_path, expect):
    # python version
    obj = CisImage()
    obj._load_file("test/cis_test_scans/" + cis_path)
    # reclock map will be checked in output image comparesion test
    width, height, _ = obj._get_decode_params_py(obj.raw_img)
    assert (width, height) == expect

    # cython version
    obj = CisImage()
    obj._load_file("test/cis_test_scans/" + cis_path)
    # reclock map will be checked in output image comparesion test
    width, height, _ = _get_decode_params(obj.raw_img, obj.vert_px, obj.hol_px, obj.overlap_twin, obj.lpt, obj.is_bicolor, obj.is_twin_array, obj.is_clocked)
    assert (width, height) == expect


@pytest.mark.parametrize("cis_path, gt_path", [
    # expect is (decoded_width, decoded_height)
    ("clocked_single.CIS", "clocked_single_gt.png"),
    ("stepper_single.CIS", "stepper_single_gt.png"),
    ("stepper_bicolor.CIS", "stepper_bicolor_gt.png"),
    ("stepper_twin.CIS", "stepper_twin_gt.png"),
    ("unknown_scanner.CIS", "unknown_scanner_gt.png"),
])
def test_decode_cis(cis_path, gt_path):
    # check pixel values are same to gt
    gt_img = cv2.imread("test/cis_test_scans/" + gt_path)
    obj = CisImage()
    obj._load_file("test/cis_test_scans/" + cis_path)
    obj._decode()

    assert np.array_equal(obj.decode_img, gt_img)


def test_decode_error_cis():
    obj = CisImage()
    obj._load_file("test/cis_test_scans/broken_data.CIS")
    with pytest.raises(BufferError):
        obj._decode()

    obj = CisImage()
    obj._load_file("test/cis_test_scans/no_encoder_signal.CIS")
    with pytest.raises(ValueError) as e:
        obj._decode()
    assert str(e.value) == "No encoder clock signal found"
