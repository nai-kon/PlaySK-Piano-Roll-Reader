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
        self.start = None
        self.fps = 0

    def __call__(self):
        cur = time.perf_counter()
        if self.start is None:
            self.start = cur
        self.fps += 1
        if cur - self.start > 1:
            print(self.name, self.fps)
            self.fps = 0
            self.start = cur


class InputVideo(wx.Panel):
    def __init__(self, parent, path, disp_size=(800, 600), callback=None):
        wx.Panel.__init__(self, parent, size=parent.FromDIP(wx.Size(disp_size)))
        self.SetDoubleBuffered(True)
        self.disp_w, self.disp_h = disp_size
        self.bmp = wx.Bitmap(self.disp_w, self.disp_h, depth=24)
        self.callback = callback
        self.src = None
        self.src_path = path
        self.scale = self.GetDPIScaleFactor()

        self.start_play = False
        self.worker_thread_quit = False
        self.thread_worker = threading.Thread(target=self.load_thread)
        self.worker_fps = 60
        self.cnt_worker_fps = FPScounter("worker fps")
        self.thread_lock = threading.Lock()

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.on_destroy)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_start)

    def start_worker(self):
        self.src = cv2.VideoCapture(self.src_path)
        self._load_next_frame()
        self.thread_worker.start()

    def release_src(self):
        self.worker_thread_quit = True
        self.thread_worker.join(timeout=3)
        if self.src is not None:
            self.src = None
            gc.collect()

    def on_destroy(self, event):
        self.worker_thread_quit = True
        self.thread_worker.join(timeout=3)
        wx.GetApp().Yield(onlyIfNeeded=True)

    def on_paint(self, event):
        # no need for BufferedPaintDC since SetDoubleBuffered(True)
        dc = wx.PaintDC(self)
        dc.SetUserScale(self.scale, self.scale)

        with self.thread_lock:
            dc.DrawBitmap(self.bmp, 0, 0)

        # draw play button
        if not self.start_play:
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
        self.start_play = not self.start_play
        event.Skip()

    def _load_next_frame(self):
        ret, frame = self.src.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            src_h, src_w = frame.shape[:2]
            new_w = self.disp_w
            new_h = src_h * new_w // src_w
            resized = cv2.resize(frame, dsize=(new_w, new_h), interpolation=cv2.INTER_NEAREST)
            vert_margin = self.disp_h - new_h
            self.frame = cv2.copyMakeBorder(resized, top=math.floor(vert_margin / 2), bottom=math.ceil(vert_margin / 2), left=0, right=0, borderType=cv2.BORDER_CONSTANT)

    def _get_one_frame_time(self):
        return 1 / self.worker_fps

    def load_thread(self):
        while not self.worker_thread_quit:
            t1 = time.perf_counter()

            if self.start_play:
                self._load_next_frame()

            if self.callback is not None:
                self.callback.emulate(self.frame, time.perf_counter())

            if not self.thread_lock.locked():
                with self.thread_lock:
                    self.bmp.CopyFromBuffer(self.frame)

                wx.CallAfter(self.Refresh, eraseBackground=False)  # refresh from thread need call after

            # wait for next frame
            desired_time = self._get_one_frame_time()
            elapsed_time = time.perf_counter() - t1
            if desired_time - elapsed_time < 0:
                print(f"コマ落ち中...{(desired_time - elapsed_time)*1000:.2f} msec")
            while desired_time > elapsed_time:
                sleep = 0.001 if desired_time - elapsed_time > 0.0015 else 0
                time.sleep(sleep)
                elapsed_time = time.perf_counter() - t1

            self.cnt_worker_fps()
        print("end thread")


class InputWebcam(InputVideo):
    def __init__(self, parent, webcam_no=0, disp_size=(800, 600), callback=None):
        super().__init__(parent, webcam_no, disp_size, callback)
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
    def __init__(self, parent, path, spool_diameter=2.72, roll_width=11.25, tempo=80, disp_size=(800, 600), callback=None):
        super().__init__(parent, path, disp_size, callback)
        self.skip_px = 1
        self.spool_rps = 0
        self.cur_spool_diameter = self.org_spool_diameter = spool_diameter
        self.cur_spool_pos = 0
        self.roll_thick = 0.00334646  # in inch
        self.roll_width = roll_width
        self.tempo = tempo

    def start_worker(self):
        with wx.BusyCursor():
            self.src = cv2.imread(self.src_path)
            self.src = cv2.cvtColor(self.src, cv2.COLOR_BGR2RGB)
        # load initial frame
        self.cur_y = self.src.shape[0] - 1
        self.left_side, self.right_side = self.__find_roll_edge()
        margin = 7 * (self.right_side - self.left_side + 1) // (self.disp_w - 7 * 2)  # 7px on both edge @800x600
        self.crop_x1 = self.left_side - margin
        self.crop_x2 = self.right_side + margin
        self.crop_h = (self.crop_x2 - self.crop_x1) * self.disp_h // self.disp_w
        self.roll_dpi = (self.right_side - self.left_side + 1) / self.roll_width
        self.set_tempo(self.tempo)
        self._load_next_frame()
        self.thread_worker.start()

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
        roll_h, roll_w = self.src.shape[:2]
        edges = []
        edge_th = 220
        for y in np.linspace(0, roll_h - 1, 20, dtype=int):
            # find left edge
            left_side = 0
            for x in range(0, roll_w // 2):
                if self.src[y, x][0] < edge_th:
                    left_side = x
                    break

            # find right edge
            right_side = roll_w - 1
            for x in range(roll_w - 1, roll_w // 2, -1):
                if self.src[y, x][0] < edge_th:
                    right_side = x
                    break

            edges.append((left_side, right_side))

        #  sort by width, and get a middle point
        edges.sort(key=lambda x: x[1] - x[0])
        middle = len(edges) // 2
        return edges[middle]

    def _load_next_frame(self):
        crop_y2 = self.cur_y
        crop_y1 = crop_y2 - self.crop_h
        if crop_y1 < 0:
            return

        frame = self.src[crop_y1:crop_y2 + 1, self.crop_x1:self.crop_x2 + 1]
        self.frame = cv2.resize(frame, (self.disp_w, self.disp_h), interpolation=cv2.INTER_NEAREST)
        self.cur_y -= self.skip_px

        # update take-up spool round
        spool_rpf = self.spool_rps / self.worker_fps
        self.cur_spool_pos += spool_rpf

    def _get_one_frame_time(self):

        # spool diameter will increase per 1 round. this causes acceleration.
        if self.cur_spool_pos > 1:
            self.cur_spool_pos -= 1  # don't reset to 0.
            self.cur_spool_diameter += self.roll_thick

        # take-up pixels per one second
        takeup_px = self.spool_rps * self.cur_spool_diameter * math.pi * self.roll_dpi

        # how many fps needed for take up
        self.worker_fps = takeup_px / self.skip_px

        return 1 / self.worker_fps


if __name__ == "__main__":
    from midi_controller import MidiWrap

    app = wx.App()
    frame = wx.Frame(None, wx.ID_ANY, "テストフレーム", size=(1280, 720))

    midobj = MidiWrap()
    midobj.open_port(None)

    # panel1 = InputVideo(frame, path="C:\\Users\\SASAKI\\Desktop\\AGDRec_20201217_200957.mp4", callback=obj.call_back)
    panel1 = InputScanImg(frame, path="C:\\Users\\SASAKI\\source\\repos\\nai-kon\\cis-roll-converter\\output\\Popular Hits of the Day 71383A_tempo75.png")
    panel1.start_worker()
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
