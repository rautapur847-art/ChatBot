import flet as ft
import random
import string
import time
import asyncio
from database.db import ChatBotDatabase
from screens.help_support import _send_email  # reuses the Resend sender already set up

OTP_EXPIRY_SECONDS = 300  # 5 minutes


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
        width=320,
    )

    email = ft.TextField(
        label="User email...",
        hint_text="Your email...",
        prefix_icon=ft.Icons.EMAIL,
        width=320,
    )

    mobile = ft.TextField(
        label="User mobile...",
        hint_text="Your mobile...",
        prefix_icon=ft.Icons.PHONE,
        width=320,
    )

    password = ft.TextField(
        label="User password...",
        hint_text="Your password...",
        prefix_icon=ft.Icons.PASSWORD,
        password=True,
        can_reveal_password=True,
        width=320,
    )

    confirm_password = ft.TextField(
        label="Confirm password...",
        hint_text="Confirm your password...",
        prefix_icon=ft.Icons.PASSWORD,
        password=True,
        can_reveal_password=True,
        width=320,
    )

    otp_field = ft.TextField(
        label="Enter OTP",
        hint_text="6-digit code from your email",
        width=320,
        visible=False,
    )
    otp_status = ft.Text("", size=12)

    message = ft.Text("", size=14)

    # OTP state — kept in a dict so nested async functions can mutate it
    # via closure without needing a pile of `nonlocal` declarations.
    otp_state = {"code": None, "sent_at": 0, "locked_email": None}

    def generate_otp():
        return "".join(random.choices(string.digits, k=6))

    async def send_otp_click(e):
        user_email = email.value.strip()
        if not user_email or "@" not in user_email:
            message.value = "Enter a valid email first."
            message.color = "red"
            page.update()
            return

        send_otp_button.disabled = True
        otp_status.value = "Sending OTP..."
        otp_status.color = "blue"
        page.update()

        otp = generate_otp()
        try:
            await asyncio.to_thread(
                _send_email,
                "ChatBot — Your verification code",
                f"Your OTP for ChatBot registration is: {otp}\nIt expires in 5 minutes.",
                user_email,
            )
            otp_state["code"] = otp
            otp_state["sent_at"] = time.time()
            otp_state["locked_email"] = user_email

            otp_field.visible = True
            otp_field.value = ""
            otp_status.value = f"OTP sent to {user_email}. Check your inbox."
            otp_status.color = "green"
            # Lock the email field so the OTP stays tied to this address —
            # changing it after sending would let someone verify an OTP
            # sent to one address, then register with a different one.
            email.disabled = True
        except Exception as ex:
            otp_status.value = f"Failed to send OTP: {ex}"
            otp_status.color = "red"
        finally:
            send_otp_button.disabled = False
            page.update()

    send_otp_button = ft.OutlinedButton(
        "Send OTP", width=320, height=40, on_click=send_otp_click
    )

    async def register_user(e):

        user_name = name.value.strip()
        user_email = email.value.strip()
        user_mobile = mobile.value.strip()
        user_password = password.value
        confirm = confirm_password.value
        entered_otp = otp_field.value.strip()

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

        if otp_state["code"] is None:
            message.value = "Click 'Send OTP' and verify your email first."
            message.color = "red"
            page.update()
            return

        if user_email != otp_state["locked_email"]:
            message.value = "Email changed after the OTP was sent — click Send OTP again."
            message.color = "red"
            page.update()
            return

        if time.time() - otp_state["sent_at"] > OTP_EXPIRY_SECONDS:
            message.value = "OTP expired — click Send OTP again."
            message.color = "red"
            otp_state["code"] = None
            otp_field.visible = False
            email.disabled = False
            page.update()
            return

        if not entered_otp or entered_otp != otp_state["code"]:
            message.value = "Incorrect OTP."
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

            await asyncio.sleep(0.5)
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
                send_otp_button,
                otp_status,
                otp_field,
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
                    "Go Login", width=320, height=40,
                    on_click=lambda e: LoginScreen(page),
                ),
            ],

            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        )
    )

    page.update()
