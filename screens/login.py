import flet as ft 
from database.db import ChatBotDatabase
import asyncio
import inspect

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
            
        try:
            db = ChatBotDatabase()
            user = db.login_user(email_value, password_value)

            if user:
                user_id = user["user_id"]
                name = user["name"]
                print("User ID:", user_id)
                print("User Name:", name)
                
                # 🌟 सुधार 1: टाइमआउट से बचने के लिए यूनिवर्सल 'shared_preferences' या 'client_storage' का उपयोग
                storage = getattr(page, "shared_preferences", getattr(page, "client_storage", None))
                if storage is not None:
                    if hasattr(storage, "set_async"):
                        await storage.set_async("is_logged_in", "true")
                        await storage.set_async("user_id", str(user_id))
                        await storage.set_async("name", str(name))
                    else:
                        storage.set("is_logged_in", "true")
                        storage.set("user_id", str(user_id))
                        storage.set("name", str(name))
                
                # 🌟 सुधार 2: स्क्रीन कंट्रोल्स साफ़ करें और होम स्क्रीन को सुरक्षित रूप से कॉल करें
                page.controls.clear()
                
                if inspect.iscoroutinefunction(HomeScreen):
                    await HomeScreen(page, int(user_id), name)
                else:
                    HomeScreen(page, int(user_id), name)
                
                # स्क्रीन को सुरक्षित अपडेट करें
                if hasattr(page, "update_async"):
                    await page.update_async()
                else:
                    page.update()
            else:
                message.value = "Invalid email and password"
                message.color = "red"
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
               email, password, message,
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
