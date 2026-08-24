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
    
    # वर्ज़न की समस्या से बचने के लिए यूनिवर्सल स्टोरेज हैंडलर
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
            
    # पुरानी किसी भी स्क्रीन के कंट्रोल्स को पूरी तरह साफ़ करें
    page.controls.clear()
    
    # 🌟 बिल्कुल सटीक सुधार: बिना किसी 'go' या 'go_async' के सीधे स्क्रीन लोड करना
    if user_logged_in == "true" and user_id and name: 
        await HomeScreen(page, int(user_id), name) 
    else:
        await LoginScreen(page) 

    # वर्ज़न के अनुसार स्क्रीन को सही ढंग से अपडेट करना
    if hasattr(page, "update_async"):
        await page.update_async()
    else:
        page.update()

# modern Flet 1.0 run command
ft.run(main, view=ft.AppView.WEB_BROWSER)
