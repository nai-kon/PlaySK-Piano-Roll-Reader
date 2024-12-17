import math
import platform

import wx
import wx.grid
from controls import BasePanel


class OrganStopIndicator(BasePanel):
    def __init__(self, parent) -> None:
        BasePanel.__init__(self, parent, wx.ID_ANY)
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

    def init_stop(self, data: dict[str, dict[str, bool]]) -> None:
        if self.grid.GetNumberRows() > 0:
            # already created
            self.change_stop(data)
            return

        # calc each cell position
        cols = 3
        cur_row = 0
        for part, stops in data.items():
            self.data[part] = {}
            cur_row += 1
            rows = math.ceil(len(stops) / cols)
            for i, stop in enumerate(stops):
                row = i % rows + cur_row
                col = i // rows
                self.data[part][stop] = {"col": col, "row": row}

            cur_row += rows

        # create grid
        self.grid.CreateGrid(cur_row, cols)

        # set header color
        if platform.system() == "Windows":
            header_bg_color = "#AAAAAA"
        elif wx.SystemSettings.GetAppearance().IsDark():
            header_bg_color = "#362927"
        else:
            header_bg_color = "#F3ECEB"

        # set cells
        cur_row = 0
        for part in data:
            # header
            self.grid.SetCellValue(cur_row, 0, part)
            self.grid.SetCellBackgroundColour(cur_row, 0, header_bg_color)
            self.grid.SetCellAlignment(cur_row, 0, wx.ALIGN_LEFT, wx.ALIGN_BOTTOM)
            self.grid.SetCellSize(cur_row, 0, 1, 3)

            # cells
            max_row = 0
            for stop, pos in self.data[part].items():
                row, col = pos["row"], pos["col"]
                self.grid.SetCellValue(row, col, stop)
                self.grid.SetCellAlignment(row, col, wx.ALIGN_CENTER, wx.ALIGN_CENTER)
                max_row = max(row, max_row)
            cur_row = max_row + 1

        self.change_stop(data)
        self.grid.AutoSize()
        self.Fit()

    def _change_stop_inner(self, data: dict[str, dict[str, bool]]) -> None:
        # change stop indicator on/off
        for part, stops in data.items():
            for label, is_on in stops.items():
                pos = self.data[part].get(label, None)
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
    panel1 = OrganStopIndicator(frame)

    data = {
        "Swell":{
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
        },
        "Great":{
            "Chimes": False,
            "Flute4": True,
            "Tremolo": False,
            "FluteP": True,
            "Harp": False,
        },
    }
    panel1.init_stop(data)

    frame.Fit()
    frame.Show()
    app.MainLoop()
