import flet as ft


def open_add_dialog(page):

    def close_dialog(e):
        page.dialog.open = False
        page.update()

    def camera_click(e):
        print("Camera clicked")
        close_dialog(e)

    def photo_click(e):
        print("Photo clicked")
        close_dialog(e)

    def files_click(e):
        print("Files clicked")
        close_dialog(e)

    dialog = ft.AlertDialog(
        modal=True,

        title=ft.Text(
            "Add",
            weight=ft.FontWeight.BOLD,
        ),

        content=ft.Column(
            [
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.CAMERA_ALT),
                    title=ft.Text("Camera"),
                    on_click=camera_click,
                ),

                ft.ListTile(
                    leading=ft.Icon(ft.Icons.PHOTO),
                    title=ft.Text("Photo"),
                    on_click=photo_click,
                ),

                ft.ListTile(
                    leading=ft.Icon(ft.Icons.FILE_PRESENT),
                    title=ft.Text("Files"),
                    on_click=files_click,
                ),
            ],
            tight=True,
        ),

        actions=[
            ft.TextButton(
                "Cancel",
                on_click=close_dialog,
            )
        ],
    )

    page.dialog = dialog
    dialog.open = True
    page.update()
