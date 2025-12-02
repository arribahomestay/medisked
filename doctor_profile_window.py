import sqlite3

import customtkinter as ctk
from tkinter import messagebox

from database import DB_NAME


class DoctorProfileWindow(ctk.CTkToplevel):
    def __init__(self, master, username: str, doctor_id: int, anchor_widget=None):
        super().__init__(master)

        self.title("Doctor Profile")
        width, height = 420, 420
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)

        self.transient(master)
        self.update_idletasks()

        if anchor_widget is not None:
            # Position the window just below and aligned to the right of the anchor widget
            ax = anchor_widget.winfo_rootx()
            ay = anchor_widget.winfo_rooty()
            aw = anchor_widget.winfo_width()
            ah = anchor_widget.winfo_height()

            x = int(ax + aw - width)
            y = int(ay + ah + 4)
        else:
            master_x = master.winfo_rootx()
            master_y = master.winfo_rooty()
            master_w = master.winfo_width()
            master_h = master.winfo_height()
            x = master_x + (master_w - width) // 2
            y = master_y + (master_h - height) // 2

        self.geometry(f"{width}x{height}+{x}+{y}")

        # Lock window position so it cannot be moved by dragging
        self._fixed_pos = (x, y)
        self._lock_position = False

        def _enforce_position(_event):
            if self._lock_position:
                return
            cur_x, cur_y = self.winfo_x(), self.winfo_y()
            if (cur_x, cur_y) != self._fixed_pos:
                self._lock_position = True
                self.geometry(f"{width}x{height}+{self._fixed_pos[0]}+{self._fixed_pos[1]}")
                self._lock_position = False

        self.bind("<Configure>", _enforce_position)

        self.old_username = username
        self.doctor_id = doctor_id
        self.master_ref = master

        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(self, text="Doctor Profile", font=("Segoe UI", 20, "bold"))
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self._load_data()

        user_label = ctk.CTkLabel(self, text="Username", font=("Segoe UI", 12))
        user_label.grid(row=1, column=0, padx=20, pady=(10, 0), sticky="w")

        self.username_entry = ctk.CTkEntry(self)
        self.username_entry.insert(0, self.username_value or "")
        self.username_entry.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")

        prof_label = ctk.CTkLabel(self, text="Profession", font=("Segoe UI", 12))
        prof_label.grid(row=3, column=0, padx=20, pady=(10, 0), sticky="w")

        self.prof_entry = ctk.CTkEntry(self)
        self.prof_entry.insert(0, self.prof_value or "")
        self.prof_entry.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")

        pwd_label = ctk.CTkLabel(self, text="Password", font=("Segoe UI", 12))
        pwd_label.grid(row=5, column=0, padx=20, pady=(10, 0), sticky="w")

        self.password_entry = ctk.CTkEntry(self, show="*")
        if self.password_value:
            self.password_entry.insert(0, self.password_value)
        self.password_entry.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")

        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.grid(row=7, column=0, padx=20, pady=(10, 10), sticky="e")

        logout_button = ctk.CTkButton(
            buttons_frame,
            text="Logout",
            width=90,
            fg_color="#b91c1c",
            hover_color="#991b1b",
            command=self._logout,
        )
        logout_button.grid(row=0, column=0, padx=(0, 8))

        save_button = ctk.CTkButton(buttons_frame, text="Save", width=80, command=self.save_profile)
        save_button.grid(row=0, column=1)

        close_button = ctk.CTkButton(
            buttons_frame,
            text="Close",
            width=80,
            command=self.destroy,
        )
        close_button.grid(row=0, column=2, padx=(8, 0))

    def _load_data(self):
        self.username_value = None
        self.prof_value = None
        self.password_value = None

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("SELECT username, password FROM users WHERE username = ?", (self.old_username,))
        row = cur.fetchone()
        if row:
            self.username_value, self.password_value = row

        if self.doctor_id is not None:
            cur.execute("SELECT specialty FROM doctors WHERE id = ?", (self.doctor_id,))
            row = cur.fetchone()
            if row:
                (self.prof_value,) = row

        conn.close()

    def save_profile(self):
        new_username = self.username_entry.get().strip()
        new_prof = self.prof_entry.get().strip()
        new_password = self.password_entry.get().strip()

        if not new_username:
            messagebox.showwarning("Validation", "Username cannot be empty.")
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Load existing password so we can keep it if left blank
        cur.execute("SELECT password FROM users WHERE username = ?", (self.old_username,))
        row = cur.fetchone()
        current_password = row[0] if row else ""

        if new_username != self.old_username:
            cur.execute("SELECT COUNT(*) FROM users WHERE username = ?", (new_username,))
            if cur.fetchone()[0] > 0:
                conn.close()
                messagebox.showerror("Error", "Username already exists.")
                return

        password_to_save = new_password if new_password else current_password

        # Remember old doctor name (if any) so we can update appointments
        old_doctor_name = None
        if self.doctor_id is not None:
            cur.execute(
                "SELECT name FROM doctors WHERE id = ?",
                (self.doctor_id,),
            )
            row = cur.fetchone()
            if row:
                old_doctor_name = row[0]

        cur.execute(
            "UPDATE users SET username = ?, password = ? WHERE username = ?",
            (new_username, password_to_save, self.old_username),
        )

        if self.doctor_id is not None:
            # Keep doctor.name aligned with username
            cur.execute(
                "UPDATE doctors SET name = ?, specialty = ? WHERE id = ?",
                (new_username, new_prof, self.doctor_id),
            )

        if old_doctor_name and new_username and new_username != old_doctor_name:
            cur.execute(
                "UPDATE appointments SET doctor_name = ? WHERE doctor_name = ?",
                (new_username, old_doctor_name),
            )

        conn.commit()
        conn.close()

        messagebox.showinfo("Profile", "Profile updated successfully. Please re-login to see name/username changes everywhere.")
        self.destroy()

    def _logout(self):
        from tkinter import messagebox as _mb

        if not hasattr(self.master_ref, "logout"):
            self.destroy()
            return
        if not _mb.askyesno("Confirm Logout", "Are you sure you want to logout?"):
            return
        self.master_ref.should_relogin = True
        self.master_ref.destroy()
        self.destroy()
