import flet as ft
import asyncio
from database.db import ChatBotDatabase


class ChatHistory:
    def __init__(self, page, user_id, chat_area, show_msg_func, db=None):
        self.page = page
        self.user_id = user_id
        self.chat_area = chat_area
        self.show_msg_func = show_msg_func

        # Reuse the same connection as home.py when one is passed in,
        # instead of opening a second separate MySQL connection — avoids
        # any cross-connection stale-read issues entirely.
        self.db = db or ChatBotDatabase()

        # Tracks which history entry is currently displayed in chat_area,
        # so that deleting that same entry can clear the (now stale) view
        # instead of leaving deleted content on screen.
        self.current_chat_id = None

        self.history_list = ft.Column(
            spacing=2,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

        self.view = ft.Column(
            controls=[
                ft.Text(
                    "Chat History",
                    size=14,
                    color=ft.Colors.GREY_400,
                    weight=ft.FontWeight.BOLD,
                ),
                self.history_list,
            ],
            spacing=5,
            expand=True,
            margin=10,
            scroll=ft.ScrollMode.AUTO,
            
            
        )

        self.load_history()

    def load_history(self):
        self.history_list.controls.clear()

        try:
            chats = self.db.get_chat_history(self.user_id)
        except Exception as ex:
            print(f"ChatHistory.load_history: failed to load ({ex})")
            self.history_list.controls.append(
                ft.Text("Couldn't load chat history.", color=ft.Colors.RED_300, size=13)
            )
            return

        if not chats:
            self.history_list.controls.append(
                ft.Text(
                    "No chat history",
                    color=ft.Colors.GREY_500,
                    size=13,
                    margin=10
                )
            )
            return

        for chat in chats:
            chat_id = chat.get("id")
            if chat_id is None:
                continue  # malformed row — skip rather than crash
            message = chat.get("user_massage", "")

            if message.startswith("[Image]|||"):
                title = "[Image] Photo Attachment"
            elif message.startswith("[File]"):
                title = message[:25] + "..." if len(message) > 25 else message
            else:
                title = message[:25] + "..." if len(message) > 25 else message

            self.history_list.controls.append(
                self.create_chat_tile(chat_id, title)
            )

    def create_chat_tile(self, chat_id, title):
        delete_menu = ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT,
            icon_color=ft.Colors.GREY_400,
            items=[
                ft.PopupMenuItem(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.DELETE, color="red", size=18),
                            ft.Text("Delete", color="white", size=13),
                        ],
                        spacing=10,
                    ),
                    on_click=lambda e, cid=chat_id: self.delete_chat(cid),
                ),
            ],
        )

        return ft.ListTile(
            title=ft.Text(title, color=ft.Colors.WHITE, size=13, max_lines=1),
            leading=ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, color=ft.Colors.BLUE, size=20),
            trailing=delete_menu,
            dense=True,
            on_click=lambda e, cid=chat_id: self.open_chat(cid),
        )

    def open_chat(self, chat_id):
        async def fetch_and_display():
            if self.page.drawer:
                await self.page.close_drawer()

            try:
                chat_data = self.db.get_single_chat(chat_id, self.user_id)
            except Exception as ex:
                print(f"ChatHistory.open_chat: failed to load chat {chat_id} ({ex})")
                return

            if chat_data:
                self.current_chat_id = chat_id
                self.chat_area.controls.clear()
                self.show_msg_func("You: ", chat_data["user_massage"])
                self.show_msg_func("AI: ", chat_data["ai_response"])
                self.page.update()

        self.page.run_task(fetch_and_display)

    def delete_chat(self, chat_id):
        try:
            self.db.delete_chat(chat_id, self.user_id)
        except Exception as ex:
            print(f"ChatHistory.delete_chat: failed to delete {chat_id} ({ex})")
            return

        # If the chat currently shown on screen is the one just deleted,
        # clear it out too — otherwise deleted content stays visible.
        if self.current_chat_id == chat_id:
            self.current_chat_id = None
            self.chat_area.controls.clear()

        self.load_history()
        self.page.update()

    def refresh(self):
        self.load_history()
        self.history_list.update()
