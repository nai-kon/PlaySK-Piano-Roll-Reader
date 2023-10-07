import math
import os
import platform
import re
import threading
import time
import numpy as np
import wx

from cis_image import CisImage
from input_editor import ImgEditDlg

os.environ["OPENCV_IO_MAX_IMAGE_PIXELS"] = pow(2, 42).__str__()
import cv2


def find_edge_margin(img):
    samples = 100
    margin_th = 220
    hist_th = samples * 0.8
    h, w = img.shape[:2]
    sample_ys = np.linspace(w, img.shape[0] - w, 100, dtype=int)  # avoid padding of start/end
    # center of left margin
    sx = 5
    ex = img.shape[1] // 4
    left_sample = img[sample_ys, sx: ex, 0]  # enough with first ch
    left_hist = (left_sample > margin_th).sum(axis=0) > hist_th
    left_margin_idx = left_hist.nonzero()[0]
    left_margin_center = None
    if left_margin_idx.size > 0:
        left_margin_center = int(np.median(left_margin_idx))
    # center of right margin
    sx = 3 * img.shape[1] // 4
    ex = img.shape[1] - 5
    right_sample = img[sample_ys, sx: ex, 0]  # enough with first ch
    right_hist = (right_sample > margin_th).sum(axis=0) > hist_th
    right_margin_idx = right_hist.nonzero()[0]
    right_margin_center = None
    if right_margin_idx.size > 0:
        right_margin_center = int(np.median(right_margin_idx) + sx)

    return left_margin_center, right_margin_center


def load_scan(path, default_tempo, force_manual_adjust=False):
    def _img_load(path, default_tempo):
        with wx.BusyCursor():
            # cv2.imread erros with multi-byte path
            n = np.fromfile(path, np.uint8)
            img = cv2.imdecode(n, cv2.IMREAD_COLOR)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # search tempo from ANN file
        ann_path = path.rsplit(".", 1)[0] + ".ANN"
        if os.path.exists(ann_path):
            with open(ann_path) as f:
                for line in f.readlines():
                    val = re.search(r"^/roll_tempo:\s+(\d{2,3})", line)
                    if val is not None:
                        return img, int(val.group(1))
        # search tempo from file name
        val = re.search(r"tempo:?\s*(\d{2,3})", path)
        tempo = int(val.group(1)) if val is not None else default_tempo
        return img, tempo

    def _cis_load(path, default_tempo, force_manual_adjust):
        # load
        obj = CisImage()
        with wx.BusyCursor():
            if not obj.load(path):
                return None, default_tempo
        # find center of roll margin or manually set if not found
        left_edge, right_edge = find_edge_margin(obj.img)
        if left_edge is None or right_edge is None or force_manual_adjust:
            with ImgEditDlg(obj) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    left_edge, right_edge = dlg.get_margin_pos()
                else:
                    return None, default_tempo
        # cut off edge
        obj.img[:, :left_edge] = (255, 255, 255)
        obj.img[:, right_edge:] = (255, 255, 255)
        tempo = default_tempo if obj.tempo == 0 else obj.tempo
        return obj.img, tempo

    basename = os.path.basename(path)
    if basename.lower().endswith(".cis"):
        return _cis_load(path, default_tempo, force_manual_adjust)
    else:
        return _img_load(path, default_tempo)


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
            # print(self.name, self.fps)
            self.fps = 0
            self.start = cur


class InputVideo(wx.Panel):
    def __init__(self, parent, path, disp_size=(800, 600), callback=None):
        wx.Panel.__init__(self, parent, size=parent.FromDIP(wx.Size(disp_size)))
        self.parent = parent
        self.SetDoubleBuffered(True)
        self.disp_w, self.disp_h = disp_size
        self.bmp = wx.Bitmap(self.disp_w, self.disp_h, depth=24)
        self.callback = callback
        self.src = None
        self.src_path = path
        self.scale = self.GetDPIScaleFactor() if platform.system() == "Windows" else 1

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
        if self.thread_worker.is_alive():
            self.thread_worker.join(timeout=3)

    def on_destroy(self, event):
        self.worker_thread_quit = True
        if self.thread_worker.is_alive():
            self.thread_worker.join(timeout=3)
        wx.GetApp().Yield(onlyIfNeeded=True)

    def on_paint(self, event):
        # no need for BufferedPaintDC since SetDoubleBuffered(True)
        dc = wx.PaintDC(self)
        dc.SetUserScale(self.scale, self.scale)

        with self.thread_lock:
            dc.DrawBitmap(self.bmp, 0, 0)

        if self.callback is not None:
            self.callback.player.draw_tracker(dc)

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
        dc.DrawPolygon([(center_x - rad // 2, center_y - int(math.sqrt(3) * rad) // 2),
                        (center_x - rad // 2, center_y + int(math.sqrt(3) * rad) // 2),
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
        t_disp_slowcpu = 0
        while not self.worker_thread_quit:
            t1 = time.perf_counter()

            if self.start_play:
                self._load_next_frame()

            if self.callback is not None:
                self.callback.emulate(self.frame, time.perf_counter())

            if self.thread_lock.acquire(timeout=0):
                self.bmp.CopyFromBuffer(self.frame)
                self.thread_lock.release()
                wx.CallAfter(self.Refresh, eraseBackground=False)  # refresh from thread need call after

            # wait for next frame
            desired_time = self._get_one_frame_time()
            t2 = time.perf_counter()
            elapsed_time = t2 - t1
            if desired_time - elapsed_time < 0:
                t_disp_slowcpu = t2
                self.parent.post_status_msg("Warning: Slow CPU")
                print(f"frame drop...{(desired_time - elapsed_time)*1000:.2f} msec")
            if t2 - t_disp_slowcpu > 1:
                self.parent.post_status_msg("")  # reset warning after 1sec
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


class InputScanImg_v0(InputVideo):
    def __init__(self, parent, img, spool_diameter=2.72, roll_width=11.25, tempo=80, disp_size=(800, 600), callback=None):
        super().__init__(parent, None, disp_size, callback)
        self.src = img
        self.skip_px = 1
        self.spool_rps = 0
        self.cur_spool_diameter = self.org_spool_diameter = spool_diameter
        self.cur_spool_pos = 0
        self.roll_thick = 0.00334646  # in inch
        self.roll_width = roll_width
        self.tempo = tempo

    def start_worker(self):
        # load initial frame
        self.cur_y = self.src.shape[0] - 1
        self.left_side, self.right_side = self._find_roll_edge()
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
                print("self.skip_px", self.skip_px, ", fps", px_per_sec / i)
                break

    def _find_roll_edge(self):
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

        # increase fps to emulating acceleration
        self.worker_fps = takeup_px / self.skip_px

        return 1 / self.worker_fps


class InputScanImg(InputScanImg_v0):
    def start_worker(self):
        # load initial frame
        self.left_side, self.right_side = self._find_roll_edge()
        margin = 7 * (self.right_side - self.left_side + 1) // (self.disp_w - 7 * 2)  # 7px on both edge @800x600
        # crop and resize image
        crop_x1 = max(self.left_side - margin, 0)
        crop_x2 = min(self.right_side + margin, self.src.shape[1])
        self.src = self.src[:, crop_x1:crop_x2 + 1]
        resize_ratio = self.disp_w / self.src.shape[1]
        resize_h = int(self.src.shape[0] * resize_ratio)
        self.src = cv2.resize(self.src, dsize=(self.disp_w, resize_h))
        self.cur_y = self.src.shape[0] - 1

        self.crop_h = self.disp_h
        self.roll_dpi = resize_ratio * (self.right_side - self.left_side + 1) / self.roll_width
        self.set_tempo(self.tempo)
        self._load_next_frame()
        self.thread_worker.start()

    def _load_next_frame(self):
        crop_y2 = self.cur_y
        crop_y1 = crop_y2 - self.crop_h
        if crop_y1 < 0:
            return
        self.frame = self.src[crop_y1:crop_y2]
        self.cur_y -= self.skip_px

        # update take-up spool round
        spool_rpf = self.spool_rps / self.worker_fps
        self.cur_spool_pos += spool_rpf


if __name__ == "__main__":
    from midi_controller import MidiWrap

    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(True)
    except Exception as e:
        print(e)

    app = wx.App()
    frame = wx.Frame(None, wx.ID_ANY, "Frame", size=(1280, 720))

    midobj = MidiWrap()
    midobj.open_port(None)

    panel1 = InputScanImg(frame, path="../sample_scans/Ampico B 68361 Dancing Tambourine tempo95.png")
    panel1.start_worker()
    # print(InputWebcam.list_camera())
    # panel1 = InputWebcam(frame, webcam_no=0)

    def slider_value_change(event):
        obj = event.GetEventObject()
        panel1.set_tempo(obj.GetValue())
    slider = wx.Slider(frame, value=80, minValue=10, maxValue=140, pos=(0, 600), size=frame.FromDIP(wx.Size((200, 100))), style=wx.SL_HORIZONTAL | wx.SL_LABELS)
    slider.SetPageSize(5)
    slider.Bind(wx.EVT_SLIDER, slider_value_change)

    frame.Show()
    app.MainLoop()
