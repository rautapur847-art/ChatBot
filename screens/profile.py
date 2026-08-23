import flet as ft
from database.db import ChatBotDatabase


def get_initials(name):
    parts = (name or "").strip().split()
    if len(parts) >= 2:
        return parts[0][0].upper() + parts[1][0].upper()
    return parts[0][0].upper() if parts else "You"


def ProfileScreen(page: ft.Page, user_id, user_name=None):
    page.clean()
    from screens.home import HomeScreen

    page.theme_mode = ft.ThemeMode.DARK
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    db = ChatBotDatabase()
    user = db.get_user_by_id(user_id) or {}

    page.appbar = ft.AppBar(
        leading=ft.IconButton(
            ft.Icons.ARROW_BACK,
            tooltip="Home",
            on_click=lambda e: HomeScreen(
                page,
                user_id,
                user.get("name", user_name)
            ),
        ),
        title=ft.Text(
            "Profile",
            color="white",
            weight=ft.FontWeight.BOLD
        ),
        center_title=True,
        bgcolor=ft.Colors.TRANSPARENT,
    )

    avatar = ft.CircleAvatar(
        content=ft.Text(
            get_initials(user.get("name", user_name)),
            weight=ft.FontWeight.BOLD,
            size=28
        ),
        radius=44,
        bgcolor=ft.Colors.BLUE,
    )

    name_field = ft.TextField(
        label="Name",
        value=user.get("name", ""),
        width=320,
        disabled=True,
        color="white",
        border_color=ft.Colors.WHITE_24,
    )

    email_field = ft.TextField(
        label="Email",
        value=user.get("email", ""),
        width=320,
        disabled=True,
        color="white",
        border_color=ft.Colors.WHITE_24,
    )

    mobile_field = ft.TextField(
        label="Mobile",
        value=user.get("mobile", ""),
        width=320,
        disabled=True,
        color="white",
        border_color=ft.Colors.WHITE_24,
    )

    password_field = ft.TextField(
        label="Password",
        value=user.get("password", ""),
        width=320,
        password=True,
        can_reveal_password=True,
        disabled=True,
        color="white",
        border_color=ft.Colors.WHITE_24,
    )

    status_text = ft.Text(
        "",
        size=12,
        text_align=ft.TextAlign.CENTER
    )

    is_editing = False

    def set_editing(editing: bool):
        nonlocal is_editing

        is_editing = editing

        name_field.disabled = not editing
        email_field.disabled = not editing
        mobile_field.disabled = not editing
        password_field.disabled = not editing

        edit_save_button.text = "Save" if editing else "Edit"
        edit_save_button.icon = (
            ft.Icons.SAVE if editing else ft.Icons.EDIT
        )

        page.update()

    def edit_save_click(e):

        if not is_editing:
            status_text.value = ""
            set_editing(True)
            return

        # ---- Save ----

        name = name_field.value.strip()
        email = email_field.value.strip()
        mobile = mobile_field.value.strip()
        new_password = password_field.value.strip()

        if not name or not email or not mobile:

            status_text.value = (
                "Name, email, and mobile can't be empty."
            )

            status_text.color = "red"

            page.update()

            return

        # Agar password change nahi kiya
        # to purana password hi save hoga.

        password_to_save = (
            new_password
            if new_password
            else user.get("password", "")
        )

        try:

            db.update_profile(
                user_id,
                name,
                email,
                mobile,
                password_to_save
            )

        except Exception as ex:

            status_text.value = f"Failed to save: {ex}"
            status_text.color = "red"

            page.update()

            return

        # Update local user data

        user["name"] = name
        user["email"] = email
        user["mobile"] = mobile
        user["password"] = password_to_save

        # Avatar update

        avatar.content.value = get_initials(name)

        status_text.value = "Profile updated!"
        status_text.color = "green"

        # Edit mode se normal mode

        set_editing(False)

    edit_save_button = ft.ElevatedButton(
        "Edit",
        icon=ft.Icons.EDIT,
        bgcolor=ft.Colors.BLUE,
        color=ft.Colors.WHITE,
        on_click=edit_save_click,
    )

    content = ft.Column(
        controls=[
            ft.Container(height=10),

            ft.Container(
                content=avatar,
                alignment=ft.Alignment(0, 0)
            ),

            ft.Container(height=20),

            name_field,
            email_field,
            mobile_field,
            password_field,

            ft.Container(height=10),

            edit_save_button,

            status_text,
        ],

        horizontal_alignment=ft.CrossAxisAlignment.CENTER,

        expand=True,

        scroll=ft.ScrollMode.AUTO,

        spacing=14,
    )

    page.add(
        ft.Container(
            content=content,
            padding=20,
            expand=True,
            alignment=ft.Alignment(0, 0),
        )
    )

    page.update()