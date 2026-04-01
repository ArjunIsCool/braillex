import flet as ft
from ui.theme import *
from ui.components import section_card, action_button, secondary_button


def build_connection_panel(
    on_connect, on_scan, on_auto_detect, ports: list[str], baud_rates: list[str]
):
    port_dropdown = ft.Dropdown(
        label="COM Port",
        options=[ft.dropdown.Option(p) for p in ports]
        if ports
        else [ft.dropdown.Option("No ports found")],
        value=ports[0] if ports else "No ports found",
        text_size=FONT_SIZE_LABEL,
        bgcolor=BG2,
        border_color=BORDER,
        focused_border_color=ACCENT,
        color=TEXT,
        label_style=ft.TextStyle(color=TEXT2, size=FONT_SIZE_SMALL),
        dense=True,
        expand=True,
    )

    baud_dropdown = ft.Dropdown(
        label="Baud Rate",
        options=[ft.dropdown.Option(b) for b in baud_rates],
        value="9600",
        text_size=FONT_SIZE_LABEL,
        bgcolor=BG2,
        border_color=BORDER,
        focused_border_color=ACCENT,
        color=TEXT,
        label_style=ft.TextStyle(color=TEXT2, size=FONT_SIZE_SMALL),
        dense=True,
        width=120,
    )

    connect_btn = action_button(
        "Connect",
        icon=ft.icons.Icons.CABLE_ROUNDED,
        on_click=on_connect,
        expand=True,
        bgcolor=ACCENT,
        color=BG,
    )

    scan_row = ft.Row(
        controls=[
            port_dropdown,
            secondary_button(
                "",
                icon=ft.icons.Icons.REFRESH_ROUNDED,
                on_click=on_scan,
                width=40,
                height=48,
            ),
        ],
        spacing=6,
    )

    baud_row = ft.Row(
        controls=[
            baud_dropdown,
            secondary_button(
                "Auto-detect",
                icon=ft.icons.Icons.BLUETOOTH_SEARCHING_ROUNDED,
                on_click=on_auto_detect,
                expand=True,
            ),
        ],
        spacing=6,
    )

    content = ft.Column(
        spacing=8,
        controls=[scan_row, baud_row, connect_btn],
    )

    return (
        section_card("Connection", content),
        port_dropdown,
        baud_dropdown,
        connect_btn,
    )
