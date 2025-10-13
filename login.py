import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

import keyring
import requests


KEYRING_SERVICE_ID = "PlatinaArchiveClient"
KEY_FILE = "platina.key"

if getattr(sys, "frozen", False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))


def load_key_from_file():
    key_path = os.path.join(base_dir, KEY_FILE)
    if not os.path.isfile(key_path):
        return None
    with open(key_path, "r") as f:
        api_key = f.read().strip()

    os.remove(key_path)
    keyring.set_password(KEYRING_SERVICE_ID, "main_api_key", api_key)
    return api_key


def _check_local_key():
    return keyring.get_password(KEYRING_SERVICE_ID, "main_api_key")


class RegisterWindow(tk.Toplevel):
    def __init__(self, parent, success_callback):
        super().__init__(parent)
        self.parent = parent
        self.success_callback = success_callback
        self.title("플라티나 아카이브 등록")
        self.geometry("300x200")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        # Decoder name
        ttk.Label(self, text="Name: ").pack(pady=5)
        self.name_entry = ttk.Entry(self)
        self.name_entry.pack(pady=2, padx=10, fill="x")

        # Password
        ttk.Label(self, text="Password: ").pack(pady=5)
        self.password_entry = ttk.Entry(self, show="*")
        self.password_entry.pack(pady=2, padx=10, fill="x")

        # Register button
        ttk.Button(self, text="Register", command=self.attempt_register).pack(pady=10)
        self.bind("<Return>", lambda x: self.attempt_register())

    def attempt_register(self):
        name = self.name_entry.get().strip()
        password = self.password_entry.get().strip()
        register_endpoint = "https://www.platina-archive.app/api/v1/register"

        if not name or not password:
            messagebox.showerror("Error", "이름과 비밀번호는 공백일 수 없습니다.")
            return

        try:
            response = requests.post(
                register_endpoint, json={"name": name, "password": password}
            )
            response.raise_for_status()

            data = response.json()
            api_key = data.get("key")

            if api_key:
                keyring.set_password(KEYRING_SERVICE_ID, "main_api_key", api_key)
                self.destroy()
                self.success_callback(name, api_key)
            else:
                messagebox.showerror(
                    "Error", "Register failed: Server did not return a key."
                )

        except requests.exceptions.HTTPError as e:
            # Handle 400 (bad creds) or 500 errors
            error_message = response.json().get("msg", "Invalid username or password")
            messagebox.showerror("Login Failed", error_message)
        except Exception as e:
            messagebox.showerror(
                "Connection Error", f"Could not connect to server: {e}"
            )
