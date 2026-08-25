import flet as ft
from database.db import ChatBotDatabase
import inspect
import os

from flet.auth.providers import GoogleOAuthProvider
from screens.captcha import generate_captcha


# =========================================================
# LOGIN SCREEN
# =========================================================

def LoginScreen(page: ft.Page):

    from screens.register import Register
    from screens.home import HomeScreen

    # -----------------------------------------------------
    # Clean old screen
    # -----------------------------------------------------

    page.clean()
    page.appbar = None
    page.drawer = None

    # -----------------------------------------------------
    # EMAIL
    # -----------------------------------------------------

    email = ft.TextField(
        hint_text="Enter your email...",
        label="Email ID",
        width=320,
        prefix_icon=ft.Icons.EMAIL,
    )

    # -----------------------------------------------------
    # PASSWORD
    # -----------------------------------------------------

    password = ft.TextField(
        hint_text="Enter your password...",
        label="Password",
        width=320,
        can_reveal_password=True,
        prefix_icon=ft.Icons.LOCK,
        password=True,
    )

    # -----------------------------------------------------
    # MESSAGE
    # -----------------------------------------------------

    message = ft.Text(
        "",
        color="red",
        size=14,
        selectable=True,
    )

    # =====================================================
    # CAPTCHA
    # =====================================================

    captcha_state = {
        "text": ""
    }

    captcha_image = ft.Image(
        src="",
        width=200,
        height=70,
        border_radius=8,
        fit=ft.BoxFit.CONTAIN,
    )

    captcha_answer = ft.TextField(
        hint_text="Type the letters/numbers above...",
        label="CAPTCHA answer",
        width=250,
        prefix_icon=ft.Icons.SHIELD_OUTLINED,
    )

    def refresh_captcha(e=None):

        try:
            text, b64 = generate_captcha()

            captcha_state["text"] = text

            captcha_image.src = b64
            captcha_answer.value = ""

            page.update()

        except Exception as ex:

            captcha_state["text"] = ""

            message.value = f"CAPTCHA error: {ex}"
            message.color = "red"

            page.update()

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

    # Generate first CAPTCHA
    refresh_captcha()

    # =====================================================
    # COMPLETE LOGIN
    # =====================================================

    async def complete_login(user_id, name):

        try:

            # -------------------------------------------------
            # SAVE LOGIN SESSION
            # -------------------------------------------------

            storage = getattr(
                page,
                "shared_preferences",
                getattr(page, "client_storage", None),
            )

            if storage is not None:

                try:

                    if hasattr(storage, "set_async"):

                        await storage.set_async(
                            "is_logged_in",
                            "true",
                        )

                        await storage.set_async(
                            "user_id",
                            str(user_id),
                        )

                        await storage.set_async(
                            "name",
                            str(name),
                        )

                    else:

                        storage.set(
                            "is_logged_in",
                            "true",
                        )

                        storage.set(
                            "user_id",
                            str(user_id),
                        )

                        storage.set(
                            "name",
                            str(name),
                        )

                except Exception as storage_error:

                    print(
                        "Storage error:",
                        storage_error,
                    )

            # -------------------------------------------------
            # OPEN HOME SCREEN
            # -------------------------------------------------

            page.clean()

            if inspect.iscoroutinefunction(HomeScreen):

                await HomeScreen(
                    page,
                    int(user_id),
                    name,
                )

            else:

                result = HomeScreen(
                    page,
                    int(user_id),
                    name,
                )

                if inspect.iscoroutine(result):

                    await result

            # -------------------------------------------------
            # UPDATE PAGE
            # -------------------------------------------------

            if hasattr(page, "update_async"):

                await page.update_async()

            else:

                page.update()

        except Exception as ex:

            message.value = f"Login error: {ex}"
            message.color = "red"

            page.update()

    # =====================================================
    # EMAIL / PASSWORD LOGIN
    # =====================================================

    async def login(e):

        email_value = email.value.strip()
        password_value = password.value.strip()

        # -------------------------------------------------
        # EMPTY CHECK
        # -------------------------------------------------

        if not email_value or not password_value:

            message.value = (
                "Please enter email and password."
            )

            message.color = "red"

            page.update()

            return

        # -------------------------------------------------
        # CAPTCHA CHECK
        # -------------------------------------------------

        entered_captcha = (
            captcha_answer.value.strip()
        )

        correct_captcha = (
            captcha_state["text"].strip()
        )

        if (
            not entered_captcha
            or entered_captcha.upper()
            != correct_captcha.upper()
        ):

            message.value = (
                "Incorrect CAPTCHA. Please try again."
            )

            message.color = "red"

            refresh_captcha()

            page.update()

            return

        # -------------------------------------------------
        # DATABASE LOGIN
        # -------------------------------------------------

        try:

            db = ChatBotDatabase()

            user = db.login_user(
                email_value,
                password_value,
            )

            # -------------------------------------------------
            # LOGIN SUCCESS
            # -------------------------------------------------

            if user:

                user_id = user["user_id"]
                name = user["name"]

                print(
                    "User ID:",
                    user_id,
                )

                print(
                    "User Name:",
                    name,
                )

                await complete_login(
                    user_id,
                    name,
                )

                return

            # -------------------------------------------------
            # LOGIN FAILED
            # -------------------------------------------------

            else:

                message.value = (
                    "Invalid email or password."
                )

                message.color = "red"

                refresh_captcha()

                page.update()

                return

        except Exception as ex:

            message.value = (
                f"Login error: {ex}"
            )

            message.color = "red"

            page.update()

            return

    # =====================================================
    # GOOGLE OAUTH CONFIGURATION
    # =====================================================

    google_client_id = os.getenv(
        "GOOGLE_CLIENT_ID"
    )

    google_client_secret = os.getenv(
        "GOOGLE_CLIENT_SECRET"
    )

    # IMPORTANT:
    # Render production callback URL
    google_redirect_url = os.getenv(
        "OAUTH_REDIRECT_URL",
        "https://1tp.onrender.com",
    )

    print(
        "Google Client ID configured:",
        bool(google_client_id),
    )

    print(
        "Google Client Secret configured:",
        bool(google_client_secret),
    )

    print(
        "Google Redirect URL:",
        google_redirect_url,
    )

    google_provider = None

    # -----------------------------------------------------
    # CREATE GOOGLE PROVIDER
    # -----------------------------------------------------

    if (
        google_client_id
        and google_client_secret
    ):

        try:

            google_provider = GoogleOAuthProvider(

                client_id=google_client_id,

                client_secret=google_client_secret,

                redirect_url=google_redirect_url,
            )

            print(
                "Google OAuth provider created."
            )

        except Exception as ex:

            print(
                "Google provider error:",
                ex,
            )

            google_provider = None

    # =====================================================
    # GOOGLE LOGIN CALLBACK
    # =====================================================

    async def on_google_login(e: ft.LoginEvent):

        try:

            # -------------------------------------------------
            # GOOGLE AUTH ERROR
            # -------------------------------------------------

            if e.error:

                message.value = (
                    "Google login failed: "
                    f"{e.error_description or e.error}"
                )

                message.color = "red"

                page.update()

                return

            # -------------------------------------------------
            # GET GOOGLE USER
            # -------------------------------------------------

            google_user = page.auth.user

            if not google_user:

                message.value = (
                    "Google account information "
                    "was not received."
                )

                message.color = "red"

                page.update()

                return

            google_email = google_user.get(
                "email"
            )

            google_name = google_user.get(
                "name"
            )

            # -------------------------------------------------
            # VALIDATE GOOGLE EMAIL
            # -------------------------------------------------

            if not google_email:

                message.value = (
                    "Google did not provide an email address."
                )

                message.color = "red"

                page.update()

                return

            if not google_name:

                google_name = (
                    google_email
                    .split("@")[0]
                )

            # -------------------------------------------------
            # DATABASE
            # -------------------------------------------------

            db = ChatBotDatabase()

            existing_user = (
                db.get_user_by_email(
                    google_email
                )
            )

            # -------------------------------------------------
            # EXISTING USER
            # -------------------------------------------------

            if existing_user:

                user_id = existing_user[
                    "user_id"
                ]

                name = existing_user[
                    "name"
                ]

            # -------------------------------------------------
            # NEW GOOGLE USER
            # -------------------------------------------------

            else:

                user_id = (
                    db.register_google_user(
                        google_name,
                        google_email,
                    )
                )

                name = google_name

            # -------------------------------------------------
            # LOGIN
            # -------------------------------------------------

            await complete_login(
                user_id,
                name,
            )

        except Exception as ex:

            print(
                "Google login error:",
                ex,
            )

            message.value = (
                f"Google login error: {ex}"
            )

            message.color = "red"

            page.update()

    # =====================================================
    # REGISTER GOOGLE LOGIN CALLBACK
    # =====================================================

    page.on_login = on_google_login

    # =====================================================
    # GOOGLE BUTTON CLICK
    # =====================================================

    def google_login_click(e):

        if google_provider is None:

            message.value = (
                "Google login is not configured. "
                "Check GOOGLE_CLIENT_ID and "
                "GOOGLE_CLIENT_SECRET."
            )

            message.color = "red"

            page.update()

            return

        try:

            page.login(
                google_provider
            )

        except Exception as ex:

            message.value = (
                f"Google login error: {ex}"
            )

            message.color = "red"

            page.update()

    # =====================================================
    # GOOGLE BUTTON
    # =====================================================

    google_button = ft.OutlinedButton(

        "Continue with Google",

        icon=ft.Icons.ACCOUNT_CIRCLE,

        width=320,

        height=40,

        on_click=google_login_click,
    )

    # =====================================================
    # LOGIN UI
    # =====================================================

    login_column = ft.Column(

        controls=[

            ft.Icon(
                ft.Icons.PERSON,
                size=90,
                color="blue",
            ),

            ft.Text(
                "Login to continue.",
                color="white",
                font_family="arial",
            ),

            # Google
            google_button,

            ft.Divider(),

            # Email
            email,

            # Password
            password,

            # CAPTCHA
            captcha_row,

            captcha_answer,

            # Error / status
            message,

            # Normal Login
            ft.OutlinedButton(

                "Login",

                width=320,

                height=40,

                on_click=login,
            ),

            # Register
            ft.OutlinedButton(

                "Go register",

                width=320,

                height=40,

                on_click=lambda e:
                    Register(page),
            ),
        ],

        horizontal_alignment=(
            ft.CrossAxisAlignment.CENTER
        ),

        alignment=(
            ft.MainAxisAlignment.CENTER
        ),
    )

    # =====================================================
    # ADD TO PAGE
    # =====================================================

    page.add(
        login_column
    )

    page.update()
