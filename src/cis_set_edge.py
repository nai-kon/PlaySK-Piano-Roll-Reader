import wx
import cv2
from cis_decoder import CisImage, ScannerType
import platform


class SetEdgeDlg(wx.Dialog):
    def __init__(self, cis: CisImage):
        wx.Dialog.__init__(self, None, title="Set roll edge")
        border_size = self.FromDIP(5)
        self.panel = SetEdgePane(self, cis.img_data)
        sizer1 = wx.BoxSizer(wx.VERTICAL)
        sizer1.Add(self.panel)
        sizer2 = wx.BoxSizer(wx.VERTICAL)
        sizer2.Add(wx.StaticText(self, label=f"- Tempo {cis.tempo}"))
        sizer2.Add(wx.StaticText(self, label=f"- {cis.scanner_type.value}"))
        if cis.doubler:
            sizer2.Add(wx.StaticText(self, label="- Clock Doubler"))
        if cis.bicolor:
            sizer2.Add(wx.StaticText(self, label="- Bi-Color scan"))
        if cis.mirror:
            sizer2.Add(wx.StaticText(self, label="- Miror Image"))
        if cis.reverse:
            sizer2.Add(wx.StaticText(self, label="- Reverse Scan"))
        sizer2.Add(wx.StaticText(self, label=f"- Horizontal {cis.hol_dpi} DPI"))
        sizer2.Add(wx.StaticText(self, label=f"- Horizontal {cis.hol_px} px"))
        if cis.scanner_type in [ScannerType.WHEELRUN, ScannerType.SHAFTRUN]:
            sizer2.Add(wx.StaticText(self, label=f"- Vertical {cis.vert_res} TPI"))
        else:
            sizer2.Add(wx.StaticText(self, label=f"- Vertical {cis.vert_res} LPI"))
        ok_btn = wx.Button(self, wx.ID_OK, size=self.FromDIP(wx.Size((90, 50))), label="OK")
        cancel_btn = wx.Button(self, wx.ID_CANCEL, size=self.FromDIP(wx.Size((90, 50))), label="Cancel")
        sizer2.Add(ok_btn)
        sizer2.Add(cancel_btn)

        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add(sizer1, border=border_size)
        sizer3.Add(sizer2, border=border_size)
        self.SetSizer(sizer3)
        self.Fit()

    def get_margin_pos(self):
        return self.panel.get_pos()


class SetEdgePane(wx.Panel):
    def __init__(self, parent, img):
        size = parent.FromDIP(wx.Size(950, 950))
        wx.Panel.__init__(self, parent, size=size)
        self.SetDoubleBuffered(True)
        self.frame_w = size[1]

        org_img_h, self.org_img_w = img.shape[:2]
        resized_h = org_img_h * self.frame_w // self.org_img_w
        img = cv2.resize(img, dsize=(self.frame_w, resized_h))
        self.left_margin_x, self.right_margin_x = 100, img.shape[1] - 100
        self.img = wx.Bitmap.FromBuffer(img.shape[1], img.shape[0], img)
        self.img_h = self.img.GetHeight()
        self.scroll_y1 = self.img_h // 2
        self.scroll_size = 500  # @px
        self.norm_cursor = wx.Cursor()
        self.adjust_cursor = wx.Cursor(wx.CURSOR_SIZEWE)
        self.adjust_cursor_slip = self.FromDIP(20)
        self.guide_base_text = "Set this line to the center of the white margin"
        self.guide_font = wx.Font(15, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_SEMIBOLD)
        self.scale = self.GetDPIScaleFactor() if platform.system() == "Windows" else 1

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_scroll)
        self.Bind(wx.EVT_MOTION, self.on_mouse)

    def on_paint(self, event):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.img, 0, self.scroll_y1 * -1)

        # guide text
        dc.SetFont(self.guide_font)
        dc.SetBackgroundMode(wx.BRUSHSTYLE_SOLID)
        dc.SetTextForeground((180, 0, 0))
        dc.DrawText("← " + self.guide_base_text, self.left_margin_x, self.frame_w // 3)
        text_len = dc.GetFullMultiLineTextExtent(self.guide_base_text + " →", self.guide_font)
        dc.DrawText(self.guide_base_text + " →", self.right_margin_x - text_len[0], self.frame_w // 2)

        # guide line
        dc.SetPen(wx.Pen((180, 0, 0), self.FromDIP(3), wx.SOLID))
        dc.DrawLine(self.left_margin_x, 0, self.left_margin_x, self.frame_w)
        dc.DrawLine(self.right_margin_x, 0, self.right_margin_x, self.frame_w)

    def on_scroll(self, event):
        direction = -1 if event.GetWheelRotation() > 0 else 1
        self.scroll_y1 = max(min(self.scroll_y1 + self.scroll_size * direction, self.img_h - self.frame_w), 0)
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

    def get_pos(self):
        left = self.ToDIP(self.left_margin_x) * self.org_img_w * self.scale / self.frame_w
        right = self.ToDIP(self.right_margin_x) * self.org_img_w * self.scale / self.frame_w
        return int(left), int(right)


if __name__ == '__main__':
    from cis_decoder import CisImage

    # high DPI awareness
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(True)
    except Exception as e:
        print(e)

    app = wx.App()

    obj = CisImage()
    if obj.load("../Dinner Music # 5 (1925) 65163A.CIS"):
        with SetEdgeDlg(obj) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                print(dlg.get_edge_pos())
