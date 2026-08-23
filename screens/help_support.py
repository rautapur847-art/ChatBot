import flet as ft
import os
import asyncio
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()  # reads .env in your project root

SUPPORT_EMAIL = "SMTP_EMAIL"


def _send_email(subject, body, sender_email, sender_password, to_email):
    """Blocking SMTP send — always call this via asyncio.to_thread."""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, [to_email], msg.as_string())


def HelpSupportScreen(page: ft.Page,user_id,user_name):
    page.clean()
    from screens.setting import SettingScreen

    page.theme_mode = ft.ThemeMode.DARK

    page.appbar = ft.AppBar(
        leading=ft.IconButton(
            ft.Icons.ARROW_BACK,
            tooltip="Setting",
            on_click=lambda e: SettingScreen(page,user_id,user_name),
        ),
        title=ft.Text("Help & Support", color="white", weight=ft.FontWeight.BOLD),
        center_title=True,
        bgcolor=ft.Colors.TRANSPARENT,

    )

    faqs = [
        (
            "How do I send a photo?",
            "Tap the + button, then Camera to take a new photo or Image to pick "
            "one from your gallery. The photo attaches to the chat — write a "
            "caption and hit send, or send it as-is for an automatic description.",
        ),
        (
            "How do I send a file?",
            "Tap the + button, then Files, and choose any file (PDF, Word doc, "
            "text file, etc). It attaches the same way a photo does.",
        ),
        (
            "How does the mic work?",
            "Tap the mic icon and start speaking. Recording stops automatically "
            "once you pause, and the transcribed text appears in the message box "
            "for you to review and send.",
        ),
        (
            "Is my chat history saved?",
            "Chats stay on screen for the current session. Use Clear Chat in the "
            "menu to start fresh at any time.",
        ),
        (
            "The app says my API key is invalid — what do I do?",
            "Double-check that your Gemini API key is set correctly (it should "
            "start with 'AIzaSy...'). Generate a new one at "
            "aistudio.google.com/apikey if needed.",
        ),
    ]

    def build_faq_tile(question, answer):
        return ft.ExpansionTile(
            title=ft.Text(question, color="white", weight=ft.FontWeight.BOLD, size=14),
            text_color="white",
            collapsed_text_color=ft.Colors.WHITE_54,
            controls=[
                ft.Container(
                    content=ft.Text(answer, color=ft.Colors.WHITE_70, size=13),
                    padding=ft.Padding(16, 0, 16, 12),
                )
            ],
        )

    # ---- "message support directly from the app" section ----
    message_field = ft.TextField(
        label="Your message",
        hint_text="Describe your issue...",
        multiline=True,
        min_lines=3,
        max_lines=6,
        color="white",
        border_color=ft.Colors.WHITE_24,
    )
    send_status = ft.Text("", size=12)

    async def send_support_click(e):
        body = message_field.value.strip()
        if not body:
            send_status.value = "Please write a message first."
            send_status.color = "red"
            page.update()
            return

        send_button.disabled = True
        message_field.disabled = True
        send_status.value = "Sending..."
        send_status.color = "blue"
        page.update()

        try:
            sender_email = os.getenv("SMTP_EMAIL")
            sender_password = os.getenv("SMTP_PASSWORD")
            if not sender_email or not sender_password:
                raise Exception(
                    "Email sending isn't configured — add SMTP_EMAIL and "
                    "SMTP_PASSWORD to your .env file."
                )

            await asyncio.to_thread(
                _send_email,
                "ChatBot Support Request",
                body,
                sender_email,
                sender_password,
                SUPPORT_EMAIL,
            )
            send_status.value = "Message sent! We'll get back to you soon."
            send_status.color = "green"
            message_field.value = ""
        except Exception as ex:
            send_status.value = f"Failed to send: {ex}"
            send_status.color = "red"
        finally:
            send_button.disabled = False
            message_field.disabled = False
            page.update()

    send_button = ft.ElevatedButton(
        "Send",
        icon=ft.Icons.SEND,
        bgcolor=ft.Colors.BLUE,
        color=ft.Colors.WHITE,
        on_click=send_support_click,
    )

    content = ft.Column(
        controls=[

             # ChatBot Logo
             ft.Container(
                 content=ft.Icon(
                     ft.Icons.SUPPORT_AGENT,
                     color="blue",
                     size=64,
                 ),
              
             ),
     
            ft.Text(
                 spans=[
                        ft.TextSpan("Sup", style=ft.TextStyle(color="red", weight=ft.FontWeight.BOLD, size=26)),
                        ft.TextSpan("port.", style=ft.TextStyle(color="blue", weight=ft.FontWeight.BOLD, size=26)),
                    ]
            ),
            ft.Divider(),
            ft.Container(height=6),
            ft.Text("Frequently asked questions", color="white", weight=ft.FontWeight.BOLD, size=16),
            ft.Column(
                controls=[build_faq_tile(q, a) for q, a in faqs],
                spacing=2,
            ),
            ft.Divider(color=ft.Colors.WHITE_24),
            ft.Text("Still need help? Message us directly:", color="white", weight=ft.FontWeight.BOLD, size=16),
            ft.Container(height=8),
            message_field,
            ft.Container(height=6),
            send_button,
            send_status,
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=10,
    )

    page.add(
        ft.Container(content=content, padding=20, expand=True),
    )
    page.update()