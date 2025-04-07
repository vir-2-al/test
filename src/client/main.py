import flet as ft
from flet.core.control_event import ControlEvent
from time import sleep

from httpx import AsyncClient, ASGITransport, Cookies, Timeout, Client, ConnectError
from fastapi import status
from authx import AuthX, AuthXConfig, TokenPayload
#from src.config import APP_SRV_HOST, APP_SRV_PORT

# Create a Cookies object
cookies = Cookies()
timeout = Timeout(5.0)

APP_SRV_HOST = "localhost"
# APP_SRV_HOST = "test_srv_app"
APP_SRV_PORT = 8000

APP_NAME = "WEB app client"
SRV_BASE_URL = f"http://{APP_SRV_HOST}:{APP_SRV_PORT}"

FORM_SIZE = 400


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

def srv_logout() -> (bool, str):
    with Client(base_url=SRV_BASE_URL) as client:
        try:
            response = client.post(url=f"api/v1/logout",
                                  cookies=cookies,
                                  timeout=timeout)
            ret_code = response.status_code
            if ret_code == status.HTTP_200_OK:
                return True, "Successful"
            else:
                return False, "Can't logout", None
        except ConnectError as e:
            return False, f"Can't connect to server. {e}", None


def srv_upload(filename: str) -> (bool, str):
    with Client(base_url=SRV_BASE_URL) as client:
        try:
            files = [("file", open(filename, "rb"))]
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

def srv_get_user_info() -> (bool, str, dict):
    with Client(base_url=SRV_BASE_URL) as client:
        try:
            response = client.get(url=f"api/v1/users/{0}",
                                   cookies=cookies,
                                   timeout=timeout)
            ret_code = response.status_code
            data = response.json()
            if ret_code == status.HTTP_200_OK:
                return True, "Successful", data
            else:
                return False, "Can't get data", None
        except ConnectError as e:
            return False, f"Can't connect to server. {e}", None

def srv_set_user_info(user_data: dict) -> (bool, str):
    with Client(base_url=SRV_BASE_URL) as client:
        try:
            response = client.put(url=f"api/v1/users/{0}",
                                  json=user_data,
                                  cookies=cookies,
                                  timeout=timeout)
            ret_code = response.status_code
            if ret_code == status.HTTP_200_OK:
                return True, "Successful"
            else:
                return False, "Can't set data", None
        except ConnectError as e:
            return False, f"Can't connect to server. {e}", None

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

    page.appbar = None
    page.clean()
    page.title = "Authentication"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window_width = FORM_SIZE
    page.window_height = FORM_SIZE
    page.window_resizable = False

    username_field = ft.TextField(label="Username", width=FORM_SIZE, hint_text="min 5 char",
                                  icon=ft.Icons.DRIVE_FILE_RENAME_OUTLINE, tooltip="Username",
                                  on_change=validate, autofocus=True)
    password_field = ft.TextField(label="Password", width=FORM_SIZE, hint_text="min 8 char", icon=ft.Icons.PASSWORD,
                                  password=True, tooltip="Password", on_change=validate,
                                  on_submit=submit, can_reveal_password=True)
    login_button = ft.ElevatedButton(text="Login", icon=ft.Icons.LOGIN, disabled=True, tooltip="Login", on_click=submit)

    page.add(
        ft.Row(
            controls=[
                ft.Column(
                    [
                        username_field,
                        password_field
                    ]
                )
            ], alignment=ft.MainAxisAlignment.CENTER
        ),
        ft.Row(
            controls=[
                ft.Column(controls=[login_button])
            ], alignment=ft.MainAxisAlignment.CENTER
        )
    )


def page_main(page: ft.Page) -> None:

    def upload_clicked(e):
        file_picker.pick_files(allow_multiple=True)

    def register_clicked(e):
        page_register(page)

    def account_clicked(e):
        page_account(page)

    def logout_clicked(e):
        res, msg = srv_logout()
        if res:
            dlg = ft.AlertDialog(
                title=ft.Text(f"User logout!"),
                on_dismiss=lambda e: page_login(page),
            )
            page.open(dlg)
        else:
            dlg = ft.AlertDialog(
                title=ft.Text(f"Error logout!"),
            )
            page.open(dlg)

    def pick_files_result(e: ft.FilePickerResultEvent):
        if e.files:
            lst = list(map(lambda f: f.path, e.files))
            for filename in lst:
                res, msg = srv_upload(filename)
                if not res:
                    page.open(ft.SnackBar(ft.Text(f"Error: {msg}")))
                    page.update()
                    break

    page.clean()
    page.title = APP_NAME
    file_picker = ft.FilePicker(on_result=pick_files_result)
    page.overlay.append(file_picker)
    page.appbar = ft.AppBar(
        leading_width=40,
        title=ft.Text(APP_NAME),
        center_title=False,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
        actions=[
            ft.IconButton(ft.Icons.UPLOAD_FILE, on_click=upload_clicked, tooltip="Upload file"),
            ft.IconButton(ft.Icons.SUPERVISOR_ACCOUNT, on_click=register_clicked, tooltip="New user"),
            ft.IconButton(ft.Icons.MANAGE_ACCOUNTS, on_click=account_clicked, tooltip="Account",),
            ft.IconButton(ft.Icons.LOGOUT, on_click=logout_clicked, tooltip="Exit", )
        ],
    )
    page.update()


def page_account(page: ft.Page):

    def validate(e: ControlEvent):
        save_button.disabled = not (len(username_field.value) >= 5 and len(password_field.value) >= 8)
        page.update()

    def submit(e: ControlEvent):
        user_data = {"id": 0,
                     "username": username_field.value,
                     "password": password_field.value,
                     "first_name": firstname_field.value,
                     "middle_name": middlename_field.value,
                     "last_name": lastname_field.value,
                     "company": company_field.value,
                     "job_title": jobtitle_field.value
                     }
        res, msg = srv_set_user_info(user_data)
        if res:
            dlg = ft.AlertDialog(
                title=ft.Text(f"User {username_field.value} updated!"),
                on_dismiss=lambda e: page_main(page),
            )
            page.open(dlg)
        else:
            dlg = ft.AlertDialog(
                title=ft.Text(f"Can't register new user!"),
            )
            page.open(dlg)

    page.clean()
    page.title = "Account"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window_width = FORM_SIZE
    page.window_height = FORM_SIZE
    page.window_resizable = False

    res, msg, data = srv_get_user_info()
    if res:
        print(repr(data))

    username_field = ft.TextField(label="Username", width=FORM_SIZE, hint_text="min 5 char",
                                  icon=ft.Icons.DRIVE_FILE_RENAME_OUTLINE, on_change=validate,
                                  tooltip="Username", autofocus=True, value=data['username'])
    password_field = ft.TextField(label="Password", width=FORM_SIZE, hint_text="min 8 char", icon=ft.Icons.PASSWORD,
                                  password=True, on_change=validate, tooltip="< Password >", can_reveal_password=True,
                                  value=data['password'])
    firstname_field = ft.TextField(label="First name", width=FORM_SIZE, hint_text="<first name>",
                                  icon=ft.Icons.EDIT, on_change=validate, value=data['first_name'],
                                  tooltip="First name")
    middlename_field = ft.TextField(label="Middle name", width=FORM_SIZE, hint_text="<middle name>",
                                   icon=ft.Icons.EDIT, on_change=validate, value=data['middle_name'],
                                   tooltip="Middle name")
    lastname_field = ft.TextField(label="Last name", width=FORM_SIZE, hint_text="<last name>",
                                    icon=ft.Icons.EDIT, on_change=validate, value=data['last_name'],
                                    tooltip="Last name")
    company_field = ft.TextField(label="Company", width=FORM_SIZE, hint_text="<company>",
                                  icon=ft.Icons.BUSINESS, on_change=validate, value=data['company'],
                                  tooltip="Company")
    jobtitle_field = ft.TextField(label="Job title", width=FORM_SIZE, hint_text="<job title>",
                                  icon=ft.Icons.BADGE, on_change=validate, value=data['job_title'],
                                  tooltip="Job title")

    cancel_button = ft.ElevatedButton(text="Cancel", icon=ft.Icons.CANCEL, disabled=False,
                                      on_click=lambda e: page_main(page), tooltip="Cencel")
    save_button = ft.ElevatedButton(text="Save", icon=ft.Icons.SAVE, disabled=True,
                                        on_click=submit, tooltip="Save data")
    page.add(
            ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            username_field,
                            password_field,
                            firstname_field,
                            middlename_field,
                            lastname_field,
                            company_field,
                            jobtitle_field
                        ]
                    )
                ], alignment=ft.MainAxisAlignment.CENTER
            ),
            ft.Row(
                controls=[
                    ft.Column(controls=[save_button]),
                    ft.Column(controls=[cancel_button])
                ], alignment=ft.MainAxisAlignment.CENTER
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
    page.title = "Registration"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window_width = FORM_SIZE
    page.window_height = FORM_SIZE
    page.window_resizable = False

    username_field = ft.TextField(label="Username", width=FORM_SIZE, hint_text="min 5 char",
                                  icon=ft.Icons.DRIVE_FILE_RENAME_OUTLINE, on_change=validate,
                                  tooltip="Username", autofocus=True)
    password_field = ft.TextField(label="Password", width=FORM_SIZE, hint_text="min 8 char", icon=ft.Icons.PASSWORD,
                                  password=True, on_change=validate, tooltip="Password", can_reveal_password=True)
    cancel_button = ft.ElevatedButton(text="Cancel", icon=ft.Icons.CANCEL, disabled=False,
                                      on_click=lambda e: page_main(page), tooltip="Cencel")
    register_button = ft.ElevatedButton(text="Add user", icon=ft.Icons.PLUS_ONE, disabled=True,
                                        on_click=submit, tooltip="Register user")

    page.add(
        ft.Row(
            controls=[
                    ft.Column(
                        controls=[
                            username_field,
                            password_field
                        ]
                    )
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
    ft.app(target=page_login, port=9000, view=ft.WEB_BROWSER)


