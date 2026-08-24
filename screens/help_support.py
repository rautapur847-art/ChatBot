import flet as ft
import os
import asyncio
import smtplib

from email.mime.text import MIMEText
from dotenv import load_dotenv


# Load variables from .env
load_dotenv()


# Support email — where support messages will be received
SUPPORT_EMAIL = "rutapur847@gmail.com"


def _send_email(subject, body, sender_email, sender_password, to_email):
    """Send email using Gmail SMTP."""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(
            sender_email,
            [to_email],
            msg.as_string()
        )


def HelpSupportScreen(page: ft.Page, user_id, name):

    page.clean()

    from screens.setting import SettingScreen

    page.theme_mode = ft.ThemeMode.DARK

    # ---------------- APP BAR ----------------

    page.appbar = ft.AppBar(
        leading=ft.IconButton(
            ft.Icons.ARROW_BACK,
            tooltip="Setting",
            on_click=lambda e: SettingScreen(
                page,
                user_id,
                name
            ),
        ),
        title=ft.Text(
            "Help & Support",
            color="white",
            weight=ft.FontWeight.BOLD
        ),
        center_title=True,
        bgcolor=ft.Colors.TRANSPARENT,
    )

    # ---------------- FAQ ----------------

    faqs = [
        (
            "How do I send a photo?",
            "Tap the + button, then Camera to take a new photo "
            "or Image to pick one from your gallery. "
            "The photo attaches to the chat."
        ),
        (
            "How do I send a file?",
            "Tap the + button, then Files, and choose any file "
            "such as PDF, Word document, text file, etc."
        ),
        (
            "How does the mic work?",
            "Tap the mic icon and start speaking. "
            "The transcribed text appears in the message box "
            "for you to review and send."
        ),
        (
            "Is my chat history saved?",
            "Chats stay on screen for the current session. "
            "Use Clear Chat in the menu to start fresh."
        ),
        (
            "The app says my API key is invalid — what do I do?",
            "Double-check that your Gemini API key is set correctly. "
            "Generate a new key if necessary."
        ),
    ]

    def build_faq_tile(question, answer):

        return ft.ExpansionTile(
            title=ft.Text(
                question,
                color="white",
                weight=ft.FontWeight.BOLD,
                size=14,
            ),
            text_color="white",
            collapsed_text_color=ft.Colors.WHITE_54,
            controls=[
                ft.Container(
                    content=ft.Text(
                        answer,
                        color=ft.Colors.WHITE_70,
                        size=13,
                    ),
                    padding=ft.Padding(16, 0, 16, 12),
                )
            ],
        )

    # ---------------- MESSAGE FIELD ----------------

    message_field = ft.TextField(
        label="Your message",
        hint_text="Describe your issue...",
        multiline=True,
        min_lines=3,
        max_lines=6,
        color="white",
        border_color=ft.Colors.WHITE_24,
    )

    send_status = ft.Text(
        "",
        size=12,
    )

    # ---------------- SEND EMAIL ----------------

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

            # Get Gmail credentials from .env
            sender_email = os.getenv("SMTP_EMAIL")
            sender_password = os.getenv("SMTP_PASSWORD")

            if not sender_email or not sender_password:

                raise Exception(
                    "Email configuration missing. "
                    "Please add SMTP_EMAIL and SMTP_PASSWORD "
                    "to your .env file."
                )

            # Run blocking SMTP operation in background thread
            await asyncio.to_thread(
                _send_email,
                "ChatBot Support Request",
                body,
                sender_email,
                sender_password,
                SUPPORT_EMAIL,
            )

            send_status.value = (
                "Message sent! We'll get back to you soon."
            )

            send_status.color = "green"

            message_field.value = ""

        except Exception as ex:

            send_status.value = f"Failed to send: {ex}"
            send_status.color = "red"
            send_status.selectable = True

        finally:

            send_button.disabled = False
            message_field.disabled = False

            page.update()

    # ---------------- SEND BUTTON ----------------

    send_button = ft.ElevatedButton(
        "Send",
        icon=ft.Icons.SEND,
        bgcolor=ft.Colors.BLUE,
        color=ft.Colors.WHITE,
        on_click=send_support_click,
    )

    # ---------------- PAGE CONTENT ----------------

    content = ft.Column(
        controls=[

            # Support Icon
            ft.Container(
                content=ft.Icon(
                    ft.Icons.SUPPORT_AGENT,
                    color="blue",
                    size=64,
                ),
            ),

            # Logo
            ft.Text(
                spans=[
                    ft.TextSpan(
                        "Sup",
                        style=ft.TextStyle(
                            color="red",
                            weight=ft.FontWeight.BOLD,
                            size=26,
                        ),
                    ),
                    ft.TextSpan(
                        "port.",
                        style=ft.TextStyle(
                            color="blue",
                            weight=ft.FontWeight.BOLD,
                            size=26,
                        ),
                    ),
                ]
            ),

            ft.Divider(),

            ft.Container(height=6),

            # FAQ heading
            ft.Text(
                "Frequently asked questions",
                color="white",
                weight=ft.FontWeight.BOLD,
                size=16,
            ),

            # FAQ list
            ft.Column(
                controls=[
                    build_faq_tile(question, answer)
                    for question, answer in faqs
                ],
                spacing=2,
            ),

            ft.Divider(
                color=ft.Colors.WHITE_24
            ),

            # Support message heading
            ft.Text(
                "Still need help? Message us directly:",
                color="white",
                weight=ft.FontWeight.BOLD,
                size=16,
            ),

            ft.Container(height=8),

            # Message input
            message_field,

            ft.Container(height=6),

            # Send button
            send_button,

            # Status
            send_status,
        ],

        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=10,
    )

    # ---------------- ADD TO PAGE ----------------

    page.add(
        ft.Container(
            content=content,
            padding=20,
            expand=True,
        )
    )

    page.update()