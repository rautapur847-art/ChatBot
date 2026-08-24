import flet as ft 
import asyncio
import inspect
from screens.home import HomeScreen
from screens.login import LoginScreen 

async def main(page: ft.Page):
    page.window.width = 360
    page.window.height = 700
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    
    storage = getattr(page, "shared_preferences", getattr(page, "client_storage", None))
    
    user_logged_in = "false"
    user_id = None
    name = None
    
    if storage is not None:
        try:
            user_logged_in = await storage.get_async("is_logged_in")
            user_id = await storage.get_async("user_id")
            name = await storage.get_async("name")
        except Exception:
            try:
                user_logged_in = await storage.get("is_logged_in")
                user_id = await storage.get("user_id")
                name = await storage.get("name")
            except Exception:
                user_logged_in = storage.get("is_logged_in")
                user_id = storage.get("user_id")
                name = storage.get("name")
            
    page.controls.clear()
    
    if user_logged_in == "true" and user_id and name: 
        if inspect.iscoroutinefunction(HomeScreen):
            await HomeScreen(page, int(user_id), name)
        else:
            res = HomeScreen(page, int(user_id), name)
            if inspect.iscoroutine(res):
                await res
    else:
        if inspect.iscoroutinefunction(LoginScreen):
            await LoginScreen(page)
        else:
            res = LoginScreen(page)
            if inspect.iscoroutine(res):
                await res

    if hasattr(page, "update_async"):
        await page.update_async()
    else:
        page.update()

# modern Flet 1.0 run command
ft.run(main, view=ft.AppView.WEB_BROWSER,assets_dir="assets")
