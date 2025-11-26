import sqlite3

import customtkinter as ctk
from tkinter import messagebox

from database import DB_NAME


class DoctorProfileWindow(ctk.CTkToplevel):
    def __init__(self, master, username: str, doctor_id: int):
        super().__init__(master)

        self.title("Doctor Profile")
        width, height = 500, 420
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

        self.old_username = username
        self.doctor_id = doctor_id

        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(self, text="Doctor Profile", font=("Segoe UI", 20, "bold"))
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self._load_data()

        user_label = ctk.CTkLabel(self, text="Username", font=("Segoe UI", 12))
        user_label.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")

        self.username_entry = ctk.CTkEntry(self)
        self.username_entry.insert(0, self.username_value or "")
        self.username_entry.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")

        name_label = ctk.CTkLabel(self, text="Name", font=("Segoe UI", 12))
        name_label.grid(row=3, column=0, padx=20, pady=(10, 0), sticky="w")

        self.name_entry = ctk.CTkEntry(self)
        self.name_entry.insert(0, self.name_value or "")
        self.name_entry.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")

        prof_label = ctk.CTkLabel(self, text="Profession", font=("Segoe UI", 12))
        prof_label.grid(row=5, column=0, padx=20, pady=(10, 0), sticky="w")

        self.prof_entry = ctk.CTkEntry(self)
        self.prof_entry.insert(0, self.prof_value or "")
        self.prof_entry.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")

        pwd_label = ctk.CTkLabel(self, text="Password", font=("Segoe UI", 12))
        pwd_label.grid(row=7, column=0, padx=20, pady=(10, 0), sticky="w")

        self.password_entry = ctk.CTkEntry(self, show="*")
        if self.password_value:
            self.password_entry.insert(0, self.password_value)
        self.password_entry.grid(row=8, column=0, padx=20, pady=(0, 10), sticky="ew")

        save_button = ctk.CTkButton(self, text="Save", command=self.save_profile)
        save_button.grid(row=9, column=0, padx=20, pady=(10, 10), sticky="e")

    def _load_data(self):
        self.username_value = None
        self.name_value = None
        self.prof_value = None
        self.password_value = None

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("SELECT username, password FROM users WHERE username = ?", (self.old_username,))
        row = cur.fetchone()
        if row:
            self.username_value, self.password_value = row

        if self.doctor_id is not None:
            cur.execute("SELECT name, specialty FROM doctors WHERE id = ?", (self.doctor_id,))
            row = cur.fetchone()
            if row:
                self.name_value, self.prof_value = row

        conn.close()

    def save_profile(self):
        new_username = self.username_entry.get().strip()
        new_name = self.name_entry.get().strip()
        new_prof = self.prof_entry.get().strip()
        new_password = self.password_entry.get().strip()

        if not new_username or not new_password:
            messagebox.showwarning("Validation", "Username and password cannot be empty.")
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        if new_username != self.old_username:
            cur.execute("SELECT COUNT(*) FROM users WHERE username = ?", (new_username,))
            if cur.fetchone()[0] > 0:
                conn.close()
                messagebox.showerror("Error", "Username already exists.")
                return

        old_doctor_name = None
        if self.doctor_id is not None:
            cur.execute("SELECT name FROM doctors WHERE id = ?", (self.doctor_id,))
            row = cur.fetchone()
            if row:
                old_doctor_name = row[0]

        cur.execute(
            "UPDATE users SET username = ?, password = ? WHERE username = ?",
            (new_username, new_password, self.old_username),
        )

        if self.doctor_id is not None:
            cur.execute(
                "UPDATE doctors SET name = ?, specialty = ? WHERE id = ?",
                (new_name, new_prof, self.doctor_id),
            )

        if old_doctor_name and new_name and new_name != old_doctor_name:
            cur.execute(
                "UPDATE appointments SET doctor_name = ? WHERE doctor_name = ?",
                (new_name, old_doctor_name),
            )

        conn.commit()
        conn.close()

        messagebox.showinfo("Profile", "Profile updated successfully. Please re-login to see name/username changes everywhere.")
        self.destroy()
