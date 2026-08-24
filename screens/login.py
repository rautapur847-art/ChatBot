import flet as ft 
from database.db import ChatBotDatabase
import asyncio
import inspect
import random

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

    # ---- simple math CAPTCHA (no external service/dependency needed) ----
    captcha_state = {"a": 0, "b": 0}

    captcha_label = ft.Text("", color="white", weight=ft.FontWeight.BOLD)
    captcha_answer = ft.TextField(
        hint_text="Your answer...",
        label=" CAPTCHA answer...",
        width=320,
        prefix_icon=ft.Icons.SHIELD_OUTLINED,
    )

    def refresh_captcha():
        # New numbers each time — so a wrong/expired attempt can't just be
        # retried against the same known answer.
        captcha_state["a"] = random.randint(1, 9)
        captcha_state["b"] = random.randint(1, 9)
        captcha_label.value = f"Solve to continue: {captcha_state['a']} + {captcha_state['b']} = ?"
        captcha_answer.value = ""

    refresh_captcha()
    
    message = ft.Text(
        "",
        color="red",
        size=14,
    )

    async def login(e):
        email_value = email.value.strip()
        password_value = password.value.strip()
        
        if not email_value or not password_value:
            message.value = "Please enter email and password.."
            message.color = "red"
            page.update()
            return

        # ---- CAPTCHA check, before ever touching the database ----
        expected = captcha_state["a"] + captcha_state["b"]
        try:
            entered = int(captcha_answer.value.strip())
        except (TypeError, ValueError):
            entered = None

        if entered != expected:
            message.value = "Incorrect CAPTCHA answer — try again."
            message.color = "red"
            refresh_captcha()
            page.update()
            return
            
        try:
            db = ChatBotDatabase()
            user = db.login_user(email_value, password_value)

            if user:
                user_id = user["user_id"]
                name = user["name"]
                print("User ID:", user_id)
                print("User Name:", name)
                
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
                
    page.add( 
        ft.Column(
            [
               ft.Icon(ft.Icons.PERSON, size=90, color="blue"),
               ft.Text("login to continue.", color="white", font_family="arial"),
               email, password,
               captcha_label, captcha_answer,
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
