import os
import sys
import sqlite3
import random
import customtkinter as ctk
from tkinter import messagebox, PhotoImage

from database import DB_NAME, init_db, get_setting, log_activity


class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window config
        self.title("MEDISKED - Login")
        self.geometry("400x520")
        self.resizable(False, False)

        # Window icon
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

        # Center window
        self.update_idletasks()
        width = 400
        height = 520
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Set appearance - Dark & Minimal
        ctk.set_appearance_mode("dark")
        self.bg_color = "#0f172a"
        self.configure(fg_color=self.bg_color)  # Deep dark slate background

        # Auth state
        self.authenticated = False
        self.logged_in_user = None
        self.logged_in_role = None

        # Main Layout - Centered Column
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Check for recent logins
        recent_users = self._fetch_recent_users()
        if recent_users:
            # Expand window slightly for the cards view if needed, 
            # but 400x520 might be tight for 3 cards horizontally. 
            # Steam does it horizontally. Let's adjust geometry for this view.
            self.geometry(f"600x450+{x-100}+{y+35}")
            self._build_recent_logins_view(recent_users)
        else:
            self._build_login_form()

    def _fetch_recent_users(self):
        """Fetch up to 3 recent unique logins with their avatars."""
        try:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            # Join with users to get profile image if available
            cur.execute("""
                SELECT r.username, u.profile_image_path, u.full_name
                FROM recent_logins r
                LEFT JOIN users u ON r.username = u.username
                ORDER BY r.last_login DESC
                LIMIT 3
            """)
            rows = cur.fetchall() # [(username, path, full_name), ...]
            conn.close()
            return rows
        except Exception:
            return []

    def _clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    def _build_recent_logins_view(self, recent_users):
        self._clear_window()
        self.title("MEDISKED - Saved Login") 
        
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Title
        ctk.CTkLabel(
            container, 
            text="Login as..", 
            font=("Segoe UI", 24, "bold"), 
            text_color="white"
        ).pack(pady=(20, 40))

        # Cards container
        cards_frame = ctk.CTkFrame(container, fg_color="transparent")
        cards_frame.pack()

        from PIL import Image
        
        def create_user_card(parent, username, img_path, display_name):
            card = ctk.CTkButton(
                parent,
                text="",
                width=110,
                height=140,
                fg_color="#1e293b",
                hover_color="#334155",
                corner_radius=10,
                border_width=0,
                command=lambda: self._switch_to_login(username)
            )
            
            # Helper: We can't put widgets inside a rounded CTkButton easily unless we use a Frame and bind click.
            # So let's use a Frame that acts as a button.
            card_frame = ctk.CTkFrame(parent, width=110, height=140, fg_color="#1e293b", corner_radius=10)
            
            # Hover effects
            def on_enter(e): card_frame.configure(fg_color="#334155")
            def on_leave(e): card_frame.configure(fg_color="#1e293b")
            card_frame.bind("<Enter>", on_enter)
            card_frame.bind("<Leave>", on_leave)
            
            # Click event
            def on_click(e): self._switch_to_login(username)
            card_frame.bind("<Button-1>", on_click)

            # Avatar
            avatar_img = None
            if img_path and os.path.exists(img_path):
                try:
                    pil_img = Image.open(img_path)
                    avatar_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(70, 70))
                except: pass
            
            lbl_img = ctk.CTkLabel(
                card_frame, 
                text="👤" if not avatar_img else "", 
                image=avatar_img,
                font=("Segoe UI", 40) if not avatar_img else None,
                width=70, height=70
            )
            lbl_img.place(relx=0.5, rely=0.4, anchor="center")
            
            # Bind events to children too
            lbl_img.bind("<Button-1>", on_click)
            lbl_img.bind("<Enter>", on_enter)
            lbl_img.bind("<Leave>", on_leave)

            # Name
            lbl_name = ctk.CTkLabel(card_frame, text=display_name, font=("Segoe UI", 12, "bold"), text_color="white")
            lbl_name.place(relx=0.5, rely=0.8, anchor="center")
            lbl_name.bind("<Button-1>", on_click)
            lbl_name.bind("<Enter>", on_enter)
            lbl_name.bind("<Leave>", on_leave)

            return card_frame

        for i, (uname, path, full_name) in enumerate(recent_users):
            display_text = full_name if full_name else uname
            c = create_user_card(cards_frame, uname, path, display_text)
            c.grid(row=0, column=i, padx=10, pady=10)

        # Plus button
        plus_frame = ctk.CTkFrame(cards_frame, width=110, height=140, fg_color="#1e293b", corner_radius=10)
        def on_enter_p(e): plus_frame.configure(fg_color="#334155")
        def on_leave_p(e): plus_frame.configure(fg_color="#1e293b")
        def on_click_p(e): self._switch_to_login(None)
        
        plus_frame.bind("<Enter>", on_enter_p)
        plus_frame.bind("<Leave>", on_leave_p)
        plus_frame.bind("<Button-1>", on_click_p)

        lbl_plus = ctk.CTkLabel(plus_frame, text="+", font=("Segoe UI", 40), text_color="#94a3b8")
        lbl_plus.place(relx=0.5, rely=0.5, anchor="center")
        lbl_plus.bind("<Button-1>", on_click_p)
        
        plus_frame.grid(row=0, column=len(recent_users), padx=10, pady=10)

        # Footer
        footer_label = ctk.CTkLabel(
            self,
            text="2025 MEDISKED",
            font=("Segoe UI", 10),
            text_color="#475569"
        )
        footer_label.place(relx=0.5, rely=0.95, anchor="center")

    def _switch_to_login(self, username_prefill):
        # Reset geometry to original portrait size
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        width, height = 400, 520
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        self._build_login_form(username_prefill)

    def _build_login_form(self, username_prefill=None):
        self._clear_window()
        self.title("MEDISKED - Login")

        # Container Frame (Transparent, just for layout)
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=0, column=0, padx=40, sticky="ew")
        content_frame.grid_columnconfigure(0, weight=1)

        # 1. Header Section
        # Icon/Logo Placeholder
        icon_label = ctk.CTkLabel(
            content_frame,
            text="⚕",  # Medical icon
            font=("Segoe UI", 48),
            text_color="#3b82f6"
        )
        icon_label.grid(row=0, column=0, pady=(0, 10))

        # Title
        title_label = ctk.CTkLabel(
            content_frame,
            text="Welcome Back",
            font=("Segoe UI", 24, "bold"),
            text_color="white"
        )
        title_label.grid(row=1, column=0, pady=(0, 5))

        subtitle_label = ctk.CTkLabel(
            content_frame,
            text="Sign in to continue to Medisked",
            font=("Segoe UI", 13),
            text_color="#94a3b8" # Slate 400
        )
        subtitle_label.grid(row=2, column=0, pady=(0, 40))

        # 2. Input Section
        # Username
        self.username_entry = ctk.CTkEntry(
            content_frame,
            placeholder_text="Username",
            height=50,
            font=("Segoe UI", 14),
            corner_radius=8,
            fg_color="#1e293b",     # Slate 800
            border_color="#334155", # Slate 700
            border_width=1,
            text_color="white",
            placeholder_text_color="#64748b"
        )
        self.username_entry.grid(row=3, column=0, pady=(0, 15), sticky="ew")
        if username_prefill:
            self.username_entry.insert(0, username_prefill)

        # Password Frame (for the eye button)
        password_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        password_frame.grid(row=4, column=0, pady=(0, 10), sticky="ew")
        password_frame.grid_columnconfigure(0, weight=1)

        self.password_entry = ctk.CTkEntry(
            password_frame,
            placeholder_text="Password",
            show="*",
            height=50,
            font=("Segoe UI", 14),
            corner_radius=8,
            fg_color="#1e293b",
            border_color="#334155",
            border_width=1,
            text_color="white",
            placeholder_text_color="#64748b"
        )
        self.password_entry.grid(row=0, column=0, sticky="ew")

        self.show_password = False
        self.eye_button = ctk.CTkButton(
            password_frame,
            text="👁",
            width=30,
            height=30,
            fg_color="transparent",
            hover_color=None,
            text_color="#94a3b8",
            font=("Segoe UI", 16),
            command=self.toggle_password_visibility,
        )
        self.eye_button.place(relx=1.0, rely=0.5, anchor="e", x=-10)
        
        # If prefilled, focus password
        if username_prefill:
            self.password_entry.focus()

        # 3. Actions (Remember / Forgot)
        actions_row = ctk.CTkFrame(content_frame, fg_color="transparent")
        actions_row.grid(row=5, column=0, pady=(0, 30), sticky="ew")
        actions_row.grid_columnconfigure(1, weight=1)

        self.remember_var = ctk.BooleanVar(value=False)
        self.remember_check = ctk.CTkCheckBox(
            actions_row,
            text="Remember me",
            variable=self.remember_var,
            font=("Segoe UI", 12),
            text_color="#cbd5e1",
            fg_color="#3b82f6",
            border_color="#475569",
            hover_color="#3b82f6",
            checkmark_color="white",
            corner_radius=4,
            width=20,
            height=20
        )
        self.remember_check.grid(row=0, column=0, sticky="w")

        self.forgot_label = ctk.CTkLabel(
            actions_row,
            text="Forgot password?",
            font=("Segoe UI", 12, "bold"),
            text_color="#3b82f6",
            cursor="hand2"
        )
        self.forgot_label.grid(row=0, column=1, sticky="e")
        self.forgot_label.bind("<Button-1>", lambda _e: self.open_forgot_password())

        # 4. Login Button
        self.login_button = ctk.CTkButton(
            content_frame,
            text="Sign In",
            font=("Segoe UI", 15, "bold"),
            height=50,
            corner_radius=8,
            fg_color="#3b82f6",     # Blue 500
            hover_color="#2563eb",  # Blue 600
            text_color="white",
            command=self.handle_login,
        )
        self.login_button.grid(row=6, column=0, sticky="ew")

        # Footer
        footer_label = ctk.CTkLabel(
            self,
            text="© 2025 Medisked System",
            font=("Segoe UI", 10),
            text_color="#475569"
        )
        footer_label.place(relx=0.5, rely=0.95, anchor="center")

        # Key binding
        self.bind("<Return>", lambda event: self.handle_login())

    def _record_recent_login(self, username):
        try:
            from datetime import datetime
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            # Upsert
            cur.execute("""
                INSERT INTO recent_logins (username, last_login) VALUES (?, ?)
                ON CONFLICT(username) DO UPDATE SET last_login = excluded.last_login
            """, (username, ts))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def open_forgot_password(self):
        """Open a window to request a password reset from the admin.

        User must enter their username and last password. A request is
        stored for the admin to review in the Manage Accounts > Requests tab.
        """

        win = ctk.CTkToplevel(self)
        win.title("Forgot Password")
        win.geometry("400x320")
        win.resizable(False, False)
        win.configure(fg_color="#0f172a") # Theme BG
        win.transient(self)
        win.grab_set()

        win.grid_rowconfigure(1, weight=1)
        win.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            win,
            text="Reset Password",
            font=("Segoe UI", 18, "bold"),
            text_color="white"
        )
        title.grid(row=0, column=0, padx=24, pady=(20, 5), sticky="w")

        body = ctk.CTkFrame(win, fg_color="transparent")
        body.grid(row=1, column=0, padx=24, pady=(5, 20), sticky="nsew")
        body.grid_columnconfigure(0, weight=1)

        info = ctk.CTkLabel(
            body,
            text="Enter your username and last known password.\nA reset request will be sent to the admin.",
            font=("Segoe UI", 12),
            text_color="#94a3b8", # Slate 400
            anchor="w",
            justify="left",
        )
        info.grid(row=0, column=0, pady=(0, 15), sticky="w")

        username_entry = ctk.CTkEntry(
            body, 
            placeholder_text="Username",
            height=40,
            font=("Segoe UI", 13),
            corner_radius=6,
            fg_color="#1e293b",
            border_color="#334155",
            border_width=1,
            text_color="white",
            placeholder_text_color="#64748b"
        )
        username_entry.grid(row=1, column=0, pady=(0, 10), sticky="ew")

        password_entry = ctk.CTkEntry(
            body, 
            placeholder_text="Last password", 
            show="*",
            height=40,
            font=("Segoe UI", 13),
            corner_radius=6,
            fg_color="#1e293b",
            border_color="#334155",
            border_width=1,
            text_color="white",
            placeholder_text_color="#64748b"
        )
        password_entry.grid(row=2, column=0, pady=(0, 20), sticky="ew")

        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.grid(row=3, column=0, sticky="ew")
        btn_row.grid_columnconfigure(1, weight=1)

        def _send():
            uname = username_entry.get().strip()
            last_pwd = password_entry.get().strip()

            if not uname or not last_pwd:
                messagebox.showwarning("Validation", "Please fill in all fields.")
                return

            import sqlite3
            from datetime import datetime

            ts = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

            try:
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()

                # Ensure username exists
                cur.execute("SELECT 1 FROM users WHERE username = ?", (uname,))
                if cur.fetchone() is None:
                    conn.close()
                    messagebox.showerror("Error", "Username does not exist in the system.")
                    return

                cur.execute(
                    "INSERT INTO password_reset_requests (username, last_password, requested_at) VALUES (?, ?, ?)",
                    (uname, last_pwd, ts),
                )
                conn.commit()
                conn.close()
            except Exception as exc:
                messagebox.showerror("Error", f"Failed to send request: {exc}")
                return

            try:
                log_activity(uname, None, "password_reset_request", "User requested password reset")
            except Exception:
                pass

            messagebox.showinfo(
                "Request Sent",
                "Your password reset request has been sent to the admin.",
            )
            win.destroy()

        cancel_btn = ctk.CTkButton(
            btn_row, 
            text="Cancel", 
            width=100,
            fg_color="transparent", 
            border_width=1,
            border_color="#475569",
            text_color="#cbd5e1",
            hover_color="#1e293b",
            command=win.destroy
        )
        cancel_btn.pack(side="left")

        send_btn = ctk.CTkButton(
            btn_row, 
            text="Send Request", 
            width=140, 
            fg_color="#3b82f6",
            hover_color="#2563eb",
            text_color="white",
            command=_send
        )
        send_btn.pack(side="right")

        # Center
        self.update_idletasks()
        win.update_idletasks()
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        win.geometry(f"+{parent_x + (self.winfo_width()-400)//2}+{parent_y + (self.winfo_height()-320)//2}")

    def handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            return

        role = self.authenticate(username, password)

        if role is not None:
            try:
                log_activity(username, role, "login_success", "User logged in")
            except Exception:
                pass

            show_popup = True
            try:
                show_popup = get_setting("show_login_success_popup", "1") == "1"
            except Exception:
                pass

            def _complete_login():
                if show_popup:
                    # Show custom styled success popup
                    succ = ctk.CTkToplevel(self)
                    succ.title("")
                    succ.geometry("300x160")
                    succ.configure(fg_color="#0f172a") # Theme BG
                    succ.overrideredirect(True) # Frameless
                    
                    # Center on screen
                    sw = self.winfo_screenwidth()
                    sh = self.winfo_screenheight()
                    succ.geometry(f"+{(sw-300)//2}+{(sh-160)//2}")
                    
                    # Container frame with border
                    container = ctk.CTkFrame(
                        succ, 
                        fg_color="#0f172a", 
                        border_width=2, 
                        border_color="#3b82f6",
                        corner_radius=0
                    )
                    container.pack(expand=True, fill="both")

                    # Content
                    ctk.CTkLabel(container, text="✅", font=("Segoe UI", 40)).pack(pady=(20, 5))
                    ctk.CTkLabel(container, text="Login Successful", font=("Segoe UI", 16, "bold"), text_color="white").pack(pady=0)
                    ctk.CTkLabel(container, text=f"Welcome, {username}", font=("Segoe UI", 12), text_color="#94a3b8").pack(pady=(5, 0))

                    succ.after(1500, succ.destroy)
                    self.after(1600, lambda: self._finalize_login(username, role))
                else:
                    self._finalize_login(username, role)
            
            # Record this successful login for "Who's playing?" screen
            self._record_recent_login(username)

            self._show_login_loading(_complete_login)
        else:
            try:
                log_activity(username or None, None, "login_failed", "Invalid credentials or role")
            except Exception:
                pass
            messagebox.showerror("Login Failed", "Invalid credentials or role.")

    def _finalize_login(self, username, role):
        self.authenticated = True
        self.logged_in_user = username
        self.logged_in_role = role
        self.destroy()

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

    # ------------------------------------------------------------------
    # Fake loading dialog for more realistic login feedback
    # ------------------------------------------------------------------

    def _show_login_loading(self, on_done):
        """Show a small 'Logging you in...' window for a short random delay."""
        delay_ms = random.randint(1200, 2000)

        win = ctk.CTkToplevel(self)
        win.title("")
        win.geometry("280x140")
        win.resizable(False, False)
        win.configure(fg_color="#0f172a") # Theme BG
        win.transient(self)
        win.grab_set()
        
        # Center relative to parent
        self.update_idletasks()
        win.update_idletasks()
        px = self.winfo_rootx()
        py = self.winfo_rooty()
        win.geometry(f"+{px + (self.winfo_width()-280)//2}+{py + (self.winfo_height()-140)//2}")

        win.grid_rowconfigure(0, weight=1)
        win.grid_columnconfigure(0, weight=1)

        # Spinner/Text
        ctk.CTkLabel(
            win,
            text="↻",
            font=("Segoe UI", 36),
            text_color="#3b82f6"
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            win,
            text="Verifying credentials...",
            font=("Segoe UI", 12, "bold"),
            text_color="white"
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            win,
            text="Please wait...",
            font=("Segoe UI", 11),
            text_color="#64748b"
        ).pack(pady=(0, 15))

        def _finish():
            try:
                win.destroy()
            except Exception:
                pass
            on_done()

        win.after(delay_ms, _finish)


def main():
    init_db(DB_NAME)
    app = LoginApp()
    app.mainloop()


if __name__ == "__main__":
    main()
