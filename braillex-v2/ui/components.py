import flet as ft
from datetime import datetime
from ui.theme import *


def status_dot(state="off", size=12):
    color_map = {
        "off": TEXT3,
        "connecting": ORANGE,
        "connected": GREEN,
        "error": RED,
    }
    color = color_map.get(state, TEXT3)

    return ft.Container(
        width=size,
        height=size,
        border_radius=size / 2,
        bgcolor=color,
        animate=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
    )


def section_card(title: str, content: ft.Control, width=None, expand=False):
    return ft.Container(
        width=width,
        expand=expand,
        bgcolor=BG3,
        border=ft.border.all(1, BORDER),
        border_radius=CARD_BORDER_RADIUS,
        padding=0,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        content=ft.Column(
            spacing=0,
            controls=[
                ft.Container(
                    padding=ft.padding.symmetric(
                        horizontal=PADDING_MD, vertical=PADDING_SM
                    ),
                    content=ft.Text(
                        title.upper(),
                        size=FONT_SIZE_SMALL,
                        weight=ft.FontWeight.W_600,
                        color=TEXT3,
                    ),
                ),
                ft.Container(
                    padding=ft.padding.all(PADDING_MD),
                    content=content,
                ),
            ],
        ),
    )


def action_button(
    text,
    icon=None,
    on_click=None,
    bgcolor=ACCENT,
    color=None,
    width=None,
    expand=False,
    height=40,
):
    if color is None:
        color = BG if bgcolor == ACCENT else TEXT
    return ft.ElevatedButton(
        content=ft.Text(text, size=FONT_SIZE_LABEL, weight=ft.FontWeight.W_500),
        icon=icon,
        icon_color=color,
        on_click=on_click,
        bgcolor=bgcolor,
        color=color,
        width=width,
        expand=expand,
        height=height,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=BORDER_RADIUS),
            elevation=0,
        ),
    )


def secondary_button(
    text, icon=None, on_click=None, width=None, expand=False, height=36
):
    return ft.OutlinedButton(
        content=ft.Text(text, size=FONT_SIZE_SMALL) if text else None,
        icon=icon,
        icon_color=TEXT2,
        on_click=on_click,
        width=width,
        expand=expand,
        height=height,
        style=ft.ButtonStyle(
            color=TEXT2,
            side=ft.BorderSide(1, BORDER),
            shape=ft.RoundedRectangleBorder(radius=BORDER_RADIUS),
        ),
    )


class LogPanel:
    def __init__(self):
        self.column = ft.Column(
            spacing=2,
            scroll=ft.ScrollMode.AUTO,
            auto_scroll=True,
        )
        self.container = ft.Container(
            expand=True,
            bgcolor=BG2,
            border=ft.border.all(1, BORDER),
            border_radius=CARD_BORDER_RADIUS,
            padding=PADDING_SM,
            content=self.column,
        )

    def log(self, msg, tag="info"):
        ts = datetime.now().strftime("%H:%M:%S")
        tag_colors = {
            "info": TEXT2,
            "ok": GREEN,
            "err": RED,
            "warn": ORANGE,
            "data": ACCENT2,
            "char": TEXT,
            "cmd": ORANGE,
        }
        color = tag_colors.get(tag, TEXT2)

        row = ft.Row(
            spacing=6,
            tight=True,
            controls=[
                ft.Text(
                    f"[{ts}]", size=FONT_SIZE_SMALL, color=TEXT3, font_family="Consolas"
                ),
                ft.Text(msg, size=FONT_SIZE_SMALL, color=color, font_family="Consolas"),
            ],
        )
        self.column.controls.append(row)

    def clear(self):
        self.column.controls.clear()
