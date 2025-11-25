import os
import sys
import sqlite3
import customtkinter as ctk
from tkinter import messagebox, PhotoImage

from database import DB_NAME, init_db, get_setting, log_activity


class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window config
        self.title("MEDISKED: HOSPITAL SCHEDULING AND BILLING MANAGMENT SYSTEM - Login")
        self.geometry("420x460")
        self.resizable(False, False)

        # Window icon (works both in source run and PyInstaller EXE)
        if getattr(sys, "frozen", False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(__file__)
        ico_path = os.path.join(base_dir, "images", "logo.ico")
        png_path = os.path.join(base_dir, "images", "logo.png")

        try:
            if os.path.exists(ico_path):
                self.iconbitmap(ico_path)
            elif os.path.exists(png_path):
                self._icon_image = PhotoImage(file=png_path)
                self.iconphoto(False, self._icon_image)
        except Exception:
            pass

        # Center window on screen (compact size)
        self.update_idletasks()
        width = 420
        height = 460
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Set appearance
        ctk.set_appearance_mode("dark")  # "light", "dark", or "system"
        ctk.set_default_color_theme("blue")

        # Auth state (used by external main app)
        self.authenticated = False
        self.logged_in_user = None
        self.logged_in_role = None

        # Root grid (single centered card)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Main card
        self.card_frame = ctk.CTkFrame(self, corner_radius=14)
        self.card_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.card_frame.grid_columnconfigure(0, weight=1)

        # Account icon (no background shape)
        self.icon_circle = ctk.CTkLabel(
            self.card_frame,
            text="👤",
            font=("Segoe UI", 32),
        )
        self.icon_circle.grid(row=0, column=0, pady=(24, 10))

        # Title
        self.logo_label = ctk.CTkLabel(
            self.card_frame,
            text="Login to Your Account",
            font=("Segoe UI", 18, "bold"),
        )
        self.logo_label.grid(row=1, column=0, padx=24, pady=(0, 16))

        # Username label + entry
        self.username_label = ctk.CTkLabel(
            self.card_frame,
            text="Username",
            font=("Segoe UI", 11),
        )
        self.username_label.grid(row=2, column=0, padx=24, sticky="w")

        self.username_entry = ctk.CTkEntry(
            self.card_frame,
            placeholder_text="Enter username",
            height=36,
            corner_radius=8,
        )
        self.username_entry.grid(row=3, column=0, padx=24, pady=(4, 10), sticky="ew")

        # Password label
        self.password_label = ctk.CTkLabel(
            self.card_frame,
            text="Password",
            font=("Segoe UI", 11),
        )
        self.password_label.grid(row=4, column=0, padx=24, sticky="w")

        # Password row (entry with eye button inside)
        self.password_frame = ctk.CTkFrame(self.card_frame, fg_color="transparent")
        self.password_frame.grid(row=5, column=0, padx=24, pady=(4, 10), sticky="ew")
        self.password_frame.grid_columnconfigure(0, weight=1)

        self.password_entry = ctk.CTkEntry(
            self.password_frame,
            placeholder_text="Enter password",
            show="*",
            height=36,
            corner_radius=8,
        )
        self.password_entry.grid(row=0, column=0, sticky="ew")

        self.show_password = False
        self.eye_button = ctk.CTkButton(
            self.password_frame,
            text="👁",
            width=28,
            height=24,
            corner_radius=0,
            fg_color="transparent",
            hover_color=None,
            border_width=0,
            command=self.toggle_password_visibility,
        )
        self.eye_button.place(relx=0.95, rely=0.5, anchor="center")

        # Bottom row: remember me + forgot password
        bottom_row = ctk.CTkFrame(self.card_frame, fg_color="transparent")
        bottom_row.grid(row=6, column=0, padx=24, pady=(0, 10), sticky="ew")
        bottom_row.grid_columnconfigure(0, weight=1)
        bottom_row.grid_columnconfigure(1, weight=0)

        self.remember_var = ctk.BooleanVar(value=False)
        self.remember_check = ctk.CTkCheckBox(
            bottom_row,
            text="Remember me",
            variable=self.remember_var,
            font=("Segoe UI", 10),
        )
        self.remember_check.grid(row=0, column=0, sticky="w")

        self.forgot_label = ctk.CTkLabel(
            bottom_row,
            text="Forgot password?",
            font=("Segoe UI", 10, "underline"),
        )
        self.forgot_label.grid(row=0, column=1, sticky="e")

        # Login button
        self.login_button = ctk.CTkButton(
            self.card_frame,
            text="Login",
            height=38,
            corner_radius=10,
            fg_color="#0d74d1",
            hover_color="#0b63b3",
            command=self.handle_login,
        )
        self.login_button.grid(row=7, column=0, padx=24, pady=(10, 24), sticky="ew")

        # Allow pressing Enter to trigger login
        self.bind("<Return>", lambda event: self.handle_login())

    def handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showwarning("Validation", "Please enter username and password.")
            return

        role = self.authenticate(username, password)

        if role is not None:
            # Log successful login
            try:
                log_activity(username, role, "login_success", "User logged in")
            except Exception:
                pass

            # Respect system setting for showing login success popup
            show_popup = True
            try:
                show_popup = get_setting("show_login_success_popup", "1") == "1"
            except Exception:
                pass
            if show_popup:
                messagebox.showinfo("Login Success", f"Welcome {username} (role: {role})")
            # TODO: Here you can open your main window based on role
            # e.g., open_admin_dashboard() or open_receptionist_dashboard()
            # For now we just close the login window
            self.authenticated = True
            self.logged_in_user = username
            self.logged_in_role = role
            self.destroy()
        else:
            try:
                log_activity(username or None, None, "login_failed", "Invalid credentials or role")
            except Exception:
                pass
            messagebox.showerror("Login Failed", "Invalid credentials or role.")

    def toggle_password_visibility(self):
        if self.show_password:
            self.password_entry.configure(show="*")
            self.eye_button.configure(text="👁")
            self.show_password = False
        else:
            self.password_entry.configure(show="")
            self.eye_button.configure(text="✖")
            self.show_password = True

    @staticmethod
    def authenticate(username: str, password: str):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute(
            "SELECT role FROM users WHERE username = ? AND password = ?",
            (username, password),
        )
        row = cur.fetchone()

        conn.close()
        if row is None:
            return None
        return row[0]


def main():
    init_db(DB_NAME)
    app = LoginApp()
    app.mainloop()


if __name__ == "__main__":
    main()
