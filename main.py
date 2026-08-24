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
    
    # 🌟 जादुई सुधार: यह कोड नए (shared_preferences) और पुराने (client_storage) दोनों वर्ज़न को खुद ही संभाल लेगा
    storage = getattr(page, "shared_preferences", getattr(page, "client_storage", None))
    
    user_logged_in = None
    if storage is not None:
        # अगर वर्ज़न नया है तो get_async उपयोग होगा, पुराने में नॉर्मल get
        if hasattr(storage, "get_async"):
            user_logged_in = await storage.get_async("is_logged_in")
            user_id = await storage.get_async("user_id")
            name = await storage.get_async("name")
        else:
            user_logged_in = storage.get("is_logged_in")
            user_id = storage.get("user_id")
            name = storage.get("name")
            
    if user_logged_in == "true" and user_id and name: 
        HomeScreen(page, int(user_id), name)
    else:
        LoginScreen(page)

    page.update()

# modern Flet 1.0 run command
ft.run(main, view=ft.AppView.WEB_BROWSER)
