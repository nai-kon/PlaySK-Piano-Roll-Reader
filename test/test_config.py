from src.config import ConfigMng


def test_load_config(monkeypatch):
    exists_path = "test/dummy_config/config.json"
    monkeypatch.setattr(ConfigMng, "_path", exists_path)
    mngr = ConfigMng()
    assert mngr.last_midi_port == "loopMIDI Port 1"
    assert mngr.last_tracker == "Duo-Art white back"
    assert mngr.update_notified_version == "3.1"

    empty_json_path = "test/dummy_config/empty_config.json"
    monkeypatch.setattr(ConfigMng, "_path", empty_json_path)
    mngr = ConfigMng()
    assert mngr.last_midi_port == ""
    assert mngr.last_tracker == ""
    assert mngr.update_notified_version == ""

    not_exists_path = "notexists.json"
    monkeypatch.setattr(ConfigMng, "_path", not_exists_path)
    mngr = ConfigMng()
    assert mngr.last_midi_port == ""
    assert mngr.last_tracker == ""
    assert mngr.update_notified_version == ""


def test_save_config(monkeypatch):
    exists_path = "test/dummy_config/config2.json"
    monkeypatch.setattr(ConfigMng, "_path", exists_path)
    mngr = ConfigMng()
    mngr.last_midi_port = 1
    mngr.last_tracker = 2
    mngr.update_notified_version = 3
    mngr.save_config()

    mngr = ConfigMng()
    assert mngr.last_midi_port == 1
    assert mngr.last_tracker == 2
    assert mngr.update_notified_version == 3
