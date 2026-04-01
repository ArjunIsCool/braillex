import flet as ft
from ui.theme import *
from ui.components import section_card, secondary_button


def build_sentence_panel(on_clear):
    buffer_text = ft.Text(
        "(empty)",
        size=FONT_SIZE_SMALL,
        color=TEXT3,
        font_family="Consolas",
        max_lines=3,
        overflow=ft.TextOverflow.ELLIPSIS,
    )

    hint_text = ft.Text(
        "OST = send original  |  CST = send corrected",
        size=9,
        color=TEXT3,
    )

    clear_btn = secondary_button(
        "Clear Buffer",
        icon=ft.icons.Icons.CLEAR_ALL_ROUNDED,
        on_click=on_clear,
        expand=True,
    )

    content = ft.Column(
        spacing=6,
        controls=[buffer_text, hint_text, clear_btn],
    )

    return section_card("Sentence Buffer", content), buffer_text


def update_sentence_display(buffer_text: ft.Text, sentence: list):
    s = "".join(sentence)
    if s:
        display = s if len(s) <= 40 else "\u2026" + s[-37:]
        buffer_text.value = display
        buffer_text.color = TEXT
    else:
        buffer_text.value = "(empty)"
        buffer_text.color = TEXT3
