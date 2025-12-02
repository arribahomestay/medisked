import sqlite3

import customtkinter as ctk
from tkinter import messagebox

from database import DB_NAME, log_activity
from profile_window import ProfileWindow


class ManageAccountsWindow(ctk.CTkToplevel):
    def __init__(self, master, username: str):
        super().__init__(master)

        self.title("Account Management")
        width, height = 580, 470
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
        self.grid_rowconfigure(2, weight=1)

        title = ctk.CTkLabel(self, text="Account Management", font=("Segoe UI", 20, "bold"))
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        top_row.grid_columnconfigure(0, weight=0)
        top_row.grid_columnconfigure(1, weight=0)
        top_row.grid_columnconfigure(2, weight=1)

        add_tab_btn = ctk.CTkButton(top_row, text="Add Staff Account", command=self.show_add_tab)
        add_tab_btn.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="w")

        users_btn = ctk.CTkButton(top_row, text="Users", command=self.toggle_users_view)
        users_btn.grid(row=0, column=1, padx=(0, 0), pady=0, sticky="w")
        
        self.add_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.add_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.add_frame.grid_columnconfigure(0, weight=1)

        section_label = ctk.CTkLabel(
            self.add_frame,
            text="Add Staff Account",
            font=("Segoe UI", 16, "bold"),
        )
        section_label.grid(row=0, column=0, padx=0, pady=(10, 5), sticky="w")

        info = ctk.CTkLabel(
            self.add_frame,
            text="Create new receptionist or doctor accounts.",
            font=("Segoe UI", 11),
        )
        info.grid(row=1, column=0, padx=0, pady=(0, 10), sticky="w")

        
        user_label = ctk.CTkLabel(self.add_frame, text="Username", font=("Segoe UI", 12))
        user_label.grid(row=2, column=0, padx=0, pady=(5, 0), sticky="w")

        self.new_username_entry = ctk.CTkEntry(self.add_frame)
        self.new_username_entry.grid(row=3, column=0, padx=0, pady=(0, 10), sticky="ew")

        
        pwd_label = ctk.CTkLabel(self.add_frame, text="Password", font=("Segoe UI", 12))
        pwd_label.grid(row=4, column=0, padx=0, pady=(5, 0), sticky="w")

        self.new_password_entry = ctk.CTkEntry(self.add_frame, show="*")
        self.new_password_entry.grid(row=5, column=0, padx=0, pady=(0, 10), sticky="ew")

        
        role_label = ctk.CTkLabel(self.add_frame, text="Role", font=("Segoe UI", 12))
        role_label.grid(row=6, column=0, padx=0, pady=(5, 0), sticky="w")

        self.role_combo = ctk.CTkComboBox(
            self.add_frame,
            values=["receptionist", "doctor", "cashier"],
            state="readonly",
        )
        self.role_combo.set("receptionist")
        self.role_combo.grid(row=7, column=0, padx=0, pady=(0, 10), sticky="ew")

        add_btn = ctk.CTkButton(self.add_frame, text="Add Account", command=self.add_account)
        add_btn.grid(row=8, column=0, padx=0, pady=(10, 10), sticky="e")

        
        self.users_frame = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.users_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        self.users_frame.grid_columnconfigure(0, weight=1)
        self.users_frame.grid_columnconfigure(1, weight=1)
        self.users_frame.grid_columnconfigure(2, weight=1)
        self.users_frame.grid_remove()

    def open_profile(self):
        ProfileWindow(self, username=self.username)

    def show_add_tab(self):
        """Switch to the Add Staff Account tab."""
        
        self.users_frame.grid_remove()
        self.add_frame.grid()

    def toggle_users_view(self):
        """Toggle between Add Account view and Users list view."""
        if self.users_frame.winfo_ismapped():
            
            self.users_frame.grid_remove()
            self.add_frame.grid()
            return

        
        for child in self.users_frame.winfo_children():
            child.destroy()

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT username, COALESCE(full_name, ''), role
                FROM users
                ORDER BY role, username
                """
            )
            rows = cur.fetchall()
        finally:
            conn.close()

        if not rows:
            lbl = ctk.CTkLabel(self.users_frame, text="No users found.")
            lbl.grid(row=0, column=0, padx=8, pady=8, sticky="w")
            self.add_frame.grid_remove()
            self.users_frame.grid()
            return

        
        header_padx = 4
        ctk.CTkLabel(
            self.users_frame, text="Username", font=("Segoe UI", 11, "bold")
        ).grid(row=0, column=0, sticky="w", padx=(header_padx, 2), pady=(4, 2))
        ctk.CTkLabel(
            self.users_frame, text="Name", font=("Segoe UI", 11, "bold")
        ).grid(row=0, column=1, sticky="w", padx=2, pady=(4, 2))
        ctk.CTkLabel(
            self.users_frame, text="Role", font=("Segoe UI", 11, "bold")
        ).grid(row=0, column=2, sticky="w", padx=(2, header_padx), pady=(4, 2))

        for idx, (uname, full_name, role) in enumerate(rows, start=1):
            row_index = idx
            ctk.CTkLabel(self.users_frame, text=uname).grid(
                row=row_index, column=0, sticky="w", padx=(header_padx, 2), pady=1
            )
            ctk.CTkLabel(self.users_frame, text=full_name or "-").grid(
                row=row_index, column=1, sticky="w", padx=2, pady=1
            )
            ctk.CTkLabel(self.users_frame, text=role).grid(
                row=row_index, column=2, sticky="w", padx=(2, header_padx), pady=1
            )

        
        self.add_frame.grid_remove()
        self.users_frame.grid()

    def add_account(self):
        username = self.new_username_entry.get().strip()
        password = self.new_password_entry.get().strip()
        role = self.role_combo.get().strip() if hasattr(self, "role_combo") else "receptionist"

        if not username or not password:
            messagebox.showwarning("Validation", "Username and password are required.")
            return

        if role not in ("receptionist", "doctor", "cashier"):
            messagebox.showwarning("Validation", "Role must be 'receptionist', 'doctor', or 'cashier'.")
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, password, role),
            )

           
            if role == "doctor":
                cur.execute(
                    "SELECT id FROM doctors WHERE name = ?",
                    (username,),
                )
                row = cur.fetchone()
                if row is None:
                    cur.execute(
                        "INSERT INTO doctors (name, specialty, status, notes) VALUES (?, NULL, 'active', NULL)",
                        (username,),
                    )

            conn.commit()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists.")
            conn.close()
            return
        conn.close()
        messagebox.showinfo("Account", f"{role.capitalize()} account created.")
        try:
            log_activity(self.username, "admin", "create_user", f"Created {role} account '{username}'")
        except Exception:
            pass
        self.new_username_entry.delete(0, "end")
        self.new_password_entry.delete(0, "end")
        if hasattr(self, "role_combo"):
            self.role_combo.set("receptionist")
