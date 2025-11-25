import sqlite3

import customtkinter as ctk
from tkinter import messagebox

from database import DB_NAME


class ProfileWindow(ctk.CTkToplevel):
    def __init__(self, master, username: str):
        super().__init__(master)

        self.title("Profile Settings")
        width, height = 420, 340
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)

        self.transient(master)
        self.update_idletasks()
        master_x = master.winfo_rootx()
        master_y = master.winfo_rooty()
        master_w = master.winfo_width()
        master_h = master.winfo_height()
        x = master_x + (master_w - width) // 2
        y = master_y + (master_h - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.username = username

        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(self, text="Profile Settings", font=("Segoe UI", 20, "bold"))
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Load existing full_name if present
        self.full_name = self._load_full_name()

        # Username (editable)
        user_label = ctk.CTkLabel(self, text="Username", font=("Segoe UI", 12))
        user_label.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")

        self.username_entry = ctk.CTkEntry(self)
        self.username_entry.insert(0, self.username)
        self.username_entry.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Name / full name
        name_label = ctk.CTkLabel(self, text="Name", font=("Segoe UI", 12))
        name_label.grid(row=3, column=0, padx=20, pady=(10, 0), sticky="w")

        self.name_entry = ctk.CTkEntry(self)
        if self.full_name:
            self.name_entry.insert(0, self.full_name)
        self.name_entry.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Password (editable)
        pwd_label = ctk.CTkLabel(self, text="Password", font=("Segoe UI", 12))
        pwd_label.grid(row=5, column=0, padx=20, pady=(10, 0), sticky="w")

        self.password_entry = ctk.CTkEntry(self, show="*")
        self.password_entry.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")

        save_button = ctk.CTkButton(self, text="Save", command=self.save_profile)
        save_button.grid(row=7, column=0, padx=20, pady=(10, 10), sticky="e")

    def _load_full_name(self) -> str | None:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        try:
            cur.execute("SELECT full_name FROM users WHERE username = ?", (self.username,))
            row = cur.fetchone()
            return row[0] if row and row[0] is not None else None
        except sqlite3.OperationalError:
            # Column may not exist yet on very old DBs
            return None
        finally:
            conn.close()

    def save_profile(self):
        new_username = self.username_entry.get().strip()
        new_name = self.name_entry.get().strip()
        new_password = self.password_entry.get().strip()

        if not new_username or not new_password:
            messagebox.showwarning("Validation", "Username and password cannot be empty.")
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # If username changed, ensure it's unique
        if new_username != self.username:
            cur.execute("SELECT COUNT(*) FROM users WHERE username = ?", (new_username,))
            if cur.fetchone()[0] > 0:
                conn.close()
                messagebox.showerror("Error", "Username already exists.")
                return

        cur.execute(
            "UPDATE users SET username = ?, password = ?, full_name = ? WHERE username = ?",
            (new_username, new_password, new_name or None, self.username),
        )
        conn.commit()
        conn.close()

        self.username = new_username

        messagebox.showinfo(
            "Profile",
            "Profile updated successfully. Use the new username the next time you log in.",
        )
        self.destroy()
