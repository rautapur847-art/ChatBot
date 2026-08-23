import flet as ft


def SettingScreen(page: ft.Page,user_id,user_name):

    page.clean()
    from screens.home import HomeScreen
    from screens.about import AboutScreen
    from screens.help_support import HelpSupportScreen
    from screens.privacy import PrivacyScreen

    page.theme_mode = ft.ThemeMode.DARK

    page.appbar = ft.AppBar(
        leading=ft.IconButton(
            ft.Icons.ARROW_BACK,
            tooltip="Home",
            on_click=lambda e: HomeScreen(page,user_id,user_name),
        ),
        title=ft.Text("Settings", color="white", weight=ft.FontWeight.BOLD),
        center_title=True,
        bgcolor=ft.Colors.TRANSPARENT,
    )

    content = ft.Column(
        controls=[
            ft.Container(height=6),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.INFO_OUTLINE, color="blue"),
                title=ft.Text("About", color="white", weight=ft.FontWeight.BOLD),
                subtitle=ft.Text("App version, credits", color=ft.Colors.WHITE_54),
                trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.WHITE_54),
                on_click=lambda e: AboutScreen(page,user_id,user_name),
            ),
            ft.Divider(color=ft.Colors.WHITE_24),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.HELP_OUTLINE, color="blue"),
                title=ft.Text("Help & Support", color="white", weight=ft.FontWeight.BOLD),
                subtitle=ft.Text("FAQs, contact support", color=ft.Colors.WHITE_54),
                trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.WHITE_54),
                on_click=lambda e: HelpSupportScreen(page,user_id,user_name),
                
            ),
            ft.Divider(color=ft.Colors.WHITE_24),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.PRIVACY_TIP_OUTLINED, color="blue"),
                title=ft.Text("Privacy Policy", color="white", weight=ft.FontWeight.BOLD),
                subtitle=ft.Text("How your data is used", color=ft.Colors.WHITE_54),
                trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT, color=ft.Colors.WHITE_54),
                on_click=lambda e: PrivacyScreen(page,user_id,user_name),
            ),
            ft.Divider(color=ft.Colors.WHITE_24),
        ],
        spacing=0,
    )

    page.add(
        ft.Container(content=content, padding=10, expand=True),
    )
    page.update()