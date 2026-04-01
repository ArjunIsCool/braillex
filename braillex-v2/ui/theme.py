import flet as ft


# ─── Color Palette ────────────────────────────────────────────────────────────

BG = "#0D0D0F"
BG2 = "#131317"
BG3 = "#1A1A20"
BORDER = "#2A2A35"
ACCENT = "#7B6EFF"
ACCENT2 = "#B8ADFF"
ACCENT_DIM = "#3D3680"
GREEN = "#3DFF9A"
GREEN_DIM = "#1A4D35"
RED = "#FF5C5C"
RED_DIM = "#4D1A1A"
ORANGE = "#FFB347"
ORANGE_DIM = "#4D3A1A"
TEXT = "#E8E6FF"
TEXT2 = "#9490B8"
TEXT3 = "#5A5780"

# ─── Spacing ──────────────────────────────────────────────────────────────────

PADDING_SM = 8
PADDING_MD = 12
PADDING_LG = 16
BORDER_RADIUS = 10
CARD_BORDER_RADIUS = 12

# ─── Font Sizes ───────────────────────────────────────────────────────────────

FONT_SIZE_LABEL = 11
FONT_SIZE_BODY = 13
FONT_SIZE_SMALL = 10
FONT_SIZE_TITLE = 18
FONT_SIZE_HEADING = 14


def get_theme():
    """Return a configured ft.Theme for the app."""
    theme = ft.Theme(
        color_scheme_seed=ACCENT,
        visual_density=ft.VisualDensity.COMPACT,
        use_material3=True,
    )
    return theme
