import sqlite3

import customtkinter as ctk
from tkinter import messagebox

from database import DB_NAME, log_activity


class AdminManageAccountsPage(ctk.CTkFrame):
    def __init__(self, master, username: str):
        super().__init__(master, corner_radius=0)

        self.username = username

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        title = ctk.CTkLabel(self, text="Account Management", font=("Segoe UI", 20, "bold"))
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        top_row.grid_columnconfigure(0, weight=0)
        top_row.grid_columnconfigure(1, weight=0)
        top_row.grid_columnconfigure(2, weight=0)
        top_row.grid_columnconfigure(3, weight=1)

        add_tab_btn = ctk.CTkButton(top_row, text="Add Staff Account", command=self.show_add_tab)
        add_tab_btn.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="w")

        users_btn = ctk.CTkButton(top_row, text="Users", command=self.toggle_users_view)
        users_btn.grid(row=0, column=1, padx=(0, 0), pady=0, sticky="w")

        requests_btn = ctk.CTkButton(top_row, text="Requests", command=self.show_requests)
        requests_btn.grid(row=0, column=2, padx=(10, 0), pady=0, sticky="w")

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
        self.users_frame.grid_columnconfigure(3, weight=0)
        self.users_frame.grid_remove()

        self.requests_frame = ctk.CTkScrollableFrame(self, corner_radius=10)
        self.requests_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.requests_frame.grid_columnconfigure(0, weight=1)
        self.requests_frame.grid_columnconfigure(1, weight=1)
        self.requests_frame.grid_columnconfigure(2, weight=1)
        self.requests_frame.grid_columnconfigure(3, weight=1)
        self.requests_frame.grid_remove()

    def show_add_tab(self):
        self.users_frame.grid_remove()
        self.requests_frame.grid_remove()
        self.add_frame.grid()

    def toggle_users_view(self):
        if self.users_frame.winfo_ismapped():
            self.users_frame.grid_remove()
            self.add_frame.grid()
            return

        self.add_frame.grid_remove()
        self.requests_frame.grid_remove()
        self._refresh_users_list()

    def show_requests(self):
        """Show password reset requests sent from the login screen."""

        self.add_frame.grid_remove()
        self.users_frame.grid_remove()

        for child in self.requests_frame.winfo_children():
            child.destroy()

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        try:
            # Join to users to show the current stored password alongside the
            # last password the user claims to remember.
            cur.execute(
                """
                SELECT r.id,
                       r.username,
                       r.last_password,
                       COALESCE(u.password, ''),
                       r.requested_at
                FROM password_reset_requests AS r
                LEFT JOIN users AS u ON u.username = r.username
                ORDER BY r.id DESC
                """
            )
            rows = cur.fetchall()
        finally:
            conn.close()

        if not rows:
            lbl = ctk.CTkLabel(self.requests_frame, text="No password reset requests.")
            lbl.grid(row=0, column=0, padx=8, pady=8, sticky="w")
            self.requests_frame.grid()
            return

        header_padx = 4
        ctk.CTkLabel(
            self.requests_frame, text="Username", font=("Segoe UI", 11, "bold")
        ).grid(row=0, column=0, sticky="w", padx=(header_padx, 2), pady=(4, 2))
        ctk.CTkLabel(
            self.requests_frame, text="Last password (user)", font=("Segoe UI", 11, "bold")
        ).grid(row=0, column=1, sticky="w", padx=2, pady=(4, 2))
        ctk.CTkLabel(
            self.requests_frame, text="Current password", font=("Segoe UI", 11, "bold")
        ).grid(row=0, column=2, sticky="w", padx=2, pady=(4, 2))
        ctk.CTkLabel(
            self.requests_frame, text="Requested at", font=("Segoe UI", 11, "bold")
        ).grid(row=0, column=3, sticky="w", padx=2, pady=(4, 2))
        ctk.CTkLabel(
            self.requests_frame, text="Actions", font=("Segoe UI", 11, "bold")
        ).grid(row=0, column=4, sticky="e", padx=2, pady=(4, 2))

        for idx, (req_id, uname, last_pwd, current_pwd, ts) in enumerate(rows, start=1):
            row_index = idx
            ctk.CTkLabel(self.requests_frame, text=uname).grid(
                row=row_index, column=0, sticky="w", padx=(header_padx, 2), pady=1
            )
            ctk.CTkLabel(self.requests_frame, text=last_pwd or "-").grid(
                row=row_index, column=1, sticky="w", padx=2, pady=1
            )
            ctk.CTkLabel(self.requests_frame, text=ts).grid(
                row=row_index, column=3, sticky="w", padx=2, pady=1
            )
            ctk.CTkLabel(self.requests_frame, text=current_pwd or "-").grid(
                row=row_index, column=2, sticky="w", padx=2, pady=1
            )

            action_frame = ctk.CTkFrame(self.requests_frame, fg_color="transparent")
            action_frame.grid(row=row_index, column=4, padx=2, pady=1, sticky="e")

            edit_btn = ctk.CTkButton(
                action_frame,
                text="Edit password",
                width=120,
                command=lambda u=uname, rid=req_id: self._edit_password_from_request(u, rid),
            )
            edit_btn.grid(row=0, column=0, padx=(0, 4))

            clear_btn = ctk.CTkButton(
                action_frame,
                text="Mark as handled",
                width=130,
                command=lambda rid=req_id: self._clear_request(rid),
            )
            clear_btn.grid(row=0, column=1)

        self.requests_frame.grid()

    def _clear_request(self, request_id: int):
        """Delete a password reset request and refresh the list."""

        import sqlite3

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM password_reset_requests WHERE id = ?", (request_id,))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            conn.close()
            messagebox.showerror("Requests", f"Failed to clear request: {exc}")
            return
        conn.close()

        self.show_requests()

    def _edit_password_from_request(self, username: str, request_id: int):
        """Open a small dialog that lets the admin change a user's password
        for a given request, then automatically marks that request as handled.
        """

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        conn.close()
        if row is None:
            messagebox.showerror("Edit Password", "User no longer exists.")
            return

        current_password = row[0]

        win = ctk.CTkToplevel(self)
        win.title(f"Edit password for {username}")
        win.geometry("380x200")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()

        win.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(win, text=f"Change password: {username}", font=("Segoe UI", 15, "bold"))
        title.grid(row=0, column=0, padx=20, pady=(16, 4), sticky="w")

        info = ctk.CTkLabel(
            win,
            text="Enter a new password for this account.",
            font=("Segoe UI", 11),
        )
        info.grid(row=1, column=0, padx=20, pady=(0, 8), sticky="w")

        pwd_entry = ctk.CTkEntry(win, show="*", placeholder_text="New password")
        pwd_entry.grid(row=2, column=0, padx=20, pady=(0, 12), sticky="ew")

        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.grid(row=3, column=0, padx=20, pady=(4, 16), sticky="e")

        def _save():
            new_pwd = pwd_entry.get().strip()
            if not new_pwd:
                messagebox.showwarning("Edit Password", "New password cannot be empty.")
                return

            conn2 = sqlite3.connect(DB_NAME)
            cur2 = conn2.cursor()
            try:
                cur2.execute(
                    "UPDATE users SET password = ? WHERE username = ?",
                    (new_pwd, username),
                )
                conn2.commit()
            except Exception as exc:
                conn2.rollback()
                conn2.close()
                messagebox.showerror("Edit Password", f"Failed to update password: {exc}")
                return
            conn2.close()

            try:
                log_activity(self.username, "admin", "reset_password", f"Reset password for '{username}' from request")
            except Exception:
                pass

            # Automatically clear the request after a successful password change
            self._clear_request(request_id)

            messagebox.showinfo("Edit Password", "Password updated and request marked as handled.")
            try:
                win.destroy()
            except Exception:
                pass

        cancel_btn = ctk.CTkButton(btn_row, text="Cancel", width=80, command=win.destroy)
        cancel_btn.grid(row=0, column=0, padx=(0, 8))

        save_btn = ctk.CTkButton(btn_row, text="Save", width=90, command=_save)
        save_btn.grid(row=0, column=1)

        # Center the edit-password window over the main admin window
        self.update_idletasks()
        win.update_idletasks()
        parent = self.winfo_toplevel()
        parent.update_idletasks()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        ww = win.winfo_width()
        wh = win.winfo_height()
        x = px + (pw - ww) // 2
        y = py + (ph - wh) // 2
        win.geometry(f"{ww}x{wh}+{x}+{y}")

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

    def _refresh_users_list(self):
        """(Re)build the Users list with edit/delete actions."""

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
        ctk.CTkLabel(
            self.users_frame, text="Actions", font=("Segoe UI", 11, "bold")
        ).grid(row=0, column=3, sticky="e", padx=(2, header_padx), pady=(4, 2))

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

            actions = ctk.CTkFrame(self.users_frame, fg_color="transparent")
            actions.grid(row=row_index, column=3, padx=(2, header_padx), pady=1, sticky="e")

            edit_btn = ctk.CTkButton(
                actions,
                text="Edit",
                width=70,
                command=lambda u=uname: self._open_edit_user(u),
            )
            edit_btn.grid(row=0, column=0, padx=(0, 4))

            del_btn = ctk.CTkButton(
                actions,
                text="Delete",
                width=70,
                fg_color="#b91c1c",
                hover_color="#991b1b",
                command=lambda u=uname: self._delete_user(u),
            )
            del_btn.grid(row=0, column=1)

        self.add_frame.grid_remove()
        self.users_frame.grid()

    def _open_edit_user(self, username: str):
        """Open a small window to edit a user's name and password."""

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT username, COALESCE(full_name, ''), password, role FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        conn.close()
        if row is None:
            messagebox.showerror("Edit User", "User not found.")
            return

        uname, full_name, current_password, role = row

        win = ctk.CTkToplevel(self)
        win.title("Edit Account")
        win.geometry("420x260")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()

        win.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(win, text=f"Edit account: {uname}", font=("Segoe UI", 16, "bold"))
        title.grid(row=0, column=0, padx=20, pady=(16, 4), sticky="w")

        meta = ctk.CTkLabel(win, text=f"Role: {role}", font=("Segoe UI", 11))
        meta.grid(row=1, column=0, padx=20, pady=(0, 8), sticky="w")

        name_label = ctk.CTkLabel(win, text="Name", font=("Segoe UI", 12))
        name_label.grid(row=2, column=0, padx=20, pady=(4, 0), sticky="w")

        name_entry = ctk.CTkEntry(win)
        name_entry.insert(0, full_name or "")
        name_entry.grid(row=3, column=0, padx=20, pady=(0, 8), sticky="ew")

        pwd_label = ctk.CTkLabel(win, text="New password (leave blank to keep)", font=("Segoe UI", 12))
        pwd_label.grid(row=4, column=0, padx=20, pady=(4, 0), sticky="w")

        pwd_entry = ctk.CTkEntry(win, show="*")
        pwd_entry.grid(row=5, column=0, padx=20, pady=(0, 12), sticky="ew")

        btn_row = ctk.CTkFrame(win, fg_color="transparent")
        btn_row.grid(row=6, column=0, padx=20, pady=(4, 16), sticky="e")

        def _save():
            new_name = name_entry.get().strip()
            new_pwd = pwd_entry.get().strip()

            if not new_name:
                # Allow empty full name but confirm
                if not messagebox.askyesno("Edit User", "Name is empty. Continue?"):
                    return

            password_to_save = new_pwd if new_pwd else current_password

            conn2 = sqlite3.connect(DB_NAME)
            cur2 = conn2.cursor()
            cur2.execute(
                "UPDATE users SET full_name = ?, password = ? WHERE username = ?",
                (new_name, password_to_save, uname),
            )
            conn2.commit()
            conn2.close()

            try:
                log_activity(self.username, "admin", "edit_user", f"Updated account '{uname}'")
            except Exception:
                pass

            messagebox.showinfo("Edit User", "Account updated successfully.")
            try:
                win.destroy()
            except Exception:
                pass
            self._refresh_users_list()

        cancel_btn = ctk.CTkButton(btn_row, text="Cancel", width=80, command=win.destroy)
        cancel_btn.grid(row=0, column=0, padx=(0, 8))

        save_btn = ctk.CTkButton(btn_row, text="Save", width=90, command=_save)
        save_btn.grid(row=0, column=1)

        # Center edit window over the main admin window
        self.update_idletasks()
        win.update_idletasks()
        parent = self.winfo_toplevel()
        parent.update_idletasks()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        ww = win.winfo_width()
        wh = win.winfo_height()
        x = px + (pw - ww) // 2
        y = py + (ph - wh) // 2
        win.geometry(f"{ww}x{wh}+{x}+{y}")

    def _delete_user(self, username: str):
        """Delete a user account after confirmation."""

        if username == self.username:
            messagebox.showwarning("Delete User", "You cannot delete the account you are currently logged in with.")
            return

        if not messagebox.askyesno("Delete User", f"Are you sure you want to delete '{username}'?"):
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT role FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        if row is None:
            conn.close()
            messagebox.showerror("Delete User", "User not found.")
            return

        role = row[0]

        try:
            cur.execute("DELETE FROM users WHERE username = ?", (username,))

            # If a doctor account is removed, mark related doctor record inactive (if present)
            if role == "doctor":
                cur.execute(
                    "UPDATE doctors SET status = 'inactive' WHERE name = ?",
                    (username,),
                )

            conn.commit()
        except Exception as exc:
            conn.rollback()
            conn.close()
            messagebox.showerror("Delete User", f"Failed to delete user: {exc}")
            return

        conn.close()

        try:
            log_activity(self.username, "admin", "delete_user", f"Deleted account '{username}'")
        except Exception:
            pass

        messagebox.showinfo("Delete User", "Account deleted successfully.")
        self._refresh_users_list()
