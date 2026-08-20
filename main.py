# import flet as ft
# import os
# import asyncio
# import google.generativeai as gn
# gn.configure(api_key=os.getenv("GEMINI_API_KEY"))
# model = gn.GenerativeModel("gemini-3.6-flash")
# def main(page:ft.Page):
#     page.horizontal_alignment=ft.MainAxisAlignment.CENTER
#     page.vertical_alignment=ft.CrossAxisAlignment.CENTER
 
#     async def open_drawer(e):
#      await page.show_drawer()
     
        
        
        
    
#     chat_area = ft.Column(
#         expand=True,

#         scroll=ft.ScrollMode.AUTO,
#         width=700
#     )
#     async def chats_clear(e):
#      await page.close_drawer()
#      chat_area.controls.clear()
#      page.update()
      
#     page.appbar = ft.AppBar(
#     leading=ft.IconButton(
#     icon=ft.Icons.MENU,
#     icon_color=ft.Colors.WHITE,
#     tooltip="menu",
#     on_click=open_drawer
#     ),
#     bgcolor=ft.Colors.BLACK,
    
#     )
#     page.drawer = ft.NavigationDrawer(
#     controls=[
#         ft.ListTile(
#              title=ft.Icon(
#                 ft.Icons.ASSISTANT,
#                  color="white",size=60
#              ),
#             min_leading_width=200,
#             leading=ft.Text(
#                 spans=[
#                     ft.TextSpan(
#                         "Chat",
#                         style=ft.TextStyle(
#                             color="red",
#                             weight=ft.FontWeight.BOLD,
#                             size=24
#                         )
#                     ),
#                     ft.TextSpan(
#                         "Bot",
#                         style=ft.TextStyle(
#                             color="blue",
#                             weight=ft.FontWeight.BOLD,
#                             size=24
#                         )
#                     )
#                 ]
#             ),
#         ),

#         ft.Divider(),

#         ft.ListTile(
#             title=ft.Text(
#                 "Clear chat",
#                 color="red",
#                 weight=ft.FontWeight.BOLD
                
#             ),
        
#             leading=ft.Icon(
#                 ft.Icons.DELETE,
#                 color="red"
#             ),
#             on_click=chats_clear
#         ),

#         ft.Divider(),

#         ft.ListTile(
#             title=ft.Text(
#                 "New Chat",
#                 color="white",
#                 weight=ft.FontWeight.BOLD
#             ),
        
#             leading=ft.Icon(
#                 ft.Icons.CHAT,
#                 color="white"
#             )
#         )
#     ]
#     )
    
#     # def show_msg(sender,message):
#     #     chat_area.controls.append(
#     #         ft.Container(
               
#     #             ft.Text(
#     #                 spans=[
#     #                     ft.TextSpan(
#     #                         f"{sender}",
#     #                         style=ft.TextStyle(color="red",weight=ft.FontWeight.BOLD),
#     #                     ),
#     #                     ft.TextSpan(
#     #                        f"{message}",
#     #                        style=ft.TextStyle(color="white",weight=ft.FontWeight.BOLD)
#     #                     )
#     #                 ],
#     #                 selectable=True
#     #             ),
#     #             padding=0,
#     #             margin=5,
#     #             border_radius=5
#     #         )
          
#     #   )
#     #     page.update()
#     def show_msg(sender, message):
#         is_user = sender == "You" or sender == "User"
#         chat_area.controls.append(
#             ft.Column(
#             controls=[
#                 ft.Container(
#                     content=ft.Text(
#                         spans=[
#                             ft.TextSpan(
#                                 f"{sender}: ",
#                                 style=ft.TextStyle(
#                                     color="green" if is_user else "red", 
#                                     weight=ft.FontWeight.BOLD
#                                 ),
#                             ),
#                             ft.TextSpan(
#                                 f"{message}",
#                                 style=ft.TextStyle(color="white", weight=ft.FontWeight.BOLD)
#                             )
#                         ],
#                         selectable=True
#                     ),
#                     bgcolor="black",          # पूरा बॉक्स ब्लैक रहेगा
#                     padding=12,               # बॉक्स के अंदर जगह
#                     margin=5,                 # बॉक्स के बाहर जगह
#                     border_radius=10,         # बॉक्स के कोने गोल
#                     # यूजर का मैसेज दाईं तरफ (Right) और बाकी बाईं तरफ (Left)
#                    horizontal_alignment=ft.CrossAxisAlignment.END if is_user else ft.CrossAxisAlignment.START
#                 ),
#                 # हर एक चैट के बाद डिवाइडर लाइन
#                 ft.Divider(height=1, color="grey", thickness=0.5)
#             ],
#             # पूरे कॉलम को अलाइन करने के लिए
#             horizontal_alignment=ft.CrossAxisAlignment.END if is_user else ft.CrossAxisAlignment.START
#         )
#        )
#         page.update()
#     async def send_msg(e):
#         user = user_msg.value.strip()
#         if not user:
#             return
#         show_msg("",user)    
        
#         user_msg.value = ""
    
#         user_msg.hint_text = "Thinking..."
#         user_msg.disabled = True
#         user_msg.hint_style=ft.TextStyle(color="blue")
#         page.update()
#         try:
#             response = await asyncio.to_thread(model.generate_content,user)
#             show_msg("",response.text)
#         except Exception as e:
#             show_msg("Error",str(e)) 
#         finally:
#             user_msg.hint_text = "Ask anything..."
#             user_msg.hint_style = ft.TextStyle(color="white")
#             user_msg.disabled=False
#             page.update()     

#     user_msg = ft.TextField(
#         hint_text="Ask anything...",
#         hint_style=ft.TextStyle(color="white"),
#         value="",
#         autofocus=True,
#         expand=True,
#         align=ft.Alignment.BOTTOM_CENTER,
#         on_submit=send_msg,
        
#         suffix=ft.IconButton(
#             icon=ft.Icons.SEND_OUTLINED,
#             icon_color="blue",
#             # bgcolor="blue",
#             on_click=send_msg,
#             tooltip="Send..."
            
#         ),
        
#         height=60,
#         margin=5,
#         border_color=ft.Colors.WHITE_24,
#         width=500,
#         border_radius=20,
#         color="white"
   
#     )
#     page.add(
       
#         chat_area,
#         ft.Row(
#             controls=[
#                 user_msg,
                

#             ]
            
#         )
#     )
# ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=int(os.getenv("PORT", 8550)))    
import flet as ft
import os
import asyncio
import google.generativeai as gn

# API Configuration
gn.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = gn.GenerativeModel("gemini-1.5-flash") # मॉडल का नाम सही किया गया है

def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#121212"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER # सुधारा गया
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
 
    async def open_drawer(e):
        page.drawer.open = True
        page.update()

    chat_area = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        width=700
    )

    async def chats_clear(e):
        page.drawer.open = False
        chat_area.controls.clear()
        page.update()
      
    page.appbar = ft.AppBar(
        leading=ft.IconButton(
            icon=ft.Icons.MENU,
            icon_color=ft.Colors.WHITE,
            tooltip="menu",
            on_click=open_drawer
        ),
        bgcolor=ft.Colors.BLACK,
        title=ft.Text("AI ChatBot")
    )

    page.drawer = ft.NavigationDrawer(
        controls=[
            ft.Container(padding=20, content=ft.Icon(ft.Icons.ASSISTANT, size=50, color="blue")),
            ft.Divider(),
            ft.ListTile(
                title=ft.Text("Clear chat", color="red", weight=ft.FontWeight.BOLD),
                leading=ft.Icon(ft.Icons.DELETE, color="red"),
                on_click=chats_clear
            ),
            ft.ListTile(
                title=ft.Text("New Chat", color="white"),
                leading=ft.Icon(ft.Icons.CHAT, color="white"),
                on_click=chats_clear
            )
        ]
    )
    
    def show_msg(sender, message):
        # "You" होने पर दाईं ओर, वरना बाईं ओर
        is_user = sender == "You"
        
        chat_area.controls.append(
            ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            spans=[
                                ft.TextSpan(
                                    f"{sender}: ",
                                    style=ft.TextStyle(
                                        color="green" if is_user else "red", 
                                        weight=ft.FontWeight.BOLD
                                    ),
                                ),
                                ft.TextSpan(
                                    f"{message}",
                                    style=ft.TextStyle(color="white")
                                )
                            ],
                            selectable=True
                        ),
                        bgcolor="#1E1E1E" if is_user else "black",
                        padding=12,
                        margin=ft.margin.only(top=5, bottom=5),
                        border_radius=10,
                        alignment=ft.alignment.center_right if is_user else ft.alignment.center_left,
                        width=500, # बॉक्स की चौड़ाई सीमित की गई
                    ),
                    ft.Divider(height=1, color="grey30", thickness=0.5)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.END if is_user else ft.CrossAxisAlignment.START
            )
        )
        page.update()

    async def send_msg(e):
        user_text = user_msg.value.strip()
        if not user_text:
            return
        
        # 1. यूजर का मैसेज दिखाओ (Sender "You" दिया ताकि यह Right में आए)
        show_msg("You", user_text)    
        
        user_msg.value = ""
        user_msg.hint_text = "Thinking..."
        user_msg.disabled = True
        page.update()

        try:
            # 2. AI से रिस्पॉन्स लो
            response = await asyncio.to_thread(model.generate_content, user_text)
            # 3. AI का मैसेज दिखाओ (Sender "Bot" दिया ताकि यह Left में आए)
            show_msg("Bot", response.text)
        except Exception as ex:
            show_msg("Error", str(ex)) 
        finally:
            user_msg.hint_text = "Ask anything..."
            user_msg.disabled = False
            user_msg.focus()
            page.update()     

    user_msg = ft.TextField(
        hint_text="Ask anything...",
        expand=True,
        on_submit=send_msg,
        suffix=ft.IconButton(
            icon=ft.Icons.SEND_OUTLINED,
            icon_color="blue",
            on_click=send_msg
        ),
        border_radius=20,
        color="white"
    )

    page.add(
        chat_area,
        ft.Container(
            padding=10,
            content=ft.Row(
                controls=[user_msg],
                alignment=ft.MainAxisAlignment.CENTER
            )
        )
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8550))
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=port)

    
    

