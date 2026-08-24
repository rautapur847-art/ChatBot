import flet as ft 
import asyncio
from screens.home import HomeScreen
from screens.login import LoginScreen 

async def main(page: ft.Page):
    page.window.width = 360
    page.window.height = 700
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    
    # 🌟 बिल्कुल नया राउटिंग आर्किटेक्चर (No more blank screens)
    async def route_change(route):
        page.views.clear()
        
        storage = getattr(page, "shared_preferences", getattr(page, "client_storage", None))
        user_logged_in = "false"
        user_id = None
        name = None
        
        if storage is not None:
            if hasattr(storage, "get_async"):
                user_logged_in = await storage.get_async("is_logged_in")
                user_id = await storage.get_async("user_id")
                name = await storage.get_async("name")
            else:
                user_logged_in = storage.get("is_logged_in")
                user_id = storage.get("user_id")
                name = storage.get("name")

        # सुरक्षित चेक: अगर लॉग इन है तो होम व्यू, वरना लॉगिन व्यू
        if user_logged_in == "true" and user_id and name:
            # नया व्यू बनाकर उसमें होम स्क्रीन को लोड करें
            home_view = ft.View(route="/home")
            await HomeScreen(home_view, int(user_id), name)
            page.views.append(home_view)
        else:
            login_view = ft.View(route="/login")
            await LoginScreen(login_view)
            page.views.append(login_view)
            
        await page.update_async()

    page.on_route_change = route_change
    # ऐप शुरू होते ही राउट ट्रिगर करें
    await page.go_async(page.route)

# modern Flet 1.0 run command
ft.run(main, view=ft.AppView.WEB_BROWSER)
