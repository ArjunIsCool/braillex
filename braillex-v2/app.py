import flet as ft
import queue
import threading
from datetime import datetime

from ui.theme import *
from ui.components import status_dot, LogPanel
from ui.connection_panel import build_connection_panel
from ui.status_panel import build_status_panel
from ui.voice_panel import build_voice_panel
from ui.sentence_panel import build_sentence_panel, update_sentence_display
from ui.debug_panel import build_debug_panel

from core.serial_worker import SerialWorker
from core.key_injector import KeyInjector
from core.tts_engine import TTSEngine, PYTTSX3_OK
from core.translator import KeyboardLayoutManager
from core.grammar import correct_text
from core.port_discovery import find_braillex_com_port, get_all_com_ports


try:
    from core.key_injector import PYNPUT_OK
except ImportError:
    PYNPUT_OK = False


class BraillexApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.worker = None
        self.event_q = queue.Queue()
        self.injector = KeyInjector()
        self.tts = TTSEngine()
        self.kbd_layout = KeyboardLayoutManager()

        self.current_sentence = []
        self.connected_port = None
        self._char_count = 0
        self._port_map = {}

        # UI references (set during build)
        self.port_dropdown = None
        self.baud_dropdown = None
        self.connect_btn = None
        self.dot_container = None
        self.conn_label = None
        self.mode_label = None
        self.typed_count = None
        self.buffer_text = None
        self.log_panel = None

    def build(self):
        page = self.page
        page.title = "Braillex"
        page.theme_mode = ft.ThemeMode.DARK
        page.theme = get_theme()
        page.bgcolor = BG
        page.padding = 0

        # ── Top bar ──
        topbar = ft.Container(
            height=56,
            bgcolor=BG,
            padding=ft.padding.symmetric(horizontal=PADDING_LG),
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("\u2803", size=24, color=ACCENT),
                            ft.Text(
                                "B R A I L L E X",
                                size=14,
                                weight=ft.FontWeight.W_600,
                                color=TEXT,
                            ),
                            ft.Text(
                                "bluetooth braille companion",
                                size=FONT_SIZE_SMALL,
                                color=TEXT3,
                            ),
                        ],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.START,
                    ),
                    self._build_dep_badges(),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        sep = ft.Container(height=1, bgcolor=BORDER)

        # ── Main body ──
        # Get ports for initial load
        ports = [f"{d} \u2014 {n}" for d, n in get_all_com_ports()]
        self._port_map = {f"{d} \u2014 {n}": d for d, n in get_all_com_ports()}

        # Build panels
        conn_card, self.port_dropdown, self.baud_dropdown, self.connect_btn = (
            build_connection_panel(
                on_connect=self._toggle_connect,
                on_scan=self._scan_ports,
                on_auto_detect=self._auto_detect,
                ports=ports,
                baud_rates=["9600", "19200", "38400", "57600", "115200"],
            )
        )

        (
            status_card,
            self.dot_container,
            self.conn_label,
            self.mode_label,
            self.typed_count,
        ) = build_status_panel()

        supported_langs = [
            self.kbd_layout.layout_map.get(c, "Unknown")
            for c in self.tts.get_supported_languages()
        ]
        voice_card = build_voice_panel(
            on_toggle=self._toggle_voice,
            on_lang_change=self._on_language_change,
            on_rate_change=self._on_rate_change,
            on_test=self._test_voice,
            supported_langs=supported_langs,
            tts_available=PYTTSX3_OK,
        )

        sentence_card, self.buffer_text = build_sentence_panel(
            on_clear=self._clear_sentence,
        )

        debug_card = build_debug_panel(
            on_debug=self._send_debug_command,
            on_battery=self._send_battery_command,
        )

        # Left column (sidebar)
        left_column = ft.Column(
            controls=[
                conn_card,
                status_card,
                voice_card,
                sentence_card,
                debug_card,
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            width=280,
        )

        # Right column — log
        self.log_panel = LogPanel()

        log_header = ft.Row(
            controls=[
                ft.Text(
                    "EVENT LOG",
                    size=FONT_SIZE_SMALL,
                    weight=ft.FontWeight.W_600,
                    color=TEXT3,
                ),
                ft.TextButton(
                    content=ft.Text("Clear Log"),
                    on_click=self._clear_log,
                    style=ft.ButtonStyle(color=TEXT2),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        right_column = ft.Column(
            controls=[
                log_header,
                self.log_panel.container,
            ],
            expand=True,
            spacing=6,
        )

        body = ft.Container(
            expand=True,
            padding=PADDING_LG,
            content=ft.Row(
                controls=[
                    right_column,
                    left_column,
                ],
                spacing=16,
                expand=True,
            ),
        )

        # ── Bottom bar ──
        bottom_sep = ft.Container(height=1, bgcolor=BORDER)
        bottom_bar = ft.Container(
            height=32,
            bgcolor=BG,
            padding=ft.padding.symmetric(horizontal=PADDING_LG),
            content=ft.Row(
                controls=[
                    ft.Text("Not connected", size=FONT_SIZE_SMALL, color=TEXT3),
                    self._build_install_hint(),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        # Assemble page
        page.add(
            topbar,
            sep,
            body,
            bottom_sep,
            bottom_bar,
        )

        # Log startup messages
        self.log_panel.log("Braillex v2 started. Connect your HC-06 device.", "info")
        if not PYNPUT_OK:
            self.log_panel.log("pynput not found — run: pip install pynput", "warn")
        if not PYTTSX3_OK:
            self.log_panel.log("pyttsx3 not found — run: pip install pyttsx3", "warn")
        else:
            self.log_panel.log("Voice assistance is ready.", "ok")

        # Start event polling
        self._poll_events()

        page.update()

    def _build_dep_badges(self):
        badges = []
        if not PYNPUT_OK:
            badges.append(
                ft.Container(
                    bgcolor=RED_DIM,
                    border_radius=6,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    content=ft.Text("pynput missing", size=9, color=RED),
                )
            )
        if not PYTTSX3_OK:
            badges.append(
                ft.Container(
                    bgcolor=RED_DIM,
                    border_radius=6,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    content=ft.Text("pyttsx3 missing", size=9, color=RED),
                )
            )
        return ft.Row(controls=badges, spacing=6)

    def _build_install_hint(self):
        missing = []
        if not PYNPUT_OK:
            missing.append("pynput")
        if not PYTTSX3_OK:
            missing.append("pyttsx3")
        if missing:
            return ft.Text(
                f"Install: {', '.join(missing)}", size=FONT_SIZE_SMALL, color=ORANGE
            )
        return ft.Text("", size=FONT_SIZE_SMALL)

    # ── Port scanning ──────────────────────────────────────────────────────────

    def _scan_ports(self, e=None):
        ports = get_all_com_ports()
        values = [f"{d} \u2014 {n}" for d, n in ports] if ports else ["No ports found"]
        self.port_dropdown.options = [ft.dropdown.Option(v) for v in values]
        self._port_map = {f"{d} \u2014 {n}": d for d, n in ports}
        if values:
            self.port_dropdown.value = values[0]
        self.log_panel.log(f"Found {len(ports)} COM port(s).", "info")
        self.page.update()

    def _auto_detect(self, e=None):
        self.log_panel.log("Scanning for Braillex Bluetooth device\u2026", "info")
        self.page.update()

        def _do():
            port, name = find_braillex_com_port()
            self.event_q.put(("autodetect_result", (port, name)))

        threading.Thread(target=_do, daemon=True).start()

    # ── Connect / Disconnect ───────────────────────────────────────────────────

    def _toggle_connect(self, e=None):
        if self.worker and self.worker.is_alive():
            self._disconnect()
        else:
            self.worker = None
            self._connect()

    def _connect(self, e=None):
        if self.worker:
            try:
                self.worker.stop()
            except Exception:
                pass
            self.worker = None

        sel = self.port_dropdown.value
        port = self._port_map.get(sel)
        if not port:
            port = sel.split("\u2014")[0].strip() if "\u2014" in sel else sel
        if not port or port == "No ports found":
            self._show_snack("Please select a COM port.", ORANGE)
            self.connect_btn.content.value = "Connect"
            self.page.update()
            return

        baud = int(self.baud_dropdown.value)
        self.log_panel.log(f"Connecting to {port} @ {baud} baud\u2026", "info")

        self.dot_container.bgcolor = ORANGE
        self.conn_label.value = "Connecting\u2026"
        self.conn_label.color = ORANGE
        self.connect_btn.content.value = "Disconnect"

        self.worker = SerialWorker(port, baud, self.event_q)
        self.worker.start()
        self.page.update()

    def _disconnect(self, e=None):
        if self.worker:
            try:
                self.worker.stop()
            except Exception:
                pass
            self.worker = None
        self.connect_btn.content.value = "Connect"
        self.page.update()

    # ── Event polling ──────────────────────────────────────────────────────────

    def _poll_events(self):
        try:
            while True:
                event, payload = self.event_q.get_nowait()
                self._handle_event(event, payload)
        except queue.Empty:
            pass

        # Re-schedule
        threading.Timer(0.05, self._poll_events_safe).start()

    def _poll_events_safe(self):
        try:
            self._poll_events()
        except Exception:
            pass

    def _handle_event(self, event, payload):
        if event == "connected":
            self.connected_port = payload
            self.dot_container.bgcolor = GREEN
            self.conn_label.value = f"Connected: {payload}"
            self.conn_label.color = GREEN
            self.connect_btn.content.value = "Disconnect"
            self.log_panel.log(f"Connected to {payload}", "ok")
            self._show_snack(f"Connected to {payload}", GREEN)

        elif event == "disconnected":
            self.connected_port = None
            self.worker = None
            self.dot_container.bgcolor = TEXT3
            self.conn_label.value = "Disconnected"
            self.conn_label.color = TEXT3
            self.connect_btn.content.value = "Connect"
            self.log_panel.log("Disconnected.", "warn")
            self._show_snack("Disconnected", ORANGE)

        elif event == "error":
            self.connected_port = None
            self.worker = None
            self.dot_container.bgcolor = RED
            self.conn_label.value = "Error"
            self.conn_label.color = RED
            self.connect_btn.content.value = "Connect"
            self.log_panel.log(f"Serial error: {payload}", "err")
            self.log_panel.log("Ready to retry. Click Connect to try again.", "info")
            self._show_snack(f"Error: {payload}", RED)

        elif event == "data":
            self._process_data(payload)

        elif event == "autodetect_result":
            port, name = payload
            if port:
                self.log_panel.log(f"Found: {name} \u2192 {port}", "ok")
                label = f"{port} \u2014 {name}"
                found = False
                for opt in self.port_dropdown.options:
                    if port in opt.key:
                        self.port_dropdown.value = opt.key
                        found = True
                        break
                if not found:
                    self.port_dropdown.options.append(ft.dropdown.Option(label))
                    self.port_dropdown.value = label
                    self._port_map[label] = port
                self._show_snack(f"Auto-detected: {port}", GREEN)
            else:
                self.log_panel.log(
                    "No Braillex device found. Try manual selection.", "warn"
                )
                self._show_snack("Device not found", ORANGE)

        self.page.update()

    # ── Data processing ────────────────────────────────────────────────────────

    def _process_data(self, line):
        if line == "BS":
            self.log_panel.log("\u2190 Backspace", "cmd")
            self._announce("Backspace")
            self.injector.backspace()
            if self.current_sentence:
                self.current_sentence.pop()
            update_sentence_display(self.buffer_text, self.current_sentence)
            return

        if line == "CLEAR":
            self.log_panel.log("\u2715 Clear All", "cmd")
            self._announce("Clear all")
            for _ in self.current_sentence:
                self.injector.backspace()
            self.current_sentence.clear()
            update_sentence_display(self.buffer_text, self.current_sentence)
            return

        if line == "SPACE":
            self.log_panel.log("\u2423 Space", "cmd")
            self._announce("Space")
            self.injector.space()
            self.current_sentence.append(" ")
            update_sentence_display(self.buffer_text, self.current_sentence)
            return

        if line == "OST":
            sentence = "".join(self.current_sentence).strip()
            self.log_panel.log(f"\u2192 OST: [{sentence}]", "cmd")
            self._announce(sentence, command="ost")
            text_to_type = self.tts.translate_text(sentence)
            if text_to_type != sentence:
                self.log_panel.log(f"   Translated to: [{text_to_type}]", "data")
            for _ in self.current_sentence:
                self.injector.backspace()
            self.injector.type_char(text_to_type)
            self.current_sentence.clear()
            update_sentence_display(self.buffer_text, self.current_sentence)
            return

        if line == "CST":
            sentence = "".join(self.current_sentence).strip()
            corrected, err = correct_text(sentence)
            if err:
                self.log_panel.log(f"Grammar correction error: {err}", "err")
                corrected = sentence
            self.log_panel.log(f"\u2192 CST original:  [{sentence}]", "cmd")
            self.log_panel.log(f"\u2192 CST corrected: [{corrected}]", "ok")
            self._announce(corrected, command="cst")
            text_to_type = self.tts.translate_text(corrected)
            if text_to_type != corrected:
                self.log_panel.log(f"   Translated to: [{text_to_type}]", "data")
            for _ in self.current_sentence:
                self.injector.backspace()
            self.injector.type_char(text_to_type)
            self.current_sentence.clear()
            update_sentence_display(self.buffer_text, self.current_sentence)
            return

        if line.startswith("Mode:"):
            mode = line.split(":", 1)[1].strip()
            mode_map = {
                "0": "lowercase",
                "1": "uppercase",
                "2": "numeric",
                "LOWERCASE": "lowercase",
                "UPPERCASE": "uppercase",
                "NUMERIC": "numeric",
            }
            mode_str = mode_map.get(mode, mode.lower())
            self.mode_label.value = mode_str
            self.log_panel.log(f"Mode \u2192 {mode_str}", "info")
            self._announce(f"Mode: {mode_str}")
            return

        if "Pattern:" in line and "\u2192" in line or "->" in line:
            sep = "\u2192" if "\u2192" in line else "->"
            parts = line.split(sep)
            ch = parts[1].strip() if len(parts) > 1 else ""
            if ch:
                self.log_panel.log(f"\u283f char: '{ch}'", "char")
                self._announce(ch, command="letter")
                self.injector.type_char(ch)
                self.current_sentence.append(ch)
                self._char_count += 1
                self.typed_count.value = str(self._char_count)
                update_sentence_display(self.buffer_text, self.current_sentence)
            return

        if len(line) == 1 and line.isprintable():
            self.log_panel.log(f"\u283f char: '{line}'", "char")
            self._announce(line, command="letter")
            self.injector.type_char(line)
            self.current_sentence.append(line)
            self._char_count += 1
            self.typed_count.value = str(self._char_count)
            update_sentence_display(self.buffer_text, self.current_sentence)
            return

        self.log_panel.log(f"raw: {line}", "data")

    # ── Voice ──────────────────────────────────────────────────────────────────

    def _announce(self, text, command="normal"):
        if not self.tts.enabled:
            return

        if command == "letter":
            announcement = f"{text}."
        elif command == "cst":
            announcement = f"Corrected. {text}"
        elif command == "ost":
            announcement = text
        else:
            announcement = text

        threading.Thread(
            target=self.tts.speak, args=(announcement,), daemon=True
        ).start()

    def _toggle_voice(self, e):
        self.tts.enabled = e.control.value
        status = "enabled" if self.tts.enabled else "disabled"
        self.log_panel.log(f"Voice assistance {status}", "info")
        self.page.update()

    def _on_language_change(self, e):
        lang_name = e.control.value
        lang_code = self.kbd_layout.get_layout_code(lang_name)

        if not self.tts.is_language_supported(lang_code):
            self.log_panel.log(
                f"Language {lang_name} not supported, reverting to English", "warn"
            )
            e.control.value = "English"
            self.tts.set_language("en")
            self.page.update()
            return

        success = self.tts.set_language(lang_code)
        if success:
            self.log_panel.log(f"Language set to {lang_name}", "ok")
        else:
            self.log_panel.log(
                f"Failed to set {lang_name}, reverting to English", "warn"
            )
            e.control.value = "English"
            self.tts.set_language("en")
        self.page.update()

    def _on_rate_change(self, e, rate_label):
        try:
            rate = int(float(e.control.value))
            self.tts.set_voice_rate(rate)
            rate_label.value = f"Speed: {rate}"
            rate_label.update()
        except Exception:
            pass

    def _test_voice(self, e=None):
        if not self.tts.enabled:
            self._show_snack("Voice assistance is disabled.", ORANGE)
            return
        threading.Thread(
            target=self.tts.speak, args=("Voice assistance test. A B C.",), daemon=True
        ).start()
        self.log_panel.log("Playing voice test\u2026", "info")

    # ── Sentence buffer ────────────────────────────────────────────────────────

    def _clear_sentence(self, e=None):
        self.current_sentence.clear()
        update_sentence_display(self.buffer_text, self.current_sentence)
        self.log_panel.log("Sentence buffer cleared.", "info")
        self.page.update()

    # ── Log ────────────────────────────────────────────────────────────────────

    def _clear_log(self, e=None):
        self.log_panel.clear()
        self.page.update()

    # ── Debug commands ─────────────────────────────────────────────────────────

    def _send_debug_command(self, e=None):
        if not self.worker or not self.worker.is_alive():
            self._show_snack("Not connected to device.", ORANGE)
            return
        if self.worker.send_command("debug"):
            self.log_panel.log("\u2192 Sent: debug", "cmd")
        else:
            self.log_panel.log("Failed to send debug command", "err")
        self.page.update()

    def _send_battery_command(self, e=None):
        if not self.worker or not self.worker.is_alive():
            self._show_snack("Not connected to device.", ORANGE)
            return
        if self.worker.send_command("battery"):
            self.log_panel.log("\u2192 Sent: battery", "cmd")
        else:
            self.log_panel.log("Failed to send battery command", "err")
        self.page.update()

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _show_snack(self, message, color=ACCENT):
        """Show a toast notification."""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=TEXT, size=FONT_SIZE_LABEL),
            bgcolor=color,
            duration=2500,
        )
        self.page.snack_bar.open = True
        self.page.update()
