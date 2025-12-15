import sqlite3

import customtkinter as ctk
from tkinter import messagebox

from database import DB_NAME, log_activity


class AdminManageAccountsPage(ctk.CTkFrame):
    def __init__(self, master, username: str):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.username = username

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Header & Controls Card
        header_card = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=16) # Slate 800
        header_card.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        header_card.grid_columnconfigure(0, weight=1)
        header_card.grid_columnconfigure(1, weight=0)

        # Title
        title_frame = ctk.CTkFrame(header_card, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=24, pady=24, sticky="ew")
        
        ctk.CTkLabel(
            title_frame, 
            text="Account Management", 
            font=("Inter", 20, "bold"), 
            text_color="white"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame, 
            text="Manage staff access and permissions.", 
            font=("Inter", 13), 
            text_color="#94a3b8"
        ).pack(anchor="w", pady=(2, 0))

        # Controls (Tabs)
        controls_frame = ctk.CTkFrame(header_card, fg_color="transparent")
        controls_frame.grid(row=0, column=1, padx=24, pady=24, sticky="e")

        def _tab_btn(txt, cmd, color="#3b82f6"): # Blue default
            return ctk.CTkButton(
                controls_frame,
                text=txt,
                font=("Inter", 13, "bold"),
                fg_color=color,
                hover_color="#2563eb",
                height=36,
                corner_radius=8,
                command=cmd
            )

        self.btn_users = _tab_btn("All Users", self.toggle_users_view)
        self.btn_users.pack(side="left", padx=(0, 10))

        self.btn_add = _tab_btn("Add Account", self.show_add_tab, "#10b981") # Green
        self.btn_add.pack(side="left", padx=(0, 10))
        
        self.btn_req = _tab_btn("Requests", self.show_requests, "#f59e0b") # Amber
        self.btn_req.pack(side="left")


        # 2. Content Area (Different views)
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 20))
        self.content_area.grid_columnconfigure(0, weight=1)
        self.content_area.grid_rowconfigure(0, weight=1)

        # -- VIEW: Users List --
        self.users_frame = ctk.CTkScrollableFrame(self.content_area, corner_radius=16, fg_color="#1e293b")
        
        # -- VIEW: Add Account --
        self.add_frame = ctk.CTkFrame(self.content_area, corner_radius=16, fg_color="#1e293b")
        self.add_frame.grid_columnconfigure(0, weight=1)
        
        # Add Account Form Layout
        center_form = ctk.CTkFrame(self.add_frame, fg_color="transparent")
        center_form.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(center_form, text="Create New Account", font=("Inter", 18, "bold"), text_color="white").pack(pady=(0, 8))
        ctk.CTkLabel(center_form, text="Enter credentials for the new staff member.", font=("Inter", 13), text_color="#94a3b8").pack(pady=(0, 24))

        self.new_username_entry = ctk.CTkEntry(center_form, width=320, height=40, placeholder_text="Username", font=("Inter", 13))
        self.new_username_entry.pack(pady=(0, 16))
        
        self.new_password_entry = ctk.CTkEntry(center_form, width=320, height=40, placeholder_text="Password", show="*", font=("Inter", 13))
        self.new_password_entry.pack(pady=(0, 16))
        
        self.role_combo = ctk.CTkComboBox(center_form, width=320, height=40, values=["receptionist", "doctor", "cashier"], state="readonly", font=("Inter", 13))
        self.role_combo.set("receptionist")
        self.role_combo.pack(pady=(0, 24))
        
        ctk.CTkButton(center_form, text="Create Account", width=320, height=40, font=("Inter", 13, "bold"), fg_color="#3b82f6", hover_color="#2563eb", command=self.add_account).pack()


        # -- VIEW: Requests --
        self.requests_frame = ctk.CTkScrollableFrame(self.content_area, corner_radius=16, fg_color="#1e293b")

        # Initial State
        self.toggle_users_view()

    def show_add_tab(self):
        self.users_frame.grid_forget()
        self.requests_frame.grid_forget()
        self.add_frame.grid(row=0, column=0, sticky="nsew")

    def toggle_users_view(self):
        self.add_frame.grid_forget()
        self.requests_frame.grid_forget()
        self.users_frame.grid(row=0, column=0, sticky="nsew")
        self._refresh_users_list()

    def show_requests(self):
        self.add_frame.grid_forget()
        self.users_frame.grid_forget()
        self.requests_frame.grid(row=0, column=0, sticky="nsew")
        self._refresh_requests_list()

    def _refresh_requests_list(self):
        for child in self.requests_frame.winfo_children():
            child.destroy()

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT r.id, r.username, r.last_password, COALESCE(u.password, ''), r.requested_at
                FROM password_reset_requests AS r
                LEFT JOIN users AS u ON u.username = r.username
                ORDER BY r.id DESC
            """)
            rows = cur.fetchall()
        finally:
            conn.close()

        if not rows:
            ctk.CTkLabel(self.requests_frame, text="No active requests.", font=("Inter", 14), text_color="#94a3b8").pack(pady=40)
            return

        # Header
        h_frame = ctk.CTkFrame(self.requests_frame, fg_color="transparent")
        h_frame.pack(fill="x", padx=10, pady=(10,5))
        h_frame.grid_columnconfigure(0, weight=1)
        h_frame.grid_columnconfigure(1, weight=1)
        h_frame.grid_columnconfigure(2, weight=1)
        h_frame.grid_columnconfigure(3, weight=0, minsize=140)

        def _hl(t, c):
             ctk.CTkLabel(h_frame, text=t.upper(), font=("Inter", 11, "bold"), text_color="#64748b", anchor="w").grid(row=0, column=c, sticky="ew", padx=10)
        
        _hl("USERNAME", 0)
        _hl("LAST KNOWN PWD", 1)
        _hl("REQUESTED AT", 2)
        ctk.CTkLabel(h_frame, text="ACTIONS", font=("Inter", 11, "bold"), text_color="#64748b", anchor="e").grid(row=0, column=3, sticky="ew", padx=10)

        for rid, uname, last_pwd, cur_pwd, ts in rows:
            card = ctk.CTkFrame(self.requests_frame, fg_color="#334155", corner_radius=8, border_width=1, border_color="#475569")
            card.pack(fill="x", padx=10, pady=5)
            card.grid_columnconfigure(0, weight=1)
            card.grid_columnconfigure(1, weight=1)
            card.grid_columnconfigure(2, weight=1)
            card.grid_columnconfigure(3, weight=0, minsize=140)

            ctk.CTkLabel(card, text=uname, font=("Inter", 13, "bold"), text_color="white", anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=12)
            ctk.CTkLabel(card, text=last_pwd or "-", font=("Inter", 12), text_color="#cbd5e1", anchor="w").grid(row=0, column=1, sticky="ew", padx=10)
            ctk.CTkLabel(card, text=ts, font=("Inter", 12), text_color="#cbd5e1", anchor="w").grid(row=0, column=2, sticky="ew", padx=10)

            actions = ctk.CTkFrame(card, fg_color="transparent")
            actions.grid(row=0, column=3, sticky="e", padx=10)
            
            ctk.CTkButton(actions, text="Reset", width=60, height=24, font=("Inter", 11), fg_color="#3b82f6", hover_color="#2563eb",
                          command=lambda u=uname, r=rid: self._edit_password_from_request(u, r)).pack(side="left", padx=2)
            ctk.CTkButton(actions, text="Ignore", width=60, height=24, font=("Inter", 11), fg_color="transparent", border_width=1, border_color="#ef4444", text_color="#ef4444", hover_color="#334155",
                          command=lambda r=rid: self._clear_request(r)).pack(side="left", padx=2)


    def _clear_request(self, request_id: int):
        conn = sqlite3.connect(DB_NAME)
        try:
            conn.execute("DELETE FROM password_reset_requests WHERE id = ?", (request_id,))
            conn.commit()
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {e}")
        finally:
            conn.close()
        self._refresh_requests_list()

    def _edit_password_from_request(self, username: str, request_id: int):
        # ... (Reuse existing logic or modernize dialog if preferred. Keeping concise for now)
        # For full consistency, we should modernize the dialog too.
        
        win = ctk.CTkToplevel(self)
        win.title("Reset Password")
        win.geometry("400x250")
        win.configure(fg_color="#0f172a")
        win.transient(self)
        win.grab_set()

        # Center
        win.update_idletasks()
        try:
            x = self.winfo_rootx() + (self.winfo_width() - 400) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 250) // 2
            win.geometry(f"+{x}+{y}")
        except: pass

        ctk.CTkLabel(win, text=f"Reset Password: {username}", font=("Inter", 16, "bold"), text_color="white").pack(pady=(25, 5))
        ctk.CTkLabel(win, text="Enter a new password for this account.", font=("Inter", 12), text_color="#94a3b8").pack(pady=(0, 20))

        pwd_entry = ctk.CTkEntry(win, width=280, placeholder_text="New Password", show="*", fg_color="#1e293b", border_color="#334155", text_color="white")
        pwd_entry.pack(pady=(0, 20))

        def _save():
            new_pwd = pwd_entry.get().strip()
            if not new_pwd: return
            
            conn = sqlite3.connect(DB_NAME)
            try:
                conn.execute("UPDATE users SET password = ? WHERE username = ?", (new_pwd, username))
                conn.commit()
                self._clear_request(request_id)
                messagebox.showinfo("Success", "Password updated.")
                win.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                conn.close()

        ctk.CTkButton(win, text="Save Password", command=_save, width=280, fg_color="#3b82f6", hover_color="#2563eb", font=("Inter", 13, "bold")).pack()


    def add_account(self):
        username = self.new_username_entry.get().strip()
        password = self.new_password_entry.get().strip()
        role = self.role_combo.get().strip()

        if not username or not password:
            messagebox.showwarning("Validation", "Username and password are required.")
            return

        conn = sqlite3.connect(DB_NAME)
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
            
            if role == "doctor":
                # Check if doctor exists, else add
                cur.execute("SELECT id FROM doctors WHERE name = ?", (username,))
                if not cur.fetchone():
                    cur.execute("INSERT INTO doctors (name, status) VALUES (?, 'active')", (username,))
            
            conn.commit()
            messagebox.showinfo("Success", f"{role.capitalize()} account created.")
            try: log_activity(self.username, "admin", "create_user", f"Created {role} '{username}'")
            except: pass
            
            self.new_username_entry.delete(0, "end")
            self.new_password_entry.delete(0, "end")
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists.")
        finally:
            conn.close()

    def _refresh_users_list(self):
        for child in self.users_frame.winfo_children():
            child.destroy()

        conn = sqlite3.connect(DB_NAME)
        try:
            cur = conn.cursor()
            cur.execute("SELECT username, COALESCE(full_name, ''), role FROM users ORDER BY role, username")
            rows = cur.fetchall()
        finally:
            conn.close()

        if not rows:
            ctk.CTkLabel(self.users_frame, text="No accounts found.", font=("Inter", 14), text_color="#94a3b8").pack(pady=40)
            return

        # Header
        h_frame = ctk.CTkFrame(self.users_frame, fg_color="transparent")
        h_frame.pack(fill="x", padx=10, pady=(10,5))
        # Cols: Username(1), Name(1), Role(1), Actions(0)
        h_frame.grid_columnconfigure(0, weight=1, uniform="ucols")
        h_frame.grid_columnconfigure(1, weight=1, uniform="ucols")
        h_frame.grid_columnconfigure(2, weight=1, uniform="ucols")
        h_frame.grid_columnconfigure(3, weight=0, minsize=140)

        def _hl(t, c):
             ctk.CTkLabel(h_frame, text=t.upper(), font=("Inter", 11, "bold"), text_color="#64748b", anchor="w").grid(row=0, column=c, sticky="ew", padx=10)

        _hl("USERNAME", 0)
        _hl("FULL NAME", 1)
        _hl("ROLE", 2)
        ctk.CTkLabel(h_frame, text="ACTIONS", font=("Inter", 11, "bold"), text_color="#64748b", anchor="e").grid(row=0, column=3, sticky="ew", padx=10)

        for uname, full_name, role in rows:
            card = ctk.CTkFrame(self.users_frame, fg_color="#334155", corner_radius=8, border_width=1, border_color="#475569", height=50)
            card.pack(fill="x", padx=10, pady=5)
            
            card.grid_columnconfigure(0, weight=1, uniform="ucols")
            card.grid_columnconfigure(1, weight=1, uniform="ucols")
            card.grid_columnconfigure(2, weight=1, uniform="ucols")
            card.grid_columnconfigure(3, weight=0, minsize=140)

            ctk.CTkLabel(card, text=uname, font=("Inter", 13, "bold"), text_color="white", anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=12)
            ctk.CTkLabel(card, text=full_name or "-", font=("Inter", 12), text_color="#cbd5e1", anchor="w").grid(row=0, column=1, sticky="ew", padx=10)
            
            role_colors = {"admin": "#ef4444", "doctor": "#3b82f6", "cashier": "#10b981", "receptionist": "#f59e0b"}
            r_col = role_colors.get(role, "gray")
            
            ctk.CTkLabel(card, text=role.capitalize(), font=("Inter", 12, "bold"), text_color=r_col, anchor="w").grid(row=0, column=2, sticky="ew", padx=10)

            actions = ctk.CTkFrame(card, fg_color="transparent")
            actions.grid(row=0, column=3, sticky="e", padx=10)

            ctk.CTkButton(actions, text="Edit", width=50, height=24, font=("Inter", 11), fg_color="transparent", border_width=1, border_color="#3b82f6", text_color="#3b82f6", hover_color="#1e293b",
                          command=lambda u=uname: self._open_edit_user(u)).pack(side="left", padx=2)
            ctk.CTkButton(actions, text="Del", width=50, height=24, font=("Inter", 11), fg_color="transparent", border_width=1, border_color="#ef4444", text_color="#ef4444", hover_color="#1e293b",
                          command=lambda u=uname: self._delete_user(u)).pack(side="left", padx=2)


    def _open_edit_user(self, username: str):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT username, COALESCE(full_name, ''), password, role FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        conn.close()
        
        if not row: return
        uname, full_name, pwd, role = row

        win = ctk.CTkToplevel(self)
        win.title("Edit User")
        win.geometry("420x350")
        win.configure(fg_color="#0f172a")
        win.transient(self)
        win.grab_set()
        
        # Center
        win.update_idletasks()
        try:
            x = self.winfo_rootx() + (self.winfo_width() - 420) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 350) // 2
            win.geometry(f"+{x}+{y}")
        except: pass

        ctk.CTkLabel(win, text=f"Edit: {uname}", font=("Inter", 18, "bold"), text_color="white").pack(pady=(25, 5))
        ctk.CTkLabel(win, text=f"Role: {role.capitalize()}", font=("Inter", 12), text_color="#64748b").pack(pady=(0, 20))

        name_e = ctk.CTkEntry(win, width=300, height=36, placeholder_text="Full access name", fg_color="#1e293b", border_color="#334155", text_color="white")
        name_e.pack(pady=5)
        name_e.insert(0, full_name)

        pwd_e = ctk.CTkEntry(win, width=300, height=36, placeholder_text="New Password (optional)", show="*", fg_color="#1e293b", border_color="#334155", text_color="white")
        pwd_e.pack(pady=5)

        def _save():
            n = name_e.get().strip()
            p = pwd_e.get().strip()
            p_final = p if p else pwd
            
            conn = sqlite3.connect(DB_NAME)
            try:
                conn.execute("UPDATE users SET full_name=?, password=? WHERE username=?", (n, p_final, uname))
                conn.commit()
                messagebox.showinfo("Success", "Account updated.")
                win.destroy()
                self._refresh_users_list()
            except Exception as e:
                messagebox.showerror("Error", str(e))
            finally:
                conn.close()

        ctk.CTkButton(win, text="Save Changes", width=300, height=36, fg_color="#3b82f6", hover_color="#2563eb", font=("Inter", 13, "bold"), command=_save).pack(pady=20)


    def _delete_user(self, username: str):
        if username == self.username:
             messagebox.showwarning("Error", "Cannot delete your own account.")
             return
        if not messagebox.askyesno("Confirm", f"Delete account '{username}'?"):
             return
             
        conn = sqlite3.connect(DB_NAME)
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM users WHERE username=?", (username,))
            # Handle doctor linked logic if needed
            cur.execute("UPDATE doctors SET status='inactive' WHERE name=?", (username,))
            conn.commit()
            messagebox.showinfo("Deleted", "Account deleted.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()
        
        self._refresh_users_list()
