import math
import os
import re
import threading
import time
from pathlib import Path

import numpy as np
import wx
from cis_image import CisImage
from controls import BasePanel
from input_editor import ImgEditDlg

os.environ["OPENCV_IO_MAX_IMAGE_PIXELS"] = pow(2, 42).__str__()
import cv2


def _find_roll_cut_point(img: np.ndarray) -> tuple[int | None, int | None]:
    """
    Finds white margins at both ends of the roll and returns the center coordinates of each margin.
    These coordinates will be used to cut out the roll image.
    """
    samples = 100
    margin_th = 220
    hist_th = samples * 0.8
    h, w = img.shape[:2]
    pad_h = w  # set start/end padding size to same with width
    sample_ys = np.linspace(pad_h, h - pad_h, samples, dtype=int)
    # find left margin center
    sx, ex = 5, w // 4
    left_sample = img[sample_ys, sx: ex, 0]  # enough with first ch
    left_hist = (left_sample > margin_th).sum(axis=0) > hist_th
    left_margin_idx = left_hist.nonzero()[0]
    left_margin_center = None
    if left_margin_idx.size > 0:
        left_margin_center = int(left_margin_idx[-1])
    # find right margin center
    sx, ex = 3 * w // 4, w - 5
    right_sample = img[sample_ys, sx: ex, 0]  # enough with first ch
    right_hist = (right_sample > margin_th).sum(axis=0) > hist_th
    right_margin_idx = right_hist.nonzero()[0]
    right_margin_center = None
    if right_margin_idx.size > 0:
        right_margin_center = int(right_margin_idx[0] + sx)

    return left_margin_center, right_margin_center


def _load_img(path: str, default_tempo: int) -> tuple[np.ndarray | None, int]:
    # cv2.imread can't load path with multi-byte
    try:
        n = np.fromfile(path, np.uint8)
        img = cv2.imdecode(n, cv2.IMREAD_COLOR)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    except Exception:
        return None, default_tempo

    # search tempo from ANN file
    ann_path = Path(path).with_suffix(".ANN")
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


def _load_cis(parent: wx.Frame, path: str, default_tempo: int, force_manual_adjust: bool) -> tuple[np.ndarray | None, int]:
    obj = CisImage()
    if not obj.load(path):
        return None, default_tempo
    # find center of roll margin or manually set if not found
    left_edge, right_edge = _find_roll_cut_point(obj.decoded_img)
    if left_edge is None or right_edge is None or force_manual_adjust:
        with ImgEditDlg(parent, obj) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                left_edge, right_edge = dlg.get_margin_pos()
            else:
                return None, default_tempo
    # cut off edge
    obj.decoded_img[:, :left_edge] = (255, 255, 255)
    obj.decoded_img[:, right_edge:] = (255, 255, 255)

    # search tempo from CIS header
    tempo = default_tempo if obj.tempo == 0 else obj.tempo
    return obj.decoded_img, tempo


def load_scan(parent: wx.Frame, path: str, default_tempo: int, force_manual_adjust: bool = False) -> tuple[np.ndarray | None, int]:
    with wx.BusyCursor():
        if Path(path).suffix.lower().endswith(".cis"):
            return _load_cis(parent, path, default_tempo, force_manual_adjust)
        else:
            return _load_img(path, default_tempo)


class FPScounter:
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


class InputVideo(BasePanel):
    def __init__(self, parent, path, window_scale, callback=None):
        self.disp_w, self.disp_h = (800, 600)
        BasePanel.__init__(self, parent, size=parent.get_dipscaled_size(wx.Size((self.disp_w, self.disp_h))))
        self.parent = parent
        self.SetDoubleBuffered(True)
        self.bmp = wx.Bitmap(self.disp_w, self.disp_h, depth=24)
        self.callback = callback
        self.src = None
        self.src_path = path
        self.scale = parent.get_dpiscale_factor()

        self.start_play = False
        self.repeat_btn_focused = False
        self.manual_expression = False
        self.draw_cache = {}
        self.expression_btn_pressed = {ord("A"): False, ord("S"): False, ord("J"): False, ord("K"): False, ord("L"): False}

        self.repeat_btn_pos = (0, 0, 0, 0)
        self.play_btn_focused = False
        self.thread_enable = True
        self.thread_worker = threading.Thread(target=self.load_thread)
        self.worker_fps = 60
        self.cnt_worker_fps = FPScounter("worker fps")
        self.thread_lock = threading.Lock()

        self.Bind(wx.EVT_PAINT, self.on_paint)
        # self.Bind(wx.EVT_WINDOW_DESTROY, self.on_destroy)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse)

    def start_worker(self):
        self.src = cv2.VideoCapture(self.src_path)
        self._load_next_frame()
        self.thread_worker.start()

    def set_pressed_key(self, keycode: int, is_pressed: bool) -> None:
        if keycode in self.expression_btn_pressed:
            self.expression_btn_pressed[keycode] = is_pressed

    def set_manual_expression(self, enabled: bool) -> None:
        self.manual_expression = enabled

    def on_destroy(self, event=None):
        self.thread_enable = False
        if self.thread_worker.is_alive():
            self.thread_worker.join(timeout=3)
        wx.GetApp().Yield(onlyIfNeeded=True)

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        dc.SetUserScale(self.scale, self.scale)

        with self.thread_lock:
            dc.DrawBitmap(self.bmp, 0, 0)

        if self.callback is not None:
            self.callback.player.draw_tracker(dc)

        # draw play button
        if not self.start_play:
            self.draw_buttons(dc)

        if self.manual_expression:
            self.draw_manual_expression(dc)

    def draw_buttons(self, dc: wx.PaintDC) -> None:
        # Draw Play/Repeat button

        dc = wx.GCDC(dc)  # for anti-aliasing

        # Play button outer
        bg_color =  "#60a5fa"  # tailwind bg-blue-400 color
        focused_color = "#3b82f6"  # tailwind bg-blue-500 color
        color = focused_color if self.play_btn_focused else bg_color
        dc.SetBrush(wx.Brush(color))
        dc.SetPen(wx.Pen(color))
        rad = self.disp_h // 14
        center_x, center_y = rad + (self.disp_w // 2), self.disp_h // 2
        dc.DrawCircle(center_x, center_y, rad)

        # Repeat button outer
        bg_color =  "#4ade80"  # tailwind bg-green-400 color
        focused_color = "#22c55e"  # tailwind bg-green-500 color
        color = focused_color if self.repeat_btn_focused else bg_color
        dc.SetBrush(wx.Brush(color))
        dc.SetPen(wx.Pen(color))
        x1, y1 = center_x - rad * 4, center_y - rad
        w = h = rad * 2
        self.repeat_btn_pos = (x1, y1, w, h)
        dc.DrawRoundedRectangle(*self.repeat_btn_pos, radius=w // 10)

        # Play button inner
        dc.SetBrush(wx.Brush("white"))
        dc.SetPen(wx.Pen("white"))
        rad = self.disp_h // 20
        dc.DrawPolygon([(center_x - rad // 2, center_y - int(math.sqrt(3) * rad) // 2),
                        (center_x - rad // 2, center_y + int(math.sqrt(3) * rad) // 2),
                        (center_x + rad, center_y)])

        # Repeat button inner
        center_x -= rad * 4
        dc.DrawPolygon([(center_x + rad // 2, center_y - int(math.sqrt(3) * rad) // 2),
                        (center_x + rad // 2, center_y + int(math.sqrt(3) * rad) // 2),
                        (center_x - rad, center_y)])
        dc.DrawRectangle(center_x - rad, center_y - int(math.sqrt(3) * rad) // 2, 5, int(math.sqrt(3) * rad))

    def draw_manual_expression(self, dc: wx.PaintDC) -> None:
        # Draw manual expression controls on bottom of screen
        dc = wx.GCDC(dc)  # for anti-aliasing

        # draw background
        dc.SetBrush(wx.Brush("#eeeeee"))
        dc.SetPen(wx.Pen("#eeeeee"))
        base_x, base_y = 0, 4 * self.disp_h // 5
        base_h = self.disp_h // 5
        dc.DrawRectangle((base_x, base_y), (self.disp_w, self.disp_h))

        # guidance
        txt = "Manual Expression Keyboard Controls"
        if "guid_font_size" not in self.draw_cache:
            guid_font_size = 10
            dc.SetFont(wx.Font(guid_font_size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            txt_w = dc.GetTextExtent(txt).Width
            self.draw_cache["guid_font_size"] = guid_font_size * self.disp_w // (txt_w * 2)
            self.draw_cache["guid_font"] = wx.Font(self.draw_cache["guid_font_size"], wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        guid_font_size = self.draw_cache["guid_font_size"]
        dc.SetFont(self.draw_cache["guid_font"])
        if "guid_txt_size" not in self.draw_cache:
            self.draw_cache["guid_txt_size"] = dc.GetTextExtent(txt)
        txt_w, txt_h = self.draw_cache["guid_txt_size"]
        x1 = self.disp_w // 2 - txt_w // 2
        y1 = base_y + txt_h // 2
        dc.DrawText(txt, x1, y1)

        # Accent keys
        font_size = int(guid_font_size * 0.8)
        if "other_font" not in self.draw_cache:
            self.draw_cache["other_font"] = wx.Font(font_size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        dc.SetFont(self.draw_cache["other_font"])

        # cache
        for txt in ("Accent", "Intensity", "Bass", "Treble", "Lv1", "Lv2", "Lv4", "A", "S", "J", "K", "L"):
            key = f"{txt}_txt_size"
            if key not in self.draw_cache:
                self.draw_cache[key] = dc.GetTextExtent(txt)

        txt = "Accent"
        txt_w, txt_h = self.draw_cache[f"{txt}_txt_size"]
        x1 = self.disp_w // 10
        y1 = base_y + 2 * base_h // 3
        dc.DrawText(txt, x1, y1)

        # "A", "B"
        x1 += txt_w + txt_h // 2
        button_w, button_h = dc.GetTextExtent("AAAA")
        for key, title in zip(("A", "S"), ("Bass", "Treble")):
            # key outer
            color = "#fca5a5" if self.expression_btn_pressed[ord(key)] else "#cccccc"
            dc.SetBrush(wx.Brush(color))
            dc.SetPen(wx.Pen(color))
            dc.DrawRoundedRectangle(x1, y1, button_w, int(button_h * 1.1), radius=button_h // 5)

            # Inner Text
            txt_w, _ = self.draw_cache[f"{key}_txt_size"]
            dc.DrawText(key, x1 + (button_w // 2) - (txt_w // 2), y1)
            # title text
            txt_w, _ = self.draw_cache[f"{title}_txt_size"]
            dc.DrawText(title, x1 + (button_w // 2) - (txt_w // 2), y1 - button_h)
            x1 += self.disp_w // 10

        # Intensity keys
        txt = "Intensity"
        txt_w, txt_h = self.draw_cache[f"{txt}_txt_size"]
        x1 = 5 * self.disp_w // 10
        dc.DrawText(txt, x1, y1)

        # "J", "K", "L"
        x1 += txt_w + txt_h // 2
        for key, title in zip(("J", "K", "L"), ("Lv1", "Lv2", "Lv4")):
            # key outer
            color = "#fca5a5" if self.expression_btn_pressed[ord(key)] else "#cccccc"
            dc.SetBrush(wx.Brush(color))
            dc.SetPen(wx.Pen(color))
            dc.DrawRoundedRectangle(x1, y1, button_w, int(button_h * 1.1), radius=button_h // 5)

            # Inner Text
            txt_w, _ = self.draw_cache[f"{key}_txt_size"]
            dc.DrawText(key, x1 + (button_w // 2) - (txt_w // 2), y1)
            # title text
            txt_w, _ = self.draw_cache[f"{title}_txt_size"]
            dc.DrawText(title, x1 + (button_w // 2) - (txt_w // 2), y1 - button_h)
            x1 += self.disp_w // 10

    def on_mouse(self, event):
        # check button is focused and pressed
        if event.Leaving():
            self.repeat_btn_focused = False
            self.play_btn_focused = False
        else:
            pos = event.GetPosition()
            if not self.start_play and \
                self.repeat_btn_pos[0] < pos.x // self.scale < self.repeat_btn_pos[0] + self.repeat_btn_pos[2] and \
                self.repeat_btn_pos[1] < pos.y // self.scale < self.repeat_btn_pos[1] + self.repeat_btn_pos[3]:
                self.repeat_btn_focused = True
                self.play_btn_focused = False
            else:
                self.repeat_btn_focused = False
                self.play_btn_focused = True

        if self.repeat_btn_focused and event.LeftDown():
            self.on_repeat()
        elif self.play_btn_focused and event.LeftDown():
            self.on_start()

    def on_start(self):
        self.start_play = not self.start_play

    def on_repeat(self):
        pass

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
        while self.thread_enable:
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
            if elapsed_time > desired_time:
                t_disp_slowcpu = t2
                self.parent.post_status_msg("Warning: Slow CPU")
                print(f"frame drop...{(desired_time - elapsed_time)*1000:.2f} msec")
            if t2 - t_disp_slowcpu > 1:
                self.parent.post_status_msg("")  # reset warning after 1sec
            while desired_time > elapsed_time:
                sleep = 0.001 if desired_time - elapsed_time > 0.0015 else 0
                time.sleep(sleep)
                elapsed_time = time.perf_counter() - t1

            # self.cnt_worker_fps()
        print(f"end {self.__class__.__name__}.load_thread")


class InputWebcam(InputVideo):
    def __init__(self, parent, webcam_no=0, window_scale=1, callback=None):
        super().__init__(parent, webcam_no, window_scale, callback)
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
    def __init__(self, parent, img, spool_diameter=2.72, roll_width=11.25, tempo=80, window_scale=1, callback=None) -> None:
        super().__init__(parent, None, window_scale, callback)
        self.src = img
        self.skip_px = 1
        self.spool_rps = 0
        self.cur_spool_diameter = self.org_spool_diameter = spool_diameter
        self.cur_spool_pos = 0
        self.roll_thick = 0.00334646  # in inch
        self.roll_width = roll_width
        self.tempo = tempo

    def start_worker(self) -> None:
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

    def on_repeat(self) -> None:
        self.parent.midi_off()
        self.start_play = False
        self.cur_y = self.src.shape[0] - 1
        self.cur_spool_pos = 0
        self.cur_spool_diameter = self.org_spool_diameter
        self._load_next_frame()

    def set_tempo(self, tempo: float) -> None:
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

    def _find_roll_edge(self) -> list[int, int]:
        # find roll edge x coordinate
        roll_h, roll_w = self.src.shape[:2]
        edges = []
        edge_th = 220
        # find roll edges
        sample_ys = np.linspace(0, roll_h - 1, 20, dtype=int)
        for v in (self.src[sample_ys, :, 0] < edge_th):
            t = v.nonzero()[0]
            if len(t) < 2:
                edges.append((0, roll_w - 1))
            else:
                edges.append(t[[0, -1]].tolist())

        # sort by width, and get a middle point
        edges.sort(key=lambda x: x[1] - x[0])
        middle = len(edges) // 2
        return edges[middle]

    def _load_next_frame(self) -> None:
        crop_y2 = self.cur_y
        crop_y1 = crop_y2 - self.crop_h
        if crop_y1 < 0:
            return
        self.frame = self.src[crop_y1:crop_y2]
        self.cur_y -= self.skip_px

        # update take-up spool round
        spool_rpf = self.spool_rps / self.worker_fps
        self.cur_spool_pos += spool_rpf

    def _get_one_frame_time(self) -> float:
        # spool diameter will increase per 1 round. this causes acceleration.
        if self.cur_spool_pos > 1:
            self.cur_spool_pos -= 1  # don't reset to 0.
            self.cur_spool_diameter += self.roll_thick

        # take-up pixels per one second
        takeup_px = self.spool_rps * self.cur_spool_diameter * math.pi * self.roll_dpi

        # increase fps to emulating acceleration
        self.worker_fps = takeup_px / self.skip_px
        return 1 / self.worker_fps


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
    img, tempo = load_scan("../sample_scans/Duo-Art 67249 Dance Of The Hours.CIS", 80)
    panel1 = InputScanImg(frame, img)
    panel1.start_worker()
    # print(InputWebcam.list_camera())
    # panel1 = InputWebcam(frame, webcam_no=0)

    def slider_value_change(event):
        obj = event.GetEventObject()
        panel1.set_tempo(obj.GetValue())
    slider = wx.Slider(frame, value=80, minValue=10, maxValue=140, pos=(0, 600), size=frame.get_dipscaled_size(wx.Size((200, 100))), style=wx.SL_HORIZONTAL | wx.SL_LABELS)
    slider.SetPageSize(5)
    slider.Bind(wx.EVT_SLIDER, slider_value_change)

    frame.Show()
    app.MainLoop()
