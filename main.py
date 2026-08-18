import flet as ft
import os
import asyncio
import google.generativeai as gn
gn.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = gn.GenerativeModel("gemini-3.6-flash")
def main(page:ft.Page):
    page.horizontal_alignment=ft.MainAxisAlignment.CENTER
    page.vertical_alignment=ft.CrossAxisAlignment.CENTER
    
    def chatDelete(fun):
        def delete(e):
            page.drawer.close()
            page.update()
            fun()
        return delete()    
        
        
    
    chat_area = ft.Column(
        expand=True,

        scroll=ft.ScrollMode.AUTO,
        width=700
    )
    def chats_clear(e):
        chat_area.controls.clear()
        page.update()
    appbar = ft.AppBar(
    ft.IconButton(
    icon=ft.Icons.MENU,
    icon_color=ft.Colors.RED,
    tooltip="Delete",
    on_click=chatDelete
    ),
    center_title=True,
    bgcolor=ft.Colors.WHITE_10,
    title=ft.Text(
        spans=[
            ft.TextSpan(
                "Chat",
                style=ft.TextStyle(color="red",weight=ft.FontWeight.BOLD)
            ),
            ft.TextSpan(
                "Bot",
                style=ft.TextStyle(color="blue",weight=ft.FontWeight.BOLD)
            )
        ]
    )
    )
    page.drawer = ft.NavigatinDrawer(
        controls=[
            ft.ListTile(
                title=ft.Text("Clear chat",color="red"),
                leading=ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_color="red"
                ),
                on_click=chats_clear
            )
        ]
    )
    def show_msg(sender,massage):
        chat_area.controls.append(
            ft.Container(
               
                ft.Text(
                    spans=[
                        ft.TextSpan(
                            f"{sender}",
                            style=ft.TextStyle(color="red",weight=ft.FontWeight.BOLD),
                        ),
                        ft.TextSpan(
                           f"{massage}",
                           style=ft.TextStyle(color="white",weight=ft.FontWeight.BOLD)
                        )
                    ],
                    selectable=True
                ),
                padding=0,
                margin=5,
                border_radius=5
            )
        )

        page.update()
    async def send_msg(e):
        user = user_msg.value.strip()
        if not user:
            return
        show_msg("",user)    
        
        user_msg.value = ""
        user_msg.hint_text = "Thinking...."
        user_msg.disabled = True
        page.update()
        try:
            response = await asyncio.to_thread(model.generate_content,user)
            show_msg("",response.text)
        except Exception as e:
            show_msg("Error",e) 
        finally:
            user_msg.hint_text = "Ask anything...."
            user_msg.disabled=False
            page.update()     

    user_msg = ft.TextField(
        hint_text="Ask anything...",
        value="",
        autofocus=True,
        expand=True,
        align=ft.Alignment.BOTTOM_CENTER,
        on_submit=send_msg,
        
        suffix=ft.IconButton(
            icon=ft.Icons.SEND_OUTLINED,
            icon_color="blue",
            # bgcolor="blue",
            on_click=send_msg,
            tooltip="Send..."
            
        ),
        
        height=60,
        margin=5,
        border_color=ft.Colors.WHITE_24,
        width=500,
        border_radius=20,
        color="white"
   
    )
    page.add(
        appbar,
        chat_area,
        ft.Row(
            controls=[
                user_msg,
                

            ]
            
        )
    )
ft.run(main)
