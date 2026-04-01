import flet as ft
from ui.theme import *
from ui.components import section_card, action_button


def build_voice_panel(
    on_toggle,
    on_lang_change,
    on_rate_change,
    on_test,
    supported_langs: list[str],
    tts_available: bool,
):
    voice_switch = ft.Switch(
        label="Enable Voice",
        value=tts_available,
        on_change=on_toggle,
        active_color=ACCENT,
        active_track_color=ACCENT_DIM,
    )

    if not tts_available:
        voice_switch.disabled = True

    lang_dropdown = ft.Dropdown(
        label="Language",
        options=[ft.dropdown.Option(lang) for lang in sorted(supported_langs)]
        if supported_langs
        else [ft.dropdown.Option("English")],
        value="English",
        text_size=FONT_SIZE_LABEL,
        bgcolor=BG2,
        border_color=BORDER,
        focused_border_color=ACCENT,
        color=TEXT,
        label_style=ft.TextStyle(color=TEXT2, size=FONT_SIZE_SMALL),
        dense=True,
        on_select=on_lang_change,
    )

    rate_label = ft.Text("Speed: 150", size=FONT_SIZE_SMALL, color=TEXT3)

    rate_slider = ft.Slider(
        min=50,
        max=300,
        value=150,
        divisions=25,
        label="{value}",
        active_color=ACCENT,
        inactive_color=BORDER,
        thumb_color=ACCENT2,
        on_change=lambda e: on_rate_change(e, rate_label),
    )

    test_btn = action_button(
        "Test Voice",
        icon=ft.icons.Icons.VOLUME_UP_ROUNDED,
        on_click=on_test,
        expand=True,
        bgcolor=BG3,
        color=TEXT,
    )

    controls = [voice_switch]

    if not tts_available:
        controls.append(
            ft.Text(
                "Install pyttsx3 for voice support", size=FONT_SIZE_SMALL, color=ORANGE
            )
        )

    if len(supported_langs) <= 1:
        controls.append(
            ft.Text(
                "Install deep-translator for multilingual support",
                size=FONT_SIZE_SMALL,
                color=ORANGE,
            )
        )

    controls.extend([lang_dropdown, rate_label, rate_slider, test_btn])

    content = ft.Column(spacing=8, controls=controls)
    return section_card("Voice Settings", content)
