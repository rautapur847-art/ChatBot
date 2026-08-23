import flet as ft


def PrivacyScreen(page: ft.Page,user_id,user_name):
    page.clean()
    from screens.setting import SettingScreen

    page.theme_mode = ft.ThemeMode.DARK

    page.appbar = ft.AppBar(
        leading=ft.IconButton(
            ft.Icons.ARROW_BACK,
            tooltip="Setting",
            on_click=lambda e: SettingScreen(page,user_id,user_name),
        ),
        title=ft.Text("Privacy Policy", color="white", weight=ft.FontWeight.BOLD),
        center_title=True,
        bgcolor=ft.Colors.TRANSPARENT,
    )

    def section(title, body):
        return ft.Column(
            controls=[
                ft.Text(title, color="white", weight=ft.FontWeight.BOLD, size=15),
                ft.Container(height=4),
                ft.Text(body, color=ft.Colors.WHITE_70, size=13),
            ],
            spacing=2,
        )

    content = ft.Column(
        controls=[
             ft.Icon(
               ft.Icons.SECURITY,
               color="blue",
               size=64,
            ),
            ft.Text(
                spans=[
                        ft.TextSpan("Chat", style=ft.TextStyle(color="red", weight=ft.FontWeight.BOLD, size=26)),
                        ft.TextSpan("Bot", style=ft.TextStyle(color="blue", weight=ft.FontWeight.BOLD, size=26)),
                ]
            ),      
            ft.Divider(),  
            ft.Text("Last updated: 2026", color=ft.Colors.WHITE_54, size=12),
            ft.Container(height=10),
            section(
                "What we collect",
                "ChatBot processes the messages, photos, files, and voice recordings "
                "you send in order to generate a response. This includes text you "
                "type, images captured by your camera or picked from your gallery, "
                "files you attach, and audio captured through the microphone for "
                "speech-to-text transcription.",
            ),
            ft.Container(height=14),
            section(
                "How your data is used",
                "Your messages, photos, and files are sent to Google's Gemini API "
                "to generate a response. Voice recordings are sent to Google's "
                "speech recognition service to be transcribed into text. ChatBot "
                "itself does not store your conversations after the app is closed "
                "— chat history lives only in memory for the current session.",
            ),
            ft.Container(height=14),
            section(
                "Third-party services",
                "This app relies on Google's Gemini API for generating responses "
                "and describing images/files, and Google's speech recognition "
                "service for voice-to-text. Use of these services is subject to "
                "Google's own privacy policy and terms.",
            ),
            ft.Container(height=14),
            section(
                "Local storage",
                "Captured photos and picked files are temporarily saved to a local "
                "'assets' folder on your device so they can be uploaded and "
                "displayed. You can delete this folder at any time.",
            ),
            ft.Container(height=14),
            section(
                "Your choices",
                "You can clear your current chat at any time from the menu. "
                "Camera, microphone, and file access are only used when you "
                "actively tap those features — nothing is captured in the "
                "background.",
            ),
            ft.Container(height=14),
            section(
                "Contact",
                "Questions about this policy? Reach out from the Help & Support "
                "screen.",
            ),
            ft.Container(height=30),
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )

    page.add(
        ft.Container(content=content, padding=20, expand=True),
    )
    page.update()