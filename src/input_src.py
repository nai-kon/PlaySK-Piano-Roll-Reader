import cv2
import time
import threading
import wx
import math
import numpy as np
import gc


class FPScounter():
    def __init__(self, name="fps"):
        self.name = name
        self.start = time.perf_counter()
        self.fps = 0

    def __call__(self):
        cur = time.perf_counter()
        self.fps += 1
        if cur - self.start > 1:
            print(self.name, self.fps)
            self.fps = 0
            self.start = cur


class InputVideo(wx.Panel):
    def __init__(self, parent, path, disp_size=(800, 600), fn=None):
        self.scale = wx.Display().GetScaleFactor()
        wx.Panel.__init__(self, parent, size=(disp_size[0] * self.scale, disp_size[1] * self.scale))
        self.SetDoubleBuffered(True)
        self.disp_w, self.disp_h = disp_size
        self.bmp = wx.Bitmap(self.disp_w, self.disp_h, depth=24)
        self.fn = fn
        self.cap = cv2.VideoCapture(path)
        self._load_next_frame()
        self.load_fps = 60
        self.last_disp = 0
        self.thread_fps = FPScounter("thread fps")
        self.disp_fps = FPScounter("disp fps")
        self.thlock = threading.Lock()

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.on_destroy)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_start)

        self.start = False
        self.thread_quit = False
        self.th1 = threading.Thread(target=self.load_thread)
        self.th1.start()

    def release_src(self):
        self.thread_quit = True
        self.th1.join(timeout=3)
        if self.cap is not None:
            self.cap = None
            gc.collect()

    def on_destroy(self, event):
        self.thread_quit = True
        self.th1.join(timeout=3)
        wx.GetApp().Yield(onlyIfNeeded=True)

    def on_paint(self, event):
        dc = wx.BufferedPaintDC(self)
        with self.thlock:
            dc.DrawBitmap(self.bmp, 0, 0)

        # draw play button
        if not self.start:
            self.draw_play_button(dc)

    def draw_play_button(self, dc):
        dc = wx.GCDC(dc)  # for anti-aliasing

        # draw circle
        dc.SetBrush(wx.Brush("#888888"))
        dc.SetPen(wx.Pen("#888888"))
        center_x, center_y = self.disp_w // 2, self.disp_h // 2
        rad = self.disp_h // 14
        dc.DrawCircle(center_x, center_y, rad)

        # draw triangle
        dc.SetBrush(wx.Brush("white"))
        dc.SetPen(wx.Pen("white"))
        rad = self.disp_h // 20
        dc.DrawPolygon([(center_x - rad // 2, center_y - math.sqrt(3) * rad // 2),
                        (center_x - rad // 2, center_y + math.sqrt(3) * rad // 2),
                        (center_x + rad, center_y)])

    def on_start(self, event):
        self.start = not self.start
        event.Skip()

    def _load_next_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            src_h, src_w = frame.shape[:2]
            new_w = self.disp_w
            new_h = int(src_h * (new_w / src_w))
            resized = cv2.resize(frame, dsize=(new_w, new_h), interpolation=cv2.INTER_NEAREST)
            vert_margin = self.disp_h - new_h
            self.frame = cv2.copyMakeBorder(resized, top=math.floor(vert_margin / 2), bottom=math.ceil(vert_margin / 2), left=0, right=0, borderType=cv2.BORDER_CONSTANT)

    def _get_one_frame_time(self):
        return 1 / self.load_fps

    def load_thread(self):
        while not self.thread_quit:
            t1 = time.perf_counter()

            if self.start:
                self._load_next_frame()

            if self.fn is not None:
                self.fn(self.frame, time.perf_counter())

            if not self.thlock.locked():
                with self.thlock:
                    self.bmp.CopyFromBuffer(self.frame)

                wx.CallAfter(self.Refresh)  # refresh from thread need call after

            # wait for next frame
            desired_time = self._get_one_frame_time()
            elapsed_time = time.perf_counter() - t1
            if desired_time - elapsed_time < 0:
                print(f"コマ落ち中...{(desired_time - elapsed_time)*1000:.2f} msec")
            while desired_time > elapsed_time:
                sleep = 0.001 if desired_time - elapsed_time > 0.0015 else 0
                time.sleep(sleep)
                elapsed_time = time.perf_counter() - t1

            self.thread_fps()
        print("end thread")


class InputWebcam(InputVideo):
    def __init__(self, parent, webcam_no=0, disp_size=(800, 600), fn=None):
        super().__init__(parent, webcam_no, disp_size, fn)
        self.start = True

    @staticmethod
    def list_camera():
        camera_list = []
        for i in range(10):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                camera_list.append(i)
            cap.release()

        return camera_list


class InputScanImg(InputVideo):
    def __init__(self, parent, path, spool_diameter=2.72, tempo=80, disp_size=(800, 600), fn=None):
        self.scale = wx.Display().GetScaleFactor()
        wx.Panel.__init__(self, parent, size=(disp_size[0] * self.scale, disp_size[1] * self.scale))
        self.SetDoubleBuffered(True)
        self.disp_w, self.disp_h = disp_size
        self.disp_ratio = self.disp_h / self.disp_w
        self.bmp = wx.Bitmap(self.disp_w, self.disp_h, depth=24)
        self.fn = fn
        self.skip_px = 1
        self.spool_rps = 0
        self.cur_spool_diameter = self.org_spool_diameter = spool_diameter
        self.cur_spool_pos = 0
        self.cur_fps = 60
        self.last_disp = 0
        cursor = wx.BusyCursor()
        self.cap = cv2.imread(path)
        self.cap = cv2.cvtColor(self.cap, cv2.COLOR_BGR2RGB)
        del cursor
        self.cur_y = self.cap.shape[0] - 1
        self.left_side, self.right_side = self.__find_roll_edge()
        self.roll_dpi = (self.right_side - self.left_side + 1) / 11.25  # standard roll width is 11.25inch
        self.margin = int(7 * (self.right_side - self.left_side + 1) / (self.disp_w - 7 * 2))  # 7px on both edge @800x600
        self.crop_x1 = self.left_side - self.margin
        self.crop_x2 = self.right_side + self.margin
        self.crop_w = self.crop_x2 - self.crop_x1

        self.roll_thick = 0.00334646  # in inch
        self._load_next_frame()
        self.set_tempo(tempo)
        self.thlock = threading.Lock()

        self.thread_fps = FPScounter("thread fps")
        self.disp_fps = FPScounter("disp fps")
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.on_destroy)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_start)

        self.start = False
        self.thread_quit = False
        self.th1 = threading.Thread(target=self.load_thread)
        self.th1.start()

    def set_tempo(self, tempo):
        # calc take-up spool rps
        self.spool_rps = (tempo * 1.2) / (self.org_spool_diameter * math.pi * 60)

        # calc skip px
        px_per_sec = (tempo * 1.2 * self.roll_dpi) / 60
        for i in range(1, 10):
            # calc skip pixels to be less than 200fps
            if (px_per_sec / i) < 200:
                self.skip_px = i
                break

    def __find_roll_edge(self):
        roll_h, roll_w = self.cap.shape[:2]
        edges = []
        edge_th = 220
        for y in np.linspace(0, roll_h - 1, 20, dtype=int):
            # find left edge
            left_side = 0
            for x in range(0, roll_w // 2):
                if self.cap[y, x][0] < edge_th:
                    left_side = x
                    break

            # find right edge
            right_side = roll_w - 1
            for x in range(roll_w - 1, roll_w // 2, -1):
                if self.cap[y, x][0] < edge_th:
                    right_side = x
                    break

            edges.append((left_side, right_side))

        #  sort by width, and get a middle point
        middle = len(edges) // 2
        edges.sort(key=lambda x: x[1] - x[0])
        return edges[middle]

    def _load_next_frame(self):
        cropy2 = self.cur_y
        cropy1 = cropy2 - int(self.crop_w * self.disp_ratio)
        if cropy1 < 0:
            return

        frame = self.cap[cropy1:cropy2 + 1, self.crop_x1:self.crop_x2 + 1]
        self.frame = cv2.resize(frame, (self.disp_w, self.disp_h), interpolation=cv2.INTER_NEAREST)
        self.cur_y -= self.skip_px

        # update take-up spool round
        spool_rpf = self.spool_rps / self.cur_fps
        self.cur_spool_pos += spool_rpf

    def _get_one_frame_time(self):

        # spool diameter will increase per 1 round. this causes acceleration.
        if self.cur_spool_pos > 1:
            self.cur_spool_pos -= 1  # don't reset to 0.
            self.cur_spool_diameter += self.roll_thick

        # take-up pixels per one second
        takeup_px = self.spool_rps * self.cur_spool_diameter * math.pi * self.roll_dpi

        # how many fps needed for take up
        self.cur_fps = takeup_px / self.skip_px

        return 1 / self.cur_fps


if __name__ == "__main__":
    from midi_controller import MidiWrap

    app = wx.App()
    frame = wx.Frame(None, wx.ID_ANY, 'テストフレーム', size=(1280, 720))

    midobj = MidiWrap()
    midobj.open_port(None)

    # panel1 = InputVideo(frame, path="C:\\Users\\SASAKI\\Desktop\\AGDRec_20201217_200957.mp4", fn=obj.call_back)
    panel1 = InputScanImg(frame, path="C:\\Users\\SASAKI\\source\\repos\\nai-kon\\cis-roll-converter\\output\\Popular Hits of the Day 71383A_tempo75.png")

    # print(InputWebcam.list_camera())
    # panel1 = InputWebcam(frame, webcam_no=0)

    def slider_value_change(event):
        obj = event.GetEventObject()
        panel1.set_tempo(obj.GetValue())
    slider = wx.Slider(frame, value=80, minValue=10, maxValue=140, pos=(0, 600), size=(200, 100), style=wx.SL_HORIZONTAL | wx.SL_LABELS)
    slider.SetPageSize(5)
    slider.Bind(wx.EVT_SLIDER, slider_value_change)

    frame.Show()
    app.MainLoop()
