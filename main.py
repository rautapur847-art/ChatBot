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
    
    # 🌟 सुधार: SharedPreferences की जगह सर्वर-फ्रेंडली client_storage का उपयोग करें
    user_logged_in = await page.client_storage.get_async("is_logged_in")
    
    if user_logged_in == "true": 
        user_id = await page.client_storage.get_async("user_id")
        name = await page.client_storage.get_async("name")
        HomeScreen(page, int(user_id), name)
    else:
        LoginScreen(page)

    page.update()

# modern Flet 1.0 run command
ft.run(main, view=ft.AppView.WEB_BROWSER)
