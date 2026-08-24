import flet as ft


def AboutScreen(page: ft.Page,user_id,name):
    page.clean()
    from screens.setting import SettingScreen
    

    page.theme_mode = ft.ThemeMode.DARK

    page.appbar = ft.AppBar(
        leading=ft.IconButton(
            ft.Icons.ARROW_BACK,
            tooltip="Setting",
            on_click=lambda e: SettingScreen(page,user_id,name),
        ),
        title=ft.Text("About", color="white", weight=ft.FontWeight.BOLD),
        center_title=True,
        bgcolor=ft.Colors.TRANSPARENT,
    )

    content = ft.Column(
        controls=[
            ft.Container(height=10),
            ft.Container(
                content=ft.Icon(ft.Icons.SMART_TOY_OUTLINED,color="blue", size=64),
                
            ),
            ft.Container(
                content=ft.Text(
                    spans=[
                        ft.TextSpan("Chat", style=ft.TextStyle(color="red", weight=ft.FontWeight.BOLD, size=26)),
                        ft.TextSpan("Bot", style=ft.TextStyle(color="blue", weight=ft.FontWeight.BOLD, size=26)),
                    ]
                ),
                
            ),
            ft.Container(
                content=ft.Text("Version 1.0.0", color=ft.Colors.WHITE_54, size=13),
                
                margin=ft.Margin(0, 4, 0, 20),
            ),
            ft.Divider(color=ft.Colors.WHITE_24),
            ft.Container(
                content=ft.Text(
                    "ChatBot is a simple AI assistant built with Flet and Google's "
                    "Gemini API. Ask questions, attach a photo or file, or use your "
                    "voice — ChatBot will do its best to help.",
                    color="white",
                    size=14,
                ),
                padding=ft.Padding(4, 16, 4, 16),
            ),
            ft.Divider(color=ft.Colors.WHITE_24),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.CODE, color="blue"),
                title=ft.Text("Built with", color="white", weight=ft.FontWeight.BOLD),
                subtitle=ft.Text("Python + Mysql + Flet + Google Gemini", color=ft.Colors.WHITE_54),
            ),
            ft.Divider(),
             ft.ListTile(
                leading=ft.Icon(ft.Icons.CODE, color="blue"),
                title=ft.Text("Built by", color="white", weight=ft.FontWeight.BOLD),
                subtitle=ft.Text(" Er. Aman kumar. { using Cloude + Gemini + Chatgpt AI's } ", color=ft.Colors.WHITE),
            ),
            
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=6,
    )

    page.add(
        ft.Container(content=content, padding=20, expand=True),
    )
    page.update()