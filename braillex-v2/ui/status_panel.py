import flet as ft
from ui.theme import *
from ui.components import section_card


def build_status_panel():
    """Build the device status panel."""

    dot_container = ft.Container(
        width=12,
        height=12,
        border_radius=6,
        bgcolor=TEXT3,
        animate=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
    )

    conn_label = ft.Text(
        "Disconnected",
        size=FONT_SIZE_SMALL,
        color=TEXT3,
    )

    mode_label = ft.Text(
        "lowercase",
        size=FONT_SIZE_SMALL,
        color=ACCENT2,
        font_family="Consolas",
    )

    typed_count = ft.Text(
        "0",
        size=FONT_SIZE_SMALL,
        color=GREEN,
        font_family="Consolas",
    )

    content = ft.Column(
        spacing=6,
        controls=[
            ft.Row(
                controls=[dot_container, conn_label],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Row(
                controls=[
                    ft.Text("Mode:", size=FONT_SIZE_SMALL, color=TEXT3),
                    mode_label,
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Row(
                controls=[
                    ft.Text("Typed:", size=FONT_SIZE_SMALL, color=TEXT3),
                    typed_count,
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        ],
    )

    return (
        section_card("Status", content),
        dot_container,
        conn_label,
        mode_label,
        typed_count,
    )
