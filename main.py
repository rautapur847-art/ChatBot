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
    
    # 🌟 बिल्कुल सटीक सुधार: Flet 1.0 के अनुसार Standalone SharedPreferences सर्विस बनाई
    prefs = ft.SharedPreferences()
    
    # Flet 1.0 में get_async नहीं, बल्कि सीधे await prefs.get() होता है
    user_logged_in = await prefs.get("is_logged_in")
    
    if user_logged_in == "true": # SharedPreferences हमेशा String स्टोर करता है
        user_id = await prefs.get("user_id")
        name = await prefs.get("name")
        HomeScreen(page, int(user_id), name)
    else:
        LoginScreen(page)

    page.update()

# modern Flet 1.0 run command
ft.run(main,view=ft.AppView.WEB_BROWSER)
