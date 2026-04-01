import flet as ft
from ui.theme import *
from ui.components import section_card, secondary_button


def build_debug_panel(on_debug, on_battery):
    debug_btn = secondary_button(
        "Toggle Debug Mode",
        icon=ft.icons.Icons.BUG_REPORT_ROUNDED,
        on_click=on_debug,
        expand=True,
    )

    battery_btn = secondary_button(
        "Toggle Battery Monitor",
        icon=ft.icons.Icons.BATTERY_FULL_ROUNDED,
        on_click=on_battery,
        expand=True,
    )

    content = ft.Column(
        spacing=6,
        controls=[debug_btn, battery_btn],
    )

    return section_card("Device Debug", content)
