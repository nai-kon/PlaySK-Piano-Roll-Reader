import os
import platform
import socket
import sys
import threading

import wx


class SingleInstWin:
    """
    Check app is single instance on Windows.
    If already exists, send command line arg path(sys.argv[1]) to exist app then close myself.
    If not exists, run socket sever to receive file path from later launch app.
    """

    def __init__(self) -> None:
        self.app_frame: wx.Frame = None
        self.message_notify = "PlaySK_msg_notify:"
        self.message_path = "PlaySK_msg_path:"
        self.port = 58583

    def file_path_receiver(self) -> None:
        # receive file path from later launched instance
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("localhost", self.port))
            sock.listen(1)
            while True:
                conn, _ = sock.accept()
                msg = conn.recv(1024).decode()
                if self.app_frame is not None:
                    if msg.startswith(self.message_path):
                        path = msg.replace(self.message_path, "", 1)
                        wx.CallAfter(self.app_frame.load_file, path=path)
                        wx.CallAfter(self.app_frame.Raise)
                    elif msg.startswith(self.message_notify):
                        wx.CallAfter(self.app_frame.Raise)

    def is_exists(self) -> bool:
        try:
            with socket.create_connection(("localhost", self.port), timeout=0.01) as sock:
                if len(sys.argv) > 1:
                    sock.sendall(f"{self.message_path}{sys.argv[1]}".encode())
                else:
                    sock.sendall(self.message_notify.encode())
            print("app is already exists.")
            return True
        except OSError:
            # app is not exists. run socket server as a daemon
            th = threading.Thread(target=self.file_path_receiver, daemon=True)
            th.start()
            return False


class AppMain(wx.App):
    """
    For open file with associated program on Mac.
    """
    def __init__(self):
        super().__init__()

    def MacOpenFile(self, path):
        # open on default app event
        if self.GetTopWindow() is None:
            # app frame is not created yet, so add to sys.argv and load it on MainFrame.init()
            sys.argv.append(path)
        else:
            wx.CallAfter(self.GetTopWindow().load_file, path=path)


if __name__ == "__main__":
    pf = platform.system()
    if pf == "Windows":
        single_inst = SingleInstWin()
        if single_inst.is_exists():
            sys.exit(0)  # close app
        from ctypes import windll
        windll.winmm.timeBeginPeriod(1)
        windll.shcore.SetProcessDpiAwareness(True)
        # drop file to .exe changes current dir and causes errors, so fix current dir
        os.chdir(os.path.dirname(sys.argv[0]))

    app = AppMain()
    from midi_controller import MidiWrap
    if not MidiWrap().port_list:
        wx.MessageBox("No any midi out port found. Exit software.", "Midi port error")
        exit(-1)

    if not os.path.exists("playsk_config/"):
        wx.MessageBox("config directory is not found. Exit software.", "Config error")
        exit(-1)

    from main_frame import MainFrame
    frame = MainFrame()
    if pf == "Windows":
        single_inst.app_frame = frame
    app.MainLoop()
    print("main loop end")

    if pf == "Windows":
        from ctypes import windll
        windll.winmm.timeEndPeriod(1)
