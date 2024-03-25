from src.config import ConfigMng


def test_load_config(mocker):
    exists_path = "test/dummy_config/config.json"
    mocker.patch("src.config.CONFIG_PATH", new=exists_path)
    mngr = ConfigMng()
    assert mngr.last_midi_port == "loopMIDI Port 1"
    assert mngr.last_tracker == "Duo-Art white back"
    assert mngr.update_notified_version == "3.1"
    assert mngr.window_scale == "125%"

    empty_json_path = "test/dummy_config/empty_config.json"
    mocker.patch("src.config.CONFIG_PATH", new=empty_json_path)
    mngr = ConfigMng()
    assert mngr.last_midi_port == ""
    assert mngr.last_tracker == ""
    assert mngr.update_notified_version == ""
    assert mngr.window_scale == "100%"

    not_exists_path = "notexists.json"
    mocker.patch("src.config.CONFIG_PATH", new=not_exists_path)
    mngr = ConfigMng()
    assert mngr.last_midi_port == ""
    assert mngr.last_tracker == ""
    assert mngr.update_notified_version == ""
    assert mngr.window_scale == "100%"


def test_save_config(mocker):
    exists_path = "test/dummy_config/config2.json"
    mocker.patch("src.config.CONFIG_PATH", new=exists_path)
    mngr = ConfigMng()
    mngr.last_midi_port = "Japanese日本語"
    mngr.last_tracker = "2"
    mngr.update_notified_version = "3"
    mngr.window_scale = "150%"
    mngr.save_config()

    mngr = ConfigMng()
    assert mngr.last_midi_port == "Japanese日本語"
    assert mngr.last_tracker == "2"
    assert mngr.update_notified_version == "3"
    assert mngr.window_scale == "150%"

    mngr = ConfigMng()
    mngr.last_midi_port = "hogehoge"
    mngr.last_tracker = "fugafuga"
    mngr.update_notified_version = "4"
    mngr.window_scale = "125%"
    mngr.save_config()