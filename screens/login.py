import flet as ft 
from database.db import ChatBotDatabase
import asyncio
import inspect
import os
from flet.auth.providers import GoogleOAuthProvider
from screens.captcha import generate_captcha

def LoginScreen(page: ft.Page):
    from screens.register import Register
    from screens.home import HomeScreen
    page.clean()
    
    page.appbar = None
    page.drawer = None
    
    email = ft.TextField(
        hint_text=" Enter your email...",
        label=" Email_id...",
        width=320,
        prefix_icon=ft.Icons.EMAIL
    )

    password = ft.TextField(
        hint_text=" Enter your password...",
        label=" Password...",
        width=320,
        can_reveal_password=True,
        prefix_icon=ft.Icons.LOCK,
        password=True
    )

    # ---- real image-based CAPTCHA (distorted text, PIL-generated) ----
    captcha_state = {"text": ""}

    captcha_image = ft.Image(
        src="",
        width=200,
        height=70,
        border_radius=8,
        fit=ft.BoxFit.CONTAIN,
    )
    captcha_answer = ft.TextField(
        hint_text="Type the letters/numbers above...",
        label=" CAPTCHA answer...",
        width=250,
        prefix_icon=ft.Icons.SHIELD_OUTLINED,
    )

    def refresh_captcha(e=None):
        # New image + text each time — so a wrong/expired attempt can't
        # just be retried against the same known answer.
        text, b64 = generate_captcha()
        captcha_state["text"] = text
        captcha_image.src = b64
        captcha_answer.value = ""
        page.update()

    refresh_captcha()

    captcha_row = ft.Row(
        controls=[
            captcha_image,
            ft.IconButton(
                icon=ft.Icons.REFRESH,
                icon_color="white",
                tooltip="Get a new CAPTCHA",
                on_click=refresh_captcha,
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=4,
    )
    
    message = ft.Text(
        "",
        color="red",
        size=14,
    )

    async def complete_login(user_id, name):
        """Shared by both email/password login and Google login — saves
        session storage and navigates to HomeScreen."""
        storage = getattr(page, "shared_preferences", getattr(page, "client_storage", None))
        if storage is not None:
            try:
                await storage.set_async("is_logged_in", "true")
                await storage.set_async("user_id", str(user_id))
                await storage.set_async("name", str(name))
            except Exception:
                await storage.set("is_logged_in", "true")
                await storage.set("user_id", str(user_id))
                await storage.set("name", str(name))

        page.controls.clear()

        if inspect.iscoroutinefunction(HomeScreen):
            await HomeScreen(page, int(user_id), name)
        else:
            res = HomeScreen(page, int(user_id), name)
            if inspect.iscoroutine(res):
                await res

        if hasattr(page, "update_async"):
            await page.update_async()
        else:
            page.update()

    async def login(e):
        email_value = email.value.strip()
        password_value = password.value.strip()
        
        if not email_value or not password_value:
            message.value = "Please enter email and password.."
            message.color = "red"
            page.update()
            return

        # ---- CAPTCHA check, before ever touching the database ----
        entered = captcha_answer.value.strip()
        if not entered or entered.upper() != captcha_state["text"].upper():
            message.value = "Incorrect CAPTCHA answer — try again."
            message.color = "red"
            refresh_captcha()
            page.update()
            return
            
        try:
            db = ChatBotDatabase()
            user = db.login_user(email_value, password_value)

            if user:
                print("User ID:", user["user_id"])
                print("User Name:", user["name"])
                await complete_login(user["user_id"], user["name"])
            else:
                # NOTE: the login query (email=%s AND password=%s) can't
                # tell us whether the email doesn't exist or the password
                # is wrong — only that the combination didn't match. A
                # single generic message here is both correct and safer
                # (not confirming to an attacker whether an email is
                # registered).
                message.value = "Invalid email or password."
                message.color = "red"
                refresh_captcha()
                page.update()

        except Exception as ex:
            message.value = f"Login error: {ex}"
            message.color = "red"
            message.selectable = True
            page.update()

    # ---- Google sign-in ----
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    google_redirect_url = os.getenv("OAUTH_REDIRECT_URL", "http://localhost:8550/oauth_callback")

    google_provider = None
    if google_client_id and google_client_secret:
        google_provider = GoogleOAuthProvider(
            client_id=google_client_id,
            client_secret=google_client_secret,
            redirect_url=google_redirect_url,
        )

    async def on_google_login(e: ft.LoginEvent):
        if e.error:
            message.value = f"Google login failed: {e.error_description or e.error}"
            message.color = "red"
            page.update()
            return

        google_user = page.auth.user
        google_email = google_user["email"]
        google_name = google_user.get("name") or google_email.split("@")[0]

        try:
            db = ChatBotDatabase()
            existing = db.get_user_by_email(google_email)
            if existing:
                user_id = existing["user_id"]
                name = existing["name"]
            else:
                # First time signing in with this Google account — create
                # an account for them automatically.
                user_id = db.register_google_user(google_name, google_email)
                name = google_name

            await complete_login(user_id, name)
        except Exception as ex:
            message.value = f"Google login error: {ex}"
            message.color = "red"
            page.update()

    page.on_login = on_google_login

    def google_login_click(e):
        if not google_provider:
            message.value = (
                "Google login isn't configured yet — add GOOGLE_CLIENT_ID "
                "and GOOGLE_CLIENT_SECRET to .env."
            )
            message.color = "red"
            page.update()
            return
        page.login(google_provider)

    google_button = ft.OutlinedButton(
        "Continue with Google",
        icon=ft.Icons.ACCOUNT_CIRCLE,
        width=320,
        height=40,
        on_click=google_login_click,
    )

    page.add( 
        ft.Column(
            [
               ft.Icon(ft.Icons.PERSON, size=90, color="blue"),
               ft.Text("login to continue.", color="white", font_family="arial"),
               google_button,
               ft.Divider(width=320),
               email, password,
               captcha_row, captcha_answer,
               message,
               ft.OutlinedButton(
                    "Login.",
                    width=320,
                    height=40,
                    on_click=login
                ),
               ft.OutlinedButton(
                    "Go register.", width=320, height=40,
                    on_click=lambda e: Register(page)
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )
    )
    
    page.update()
