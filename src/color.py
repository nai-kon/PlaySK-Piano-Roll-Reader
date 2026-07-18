from config import ConfigMng


class Color:
    @staticmethod
    def cur_theme() -> str:
        conf = ConfigMng()
        return conf.theme

    @staticmethod
    def main_bg() -> str:
        return "#222222" if Color.cur_theme() == "Dark" else "#aaaaaa"

    @staticmethod
    def welcome_bg() -> str:
        return "#333333" if Color.cur_theme() == "Dark" else "#555555"

    @staticmethod
    def welcome_text() -> str:
        return "#ffffff"

    @staticmethod
    def midi_btn_bg() -> str:
        return "#cb9255"

    @staticmethod
    def vacuum_gauge_bg() -> str:
        return "#303030"

    @staticmethod
    def vacuum_gauge_scale() -> str:
        return "#ffffff"

    @staticmethod
    def vacuum_gauge_grid() -> str:
        return "#000000"

    @staticmethod
    def vacuum_gauge_graph() -> str:
        return "yellow"

    @staticmethod
    def organ_stop_on_bg() -> str:
        return "#cb9255"

    @staticmethod
    def organ_stop_off_bg() -> str:
        return "#303030"

    @staticmethod
    def organ_stop_on_text() -> str:
        return "#000000"

    @staticmethod
    def organ_stop_off_text() -> str:
        return "#ffffff"

    @staticmethod
    def organ_stop_header() -> str:
        return Color.main_bg()

    @staticmethod
    def play_btn() -> str:
        return "#60a5fa"  # tailwind bg-blue-400 color

    @staticmethod
    def play_btn_focused() -> str:
        return "#3b82f6"  # tailwind bg-blue-500 color

    @staticmethod
    def repeat_btn() -> str:
        return "#4ade80"  # tailwind bg-green-400 color

    @staticmethod
    def repeat_btn_focused() -> str:
        return "#22c55e"  # tailwind bg-green-500 color

    @staticmethod
    def manual_ctrl_bg() -> str:
        return "#333333" if Color.cur_theme() == "Dark" else "#eeeeee"

    @staticmethod
    def manual_ctrl_key() -> str:
        return "#cccccc"

    @staticmethod
    def manual_ctrl_key_pressed() -> str:
        return "#cb9255"

    @staticmethod
    def manual_ctrl_text() -> str:
        return "#ffffff" if Color.cur_theme() == "Dark" else "#000000"
