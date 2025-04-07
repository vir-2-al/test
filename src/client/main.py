import flet as ft
from flet.core.control_event import ControlEvent
from time import sleep

from httpx import AsyncClient, ASGITransport, Cookies, Timeout, Client, ConnectError
from fastapi import status
from src.config import APP_NET_PORT

# Create a Cookies object
cookies = Cookies()
timeout = Timeout(5.0)

APP_NAME = "WEB app client"
SRV_BASE_URL = f"http://localhost:{APP_NET_PORT}"


def srv_login(username: str, password: str) -> (bool, str):
    global cookies
    with Client(base_url=SRV_BASE_URL) as client:
        try:
            response = client.post(url="api/v1/login",
                                   json={
                                       "username": username,
                                       "password": password
                                   },
                                   timeout=timeout)
            ret_code = response.status_code
            if ret_code == status.HTTP_200_OK:
                cookies = response.cookies
                return True, "Successful"
            else:
                return False, "Incorrect credentials"
        except ConnectError as e:
            return False, f"Can't connect to server. {e}"


def srv_upload(filename: str) -> (bool, str):
    with Client(base_url=SRV_BASE_URL) as client:
        try:
            # with open(filename, 'rb') as f:
            #     response = client.post(url="api/v1/files",
            #                            files={'file': (filename, f)},
            #                            cookies=cookies
            #                            )

            files = [('file', open(filename, 'rb'))]
            # files = {'file': open(filename, 'rb')}
            response = client.post(url="api/v1/files",
                                   headers={"Content-Type": "application/json"},
                                   files=files,
                                   cookies=cookies)
            ret_code = response.status_code
            if ret_code == status.HTTP_201_CREATED:
                return True, "Successful"
            else:
                return False, "Error upload file"
        except ConnectError as e:
            return False, f"Connection error. {e}"


def srv_reg_user(username: str, password: str) -> (bool, str):
    with Client(base_url=SRV_BASE_URL) as client:
        try:
            response = client.post(url="api/v1/users",
                                   json={
                                       "username": username,
                                       "password": password
                                   },
                                   cookies=cookies,
                                   timeout=timeout)
            ret_code = response.status_code
            if ret_code == status.HTTP_201_CREATED:
                return True, "Successful"
            else:
                return False, "Can't register new user"
        except ConnectError as e:
            return False, f"Can't connect to server. {e}"


def page_login(page: ft.Page) -> None:
    def validate(e: ControlEvent):
        login_button.disabled = not (len(username_field.value) >= 5 and len(password_field.value) >= 8)
        page.update()

    def submit(e: ControlEvent):
        username = username_field.value
        password = password_field.value
        res, msg = srv_login(username, password)
        if res:
            page.clean()
            page.add(
                ft.Row(
                    controls=[ft.Text(value=f"Welcome {username}!", size=20)],
                    alignment=ft.MainAxisAlignment.CENTER
                )
            )
            sleep(2)
            page_main(page)
        else:
            page.open(ft.SnackBar(ft.Text(f"{msg}")))
            page.update()

    page.clean()
    page.title = APP_NAME
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window_width = 400
    page.window_height = 400
    page.window_resizable = False

    username_field = ft.TextField(label="Username", width=400, hint_text="min 5 char",
                                  icon=ft.Icons.DRIVE_FILE_RENAME_OUTLINE, tooltip="Username", on_change=validate)
    password_field = ft.TextField(label="Password", width=400, hint_text="min 8 char", icon=ft.Icons.PASSWORD,
                                  password=True, tooltip="Password", on_change=validate)
    login_button = ft.ElevatedButton(text="Login", icon=ft.Icons.LOGIN, disabled=True, tooltip="Login", on_click=submit)

    page.add(
        ft.Row(
            controls=[
                ft.Column(
                    [
                        username_field,
                        password_field,
                        login_button
                    ]
                )
            ], alignment=ft.MainAxisAlignment.CENTER
        )
    )


def page_main(page: ft.Page) -> None:

    def upload_clicked(e):
        file_picker.pick_files(allow_multiple=True)
        # page.update()
        # page.open(ft.SnackBar(ft.Text("Upload")))
        # page.update()

    def register_clicked(e):
        page_register(page)

    def account_clicked(e):
        page_account(page)

    def pick_files_result(e: ft.FilePickerResultEvent):
        if e.files:
            lst = list(map(lambda f: f.path, e.files))
            for filename in lst:
                res, msg = srv_upload(filename)
                if not res:
                    page.open(ft.SnackBar(ft.Text(f"Error: {msg}")))
                    page.update()
                    break

        # selected_files.value = (
        #     ", ".join(map(lambda f: f.name, e.files)) if e.files else "Cancelled!"
        # )
        # selected_files.update()
        # ft.SnackBar(selected_files)
        # # e.files is a list of files
        # if e.files is None: return
        # for x in e.files:
        #     # do_something
        #     # x.name to get the name of the file
        #     # x.path to get the path of the file
        #     pass

    page.clean()
    file_picker = ft.FilePicker(on_result=pick_files_result)
    page.overlay.append(file_picker)
    page.appbar = ft.AppBar(
        #leading=ft.Icon(ft.Icons.PALETTE),
        leading_width=40,
        title=ft.Text(APP_NAME),
        center_title=False,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        actions=[
            ft.IconButton(ft.Icons.UPLOAD_FILE, on_click=upload_clicked, tooltip="Upload file"),
            ft.IconButton(ft.Icons.SUPERVISOR_ACCOUNT, on_click=register_clicked, tooltip="New user"),
            ft.IconButton(ft.Icons.MANAGE_ACCOUNTS, on_click=account_clicked, tooltip="Account",)
        ],
    )
    # page.add(ft.Text("Body!"))
    page.update()


# def file_upload_page(page: ft.Page):
#     file_picker = ft.FilePicker()
#     upload_button = ft.ElevatedButton("Upload", on_click=lambda _: file_picker.pick_files(allow_multiple=True))
#     page.add(ft.Row([upload_button, file_picker], alignment=ft.MainAxisAlignment.CENTER,))

def page_account(page: ft.Page):
    page.clean()

    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window_width = 400
    page.window_height = 400
    page.window_resizable = False

    page.add(
        ft.AutofillGroup(
            ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.TextField(
                                label="Username",
                                autofill_hints=ft.AutofillHint.USERNAME,
                            ),
                            ft.TextField(
                                label="Password",
                                autofill_hints=ft.AutofillHint.PASSWORD,
                            ),
                            ft.TextField(
                                label="First name",
                                autofill_hints=ft.AutofillHint.NAME,
                            ),
                            ft.TextField(
                                label="Middle name",
                                autofill_hints=ft.AutofillHint.MIDDLE_NAME,
                            ),
                            ft.TextField(
                                label="Last name",
                                autofill_hints=ft.AutofillHint.FAMILY_NAME,
                            ),
                            ft.TextField(
                                label="Company",
                                autofill_hints=ft.AutofillHint.ORGANIZATION_NAME,
                            ),
                            ft.TextField(
                                label="Job title",
                                autofill_hints=[ft.AutofillHint.JOB_TITLE],
                            )
                        ], alignment=ft.MainAxisAlignment.CENTER
                    )
                ]
            )
        )
    )
    page.update()


def page_register(page: ft.Page):

    def validate(e: ControlEvent):
        register_button.disabled = not (len(username_field.value) >= 5 and len(password_field.value) >= 8)
        page.update()

    def submit(e: ControlEvent):
        username = username_field.value
        password = password_field.value
        res, msg = srv_reg_user(username, password)
        if res:
            dlg = ft.AlertDialog(
                title=ft.Text(f"User {username} register!"),
                on_dismiss=lambda e: page_main(page),
            )
            page.open(dlg)
        else:
            dlg = ft.AlertDialog(
                title=ft.Text(f"Can't register new user!"),
            )
            page.open(dlg)

    page.clean()

    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window_width = 400
    page.window_height = 400
    page.window_resizable = False

    username_field = ft.TextField(label="Username", width=400, hint_text="min 5 char",
                                  icon=ft.Icons.DRIVE_FILE_RENAME_OUTLINE, on_change=validate, tooltip="Username")
    password_field = ft.TextField(label="Password", width=400, hint_text="min 8 char", icon=ft.Icons.PASSWORD,
                                  password=True, on_change=validate, tooltip="Password")
    cancel_button = ft.ElevatedButton(text="Cancel", icon=ft.Icons.CANCEL, disabled=False,
                                      on_click=lambda e: page_main(page), tooltip="Cencel")
    register_button = ft.ElevatedButton(text="Add user", icon=ft.Icons.PLUS_ONE, disabled=True,
                                        on_click=submit, tooltip="Register user")

    page.add(
        ft.Row(
            controls=[
                ft.AutofillGroup(
                    ft.Column(
                        controls=[
                            username_field,
                            password_field
                        ]
                    )
                ),
            ], alignment=ft.MainAxisAlignment.CENTER
        ),
        ft.Row(
            controls=[
                ft.Column(controls=[register_button]),
                ft.Column(controls=[cancel_button])
            ], alignment=ft.MainAxisAlignment.CENTER
        )
    )
    page.update()


if __name__ == "__main__":
    # ft.app(target=page_login)
    ft.app(target=page_login, port=8550, view=ft.WEB_BROWSER)


