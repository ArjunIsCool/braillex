import flet as ft
from app import BraillexApp


def main(page: ft.Page):
    app = BraillexApp(page)
    app.build()


if __name__ == "__main__":
    ft.run(main)
