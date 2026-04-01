try:
    import pynput.keyboard as kb_ctrl

    PYNPUT_OK = True
except ImportError:
    PYNPUT_OK = False


class KeyInjector:
    def __init__(self):
        self.controller = kb_ctrl.Controller() if PYNPUT_OK else None

    def type_char(self, ch):
        if not self.controller:
            return
        try:
            self.controller.type(ch)
        except Exception:
            pass

    def backspace(self):
        if not self.controller:
            return
        try:
            self.controller.press(kb_ctrl.Key.backspace)
            self.controller.release(kb_ctrl.Key.backspace)
        except Exception:
            pass

    def space(self):
        if not self.controller:
            return
        try:
            self.controller.press(kb_ctrl.Key.space)
            self.controller.release(kb_ctrl.Key.space)
        except Exception:
            pass
