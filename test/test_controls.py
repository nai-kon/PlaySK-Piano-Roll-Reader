import re
import sys
import time

sys.path.append("src/")
from config import ConfigMng
from controls import NotifyDialog, NotifyUpdate


class TestNotifyUpdate:
    def test_fetch_latest_version(self):
        conf = ConfigMng()
        obj = NotifyUpdate(None, conf)

        # return "X.Y"
        ver = obj.fetch_latest_version()
        assert re.match(r"\d\.\d", ver) is not None

        # return None
        obj.url = "https://NOTEXISTS.gov"
        start = time.time()
        ver = obj.fetch_latest_version()
        end = time.time()
        assert end - start < 10 + 1
        assert ver is None

    def test_need_notify(self, mocker):
        conf = ConfigMng()
        obj = NotifyUpdate(None, conf)

        conf.update_notified_version = "3.0"
        mocker.patch("controls.APP_VERSION", new="3.0")
        # not notify
        assert not obj.need_notify("3.0")
        assert not obj.need_notify(None)
        # notify
        assert obj.need_notify("3.1")
        # already notified this version. skip
        conf.update_notified_version = "3.1"
        assert not obj.need_notify("3.1")
        # more new version is coming. notify
        assert obj.need_notify("3.2")

    def test_notify(self, mocker):
        conf = ConfigMng()
        conf.update_notified_version = "3.0"
        wxcallafter_mock = mocker.patch("wx.CallAfter")
        obj = NotifyUpdate(None, conf)
        obj.notify("3.1")
        # version in conf is updated
        assert conf.update_notified_version == "3.1"
        # call notify dlg with desired param
        wxcallafter_mock.assert_called_once_with(NotifyDialog, None, "3.1")

    def test_check(self, mocker, monkeypatch):
        # integration testing
        conf = ConfigMng()
        conf.update_notified_version = "3.0"
        mocker.patch("controls.APP_VERSION", new="3.0")
        wxcallafter_mock = mocker.patch("wx.CallAfter")
        monkeypatch.setattr(NotifyUpdate, "fetch_latest_version", lambda self: "3.0")

        # not notify
        start = time.time()
        th = NotifyUpdate.check(None, conf)
        end = time.time()
        th.join()
        assert end - start < 0.5  # return immediately
        wxcallafter_mock.assert_not_called()

        # notify
        monkeypatch.setattr(NotifyUpdate, "fetch_latest_version", lambda self: "3.1")
        start = time.time()
        th = NotifyUpdate.check(None, conf)
        end = time.time()
        th.join()
        assert end - start < 0.5  # return immediately
        wxcallafter_mock.assert_called_once_with(NotifyDialog, None, "3.1")
