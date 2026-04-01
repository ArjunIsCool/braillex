try:
    import ctypes
    from ctypes import windll

    WINDOWS_KEYBOARD_OK = True
except ImportError:
    WINDOWS_KEYBOARD_OK = False


class KeyboardLayoutManager:
    def __init__(self):
        self.active_layout = "en"
        self.layout_map = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "hi": "Hindi",
            "ar": "Arabic",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "ta": "Tamil",
        }

    def get_active_layout(self):
        if WINDOWS_KEYBOARD_OK:
            try:
                hwnd = windll.user32.GetForegroundWindow()
                layout_id = windll.user32.GetKeyboardLayout(0)
                lang_id = layout_id & 0xFFFF

                lang_map = {
                    0x0409: "en",
                    0x0809: "en",
                    0x0C0A: "es",
                    0x040C: "fr",
                    0x0407: "de",
                    0x0439: "hi",
                    0x0401: "ar",
                    0x0804: "zh",
                    0x0404: "zh",
                    0x0411: "ja",
                    0x0412: "ko",
                    0x0449: "ta",
                }

                self.active_layout = lang_map.get(lang_id, "en")
                return self.active_layout
            except Exception:
                pass
        return "en"

    def get_available_layouts(self):
        return list(self.layout_map.values())

    def get_layout_code(self, layout_name):
        for code, name in self.layout_map.items():
            if name == layout_name:
                return code
        return "en"
