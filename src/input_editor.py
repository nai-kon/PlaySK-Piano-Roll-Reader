from pathlib import Path

import cv2
import numpy as np
import wx

from cis_image import CisImage, ScannerType


class ImgEditDlg(wx.Dialog):
    def __init__(self, parent, cis: CisImage):
        wx.Dialog.__init__(self, None, title="Adjust roll image")
        self.parent = parent
        self.cis = cis
        self.panel = SetEdgePane(self, cis.decoded_img)

        border_size = self.get_dipscaled_size(5)
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(wx.StaticText(self, label=self.get_show_text()), 1, wx.EXPAND | wx.ALL, border_size)
        convert_bw_btn = wx.Button(self, label="Convert Black pixel to White")
        sizer1.Add(convert_bw_btn, 1, wx.EXPAND | wx.ALL, border_size)
        save_btn = wx.Button(self, label="Save as PNG image")
        sizer1.Add(save_btn, 1, wx.EXPAND | wx.ALL, border_size)
        sizer1.Add(wx.Button(self, wx.ID_CANCEL, label="Cancel"), 1, wx.EXPAND | wx.ALL, border_size)
        sizer1.Add(wx.Button(self, wx.ID_OK, label="OK"), 1, wx.EXPAND | wx.ALL, border_size)

        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.panel)
        sizer2.Add(sizer1)
        self.SetSizer(sizer2)
        self.Fit()

        x, _ = self.GetPosition()
        cur_w, _ = self.GetSize()
        set_x = min(x, wx.Display().GetClientArea().width - cur_w - 1)
        self.SetPosition((set_x, 0))

        convert_bw_btn.Bind(wx.EVT_BUTTON, self.convert_bw)
        save_btn.Bind(wx.EVT_BUTTON, self.save_img)

    def convert_bw(self, event):
        # some cis scan has black background so convert it to white
        with wx.BusyCursor():
            self.cis.convert_bw()
        self.panel.set_image(self.cis.decoded_img)
        self.panel.Refresh()

    def save_img(self, event) -> None:
        # save decoded CIS as PNG image
        with wx.FileDialog(self, "Save as PNG File", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                           wildcard="PNG files (*.png)|*.png",
                           defaultFile=Path(self.cis.file_path).with_suffix(".png").name) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                with wx.BusyCursor():
                    ret = cv2.imwrite(path, self.cis.decoded_img)
                if not ret:
                    wx.MessageBox("Failed to save the image.", "Error")

    def get_show_text(self):
        # get roll info text
        out = [f"Type: {self.cis.scanner_type.value}"]
        if self.cis.is_twin_array:
            out.append("Twin Array scan")
        if self.cis.is_bicolor:
            out.append("Bi-Color scan")
        out.append(f"Tempo: {self.cis.tempo}")
        out.append(f"Horizontal: {self.cis.hol_dpi} Dots / inch")
        if self.cis.scanner_type in (ScannerType.WHEELENCODER, ScannerType.SHAFTENCODER):
            out.append(f"Vertical: {self.cis.vert_res} Ticks / inch (Re-clocked)")
        else:
            out.append(f"Vertical: {self.cis.vert_res} Lines / inch")

        return "\n".join(out)

    def get_edge_pos(self):
        return self.panel.get_edge_pos()

    def get_dipscaled_size(self, size):
        return self.parent.get_dipscaled_size(size)

    def get_dpiscale_factor(self):
        return self.parent.get_dpiscale_factor()


class SetEdgePane(wx.Panel):
    def __init__(self, parent, img: np.ndarray):
        self.frame_w = parent.get_dipscaled_size(950)
        self.frame_h = wx.Display().GetClientArea().height  # display height
        wx.Panel.__init__(self, parent, size=(self.frame_w, self.frame_h))
        self.SetDoubleBuffered(True)
        self.set_image(img)

        self.scroll_size = 500  # @px
        self.norm_cursor = wx.Cursor()
        self.guild_line_w = parent.get_dipscaled_size(2)
        self.adjust_cursor = wx.Cursor(wx.CURSOR_SIZEWE)
        self.adjust_cursor_slip = parent.get_dipscaled_size(20)
        self.guide_base_text = "Set this line to the edge of the roll"
        self.guide_font = wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_SEMIBOLD)
        self.scale = parent.get_dpiscale_factor()

        text = "Roll edge could not be detected. Please set it manually."
        guidance = wx.StaticText(self, label=text, size=wx.Size(self.frame_w, 0), style=wx.ALIGN_CENTRE_HORIZONTAL)
        guidance.SetFont(wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_SEMIBOLD))

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_scroll)
        self.Bind(wx.EVT_MOTION, self.on_mouse)

    def set_image(self, img: np.ndarray):
        org_img_h, self.org_img_w = img.shape[:2]
        resized_h = org_img_h * self.frame_w // self.org_img_w
        img = cv2.resize(img, dsize=(self.frame_w, resized_h))
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        self.left_margin_x, self.right_margin_x = 100, img.shape[1] - 100
        self.img = wx.Bitmap.FromBuffer(img.shape[1], img.shape[0], img)
        self.img_h = self.img.GetHeight()
        self.scroll_y1 = self.img_h // 2

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.img, 0, self.scroll_y1 * -1)

        # guide text
        dc.SetFont(self.guide_font)
        dc.SetBackgroundMode(wx.BRUSHSTYLE_SOLID)
        dc.SetTextBackground((255, 255, 255))
        dc.SetTextForeground((180, 0, 0))
        dc.DrawText("← " + self.guide_base_text, self.left_margin_x, self.frame_h // 3)
        text_len = dc.GetFullMultiLineTextExtent(self.guide_base_text + " →", self.guide_font)
        dc.DrawText(self.guide_base_text + " →", self.right_margin_x - text_len[0], self.frame_h // 2)

        # guide line
        dc.SetPen(wx.Pen((180, 0, 0), self.guild_line_w, wx.SOLID))
        dc.DrawLine(self.left_margin_x, 0, self.left_margin_x, self.frame_h)
        dc.DrawLine(self.right_margin_x, 0, self.right_margin_x, self.frame_h)

    def on_scroll(self, event):
        direction = -1 if event.GetWheelRotation() > 0 else 1
        self.scroll_y1 = max(min(self.scroll_y1 + self.scroll_size * direction, self.img_h - self.frame_h), 0)
        self.Refresh()

    def on_mouse(self, event):
        pos = event.GetPosition()
        left_active = False
        right_active = False
        if self.left_margin_x - self.adjust_cursor_slip < pos.x < self.left_margin_x + self.adjust_cursor_slip:
            left_active = True
        elif self.right_margin_x - self.adjust_cursor_slip < pos.x < self.right_margin_x + self.adjust_cursor_slip:
            right_active = True

        if left_active or right_active:
            self.SetCursor(self.adjust_cursor)
        else:
            self.SetCursor(self.norm_cursor)

        if left_active and event.Dragging():
            self.left_margin_x = pos.x
            self.Refresh()
        elif right_active and event.Dragging():
            self.right_margin_x = pos.x
            self.Refresh()

    def get_edge_pos(self):
        left = int(self.left_margin_x * self.org_img_w / self.frame_w)
        right = int(self.right_margin_x * self.org_img_w / self.frame_w)
        return left, right


if __name__ == "__main__":
    from cis_image import CisImage

    # high DPI awareness
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(True)
    except Exception as e:
        print(e)

    app = wx.App()

    frame = wx.Frame(None, wx.ID_ANY, "Frame", size=(1280, 720))

    obj = CisImage()
    if obj.load("../sample_scans/Ampico B 2551 If God Left Only You.CIS"):
        with ImgEditDlg(frame, obj) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                print(dlg.get_margin_pos())
