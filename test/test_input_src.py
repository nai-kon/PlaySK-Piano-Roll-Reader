import pytest

from src.input_src import _find_roll_edge, _load_img


@pytest.mark.parametrize("img_path, expect", [
    # expect is (Image is not None, tempo)
    ("notexists.jpg", (False, 80)),
    ("Welte Licensee 7005 Etude Japonaise tempo90.jpg", (True, 90)),
    ("Welte Licensee 7005 Etude Japonaise with ann.png", (True, 90)),
    ("Welte Licensee 7005 Etude Japonaise.tif", (True, 80)),
])
def test_load_img(img_path, expect):
    img, tempo = _load_img("test/test_images/" + img_path, 80)
    assert (img is not None) == expect[0]
    assert tempo == expect[1]


@pytest.mark.parametrize("img_path, expect", [
    # expect is (left_edge, right_edge)
    ("find_edge_test.png", (64, 1761)),
    ("find_edge_test_with_noise_line.png", (64, 1761)),
    ("find_edge_test_no_padding.png", (None, None)),
    ("find_edge_test_too_little_padding.png", (None, None)),
])
def test_find_roll_edge(img_path, expect):
    img, _ = _load_img("test/test_images/" + img_path, 80)
    left, right = _find_roll_edge(img)
    assert (left, right) == expect
