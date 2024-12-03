import math

import wx
import wx.grid
from controls import BasePanel


class OrganStopIndicator(BasePanel):
    def __init__(self, parent, caption: str="") -> None:
        BasePanel.__init__(self, parent, wx.ID_ANY)
        self.caption = wx.StaticText(self, wx.ID_ANY, caption)

        self.data = {}
        self.grid = wx.grid.Grid(self)
        self.grid.EnableGridLines(False)
        # disable edit
        self.grid.EnableEditing(False)
        # disable header
        self.grid.SetColLabelSize(0)
        self.grid.SetRowLabelSize(0)
        self.grid.SetCellHighlightPenWidth(0)

        # disable size change
        self.grid.EnableDragColSize(False)
        self.grid.EnableDragRowSize(False)
        self.grid.EnableDragGridSize(False)

        self.cell_color_off = "#303030"
        self.cell_color_on = "#f6b26b"
        self.text_color_off = "white"
        self.text_color_on = "black"
        self.grid.SetDefaultCellBackgroundColour(self.cell_color_off)

        self.grid.AutoSize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.caption, flag=wx.EXPAND)
        sizer.Add(self.grid, flag=wx.EXPAND)
        self.SetSizer(sizer)
        self.Fit()

    def init_stop(self, data: dict[str, bool]) -> None:
        # initialize stop
        cols = 2
        rows = math.ceil(len(data) / cols)
        self.grid.CreateGrid(rows, cols)
        for i, label in enumerate(data):
            row = i % rows
            col = i // rows
            self.data[label] = {"col": col, "row": row}
            self.grid.SetCellValue(row, col, label)

        self.change_stop(data)
        self.grid.AutoSize()
        self.Fit()

    def _change_stop_inner(self, data: dict[str, bool]) -> None:
        # change stop on/off
        for label, is_on in data.items():
            pos = self.data.get(label, None)
            if pos is None:
                continue

            row, col = pos["row"], pos["col"]
            if is_on:
                self.grid.SetCellBackgroundColour(row, col, self.cell_color_on)
                self.grid.SetCellTextColour(row, col, self.text_color_on)
            else:
                self.grid.SetCellBackgroundColour(row, col, self.cell_color_off)
                self.grid.SetCellTextColour(row, col, self.text_color_off)

        self.Refresh()

    def change_stop(self, data: dict[str, bool]) -> None:
        wx.CallAfter(self._change_stop_inner, data)


if __name__ == "__main__":
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(True)
    app = wx.App()
    frame = wx.Frame(None, wx.ID_ANY, size=(1000, 1000))
    panel1 = OrganStopIndicator(frame, "Swell")

    data = {
        "Chimes": False,
        "Flute4": True,
        "Tremolo": False,
        "FluteP": True,
        "Harp": False,
        "String Vibrato f": False,
        "Trumpet": False,
        "String f": True,
        "Oboe": False,
        "String mf": True,
        "Vox Humana": False,
        "String p": False,
        "Diapason mf": True,
        "String pp": True,
        "Flute16": False,
        "Soft chimes": False,
    }
    panel1.init_stop(data)

    frame.Fit()
    frame.Show()
    app.MainLoop()
