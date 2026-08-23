import flet as ft
from database.db import ChatBotDatabase


def Register(page: ft.Page):
    from screens.login import LoginScreen

    page.clean()

    page.horizontal_alignment = ft.MainAxisAlignment.CENTER
    page.vertical_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 360
    page.window.height = 700

    name = ft.TextField(
        label="User name...",
        hint_text="User name...",
        prefix_icon=ft.Icons.PERSON,
    )

    email = ft.TextField(
        label="User email...",
        hint_text="Your email...",
        prefix_icon=ft.Icons.EMAIL,
    )

    mobile = ft.TextField(
        label="User mobile...",
        hint_text="Your mobile...",
        prefix_icon=ft.Icons.PHONE,
    )

    password = ft.TextField(
        label="User password...",
        hint_text="Your password...",
        prefix_icon=ft.Icons.PASSWORD,
        password=True,
        can_reveal_password=True,
    )

    confirm_password = ft.TextField(
        label="Confirm password...",
        hint_text="Confirm your password...",
        prefix_icon=ft.Icons.PASSWORD,
        password=True,
        can_reveal_password=True,
    )

    message = ft.Text(
        "",
        size=14,
    )

    async def register_user(e):

        user_name = name.value.strip()
        user_email = email.value.strip()
        user_mobile = mobile.value.strip()
        user_password = password.value
        confirm = confirm_password.value

        # Validation
        if not user_name or not user_email or not user_mobile:
            message.value = "Please fill all fields."
            message.color = "red"
            page.update()
            return

        if not user_password:
            message.value = "Please enter password."
            message.color = "red"
            page.update()
            return

        if user_password != confirm:
            message.value = "Passwords do not match."
            message.color = "red"
            page.update()
            return

        try:
            db = ChatBotDatabase()

            db.register_user(
                user_name,
                user_email,
                user_mobile,
                user_password,
            )

            message.value = "Registration successful!"
            message.color = "green"
            page.update()

            # Go to login
            await __import__("asyncio").sleep(0.5)
            LoginScreen(page)

        except Exception as ex:

            message.value = f"Registration error: {ex}"
            message.color = "red"
            page.update()

    page.add(
        ft.Column(
            [
                ft.Icon(
                    ft.Icons.PERSON_ADD,
                    size=90,
                    color="blue",
                ),

                ft.Text(
                    "If you already have an account, go to login.",
                    color="white",
                    font_family="arial",
                ),

                name,
                email,
                mobile,
                password,
                confirm_password,

                message,

                ft.OutlinedButton(
                    "Register",
                    width=320,
                    height=40,
                    on_click=register_user,
                ),

                ft.OutlinedButton(
                    "Go Login",
                    width=320,
                    height=40,
                    on_click=lambda e: LoginScreen(page),
                ),
            ],

            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )
    )

    page.update()