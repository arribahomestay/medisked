import os
import sys
from datetime import datetime
import time
import urllib.request
import sqlite3
import customtkinter as ctk
from tkinter import messagebox, PhotoImage
from PIL import Image, ImageDraw

from login import LoginApp
from database import init_db, DB_NAME
from admin_dashboard import AdminDashboard
from doctor_dashboard import DoctorDashboard
from sidebar_receptionist import ReceptionistSidebar
from profile_window import ProfileWindow


class MainApp(ctk.CTk):
    def __init__(self, username: str, role: str):
        super().__init__()

        self.title("MEDISKED: HOSPITAL SCHEDULING AND BILLING MANAGMENT SYSTEM - Receptionist")
        self.geometry("1100x650")
        self.resizable(True, True)

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

        self.update_idletasks()
        width = 1100
        height = 650
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Use a consistent dark background color for this window
        self.configure(fg_color="#020617")

        self.username = username
        self.role = role
        self.should_relogin = False
        self.profile_window = None
        self.account_menu = None

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self.sidebar = ReceptionistSidebar(
            self,
            username=self.username,
            on_appointment=self.show_appointment,
            on_schedule=self.show_schedule,
            on_records=self.show_records,
            on_profile=self.open_profile,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsw", rowspan=2)

        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=20, pady=(60, 20))
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # Bottom status bar
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.grid(row=1, column=1, sticky="ew", padx=20, pady=(0, 10))
        self.status_frame.grid_columnconfigure(0, weight=0)
        self.status_frame.grid_columnconfigure(1, weight=1)

        self.net_status_label = ctk.CTkLabel(
            self.status_frame,
            text="● Checking...",
            anchor="w",
            font=("Inter", 11),
            text_color="#64748b",
        )
        self.net_status_label.grid(row=0, column=0, sticky="w", padx=(0, 12))

        self.status_label = ctk.CTkLabel(
            self.status_frame, 
            text="", 
            anchor="e",
            font=("Inter", 11),
            text_color="#64748b"
        )
        self.status_label.grid(row=0, column=1, sticky="e")

        self._net_status = "unknown"

        # Top-right avatar
        # Load user image from DB
        self.current_avatar_path = None
        try:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("SELECT profile_image_path FROM users WHERE username = ?", (self.username,))
            row = cur.fetchone()
            if row and row[0]:
                self.current_avatar_path = row[0]
            conn.close()
        except Exception:
            pass
            
        self._reload_avatar_image()

        self.avatar_button = ctk.CTkButton(
            self,
            image=self._avatar_icon,
            text="",
            width=32,
            height=32,
            fg_color="#020617",
            hover_color="#1e293b",
            corner_radius=16,
            command=self.open_profile,
        )
        self.avatar_button.place(relx=1.0, x=-15, y=10, anchor="ne")

        self.current_page = None
        self.show_appointment()
        self._update_status_bar()
        self._update_network_status()

    def _reload_avatar_image(self):
        # Default
        if getattr(sys, "frozen", False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(__file__)
        img_path = os.path.join(base_dir, "images", "user.png")
        
        # Override if custom
        if self.current_avatar_path and os.path.exists(self.current_avatar_path):
            img_path = self.current_avatar_path
            
        try:
            # Open and convert to RGBA
            raw_img = Image.open(img_path).convert("RGBA")
            
            # Resize
            size = (60, 60)
            raw_img = raw_img.resize(size, Image.Resampling.LANCZOS)
            
            # Create circular mask
            mask = Image.new("L", size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + size, fill=255)
            
            # Apply mask
            circular_img = Image.new("RGBA", size, (0, 0, 0, 0))
            circular_img.paste(raw_img, (0, 0), mask=mask)
            
            self._avatar_icon = ctk.CTkImage(light_image=circular_img, dark_image=circular_img, size=(30, 30))
        except Exception:
            self._avatar_icon = None

    def _update_avatar_ui(self, new_path):
        self.current_avatar_path = new_path
        self._reload_avatar_image()
        self.avatar_button.configure(image=self._avatar_icon)

    def _set_page(self, widget: ctk.CTkFrame):
        if self.current_page is not None:
            self.current_page.destroy()
        self.current_page = widget
        self.current_page.grid(row=0, column=0, sticky="nsew")

    def show_appointment(self):
        from pages.receptionist_appointment_page import ReceptionistAppointmentPage

        page = ReceptionistAppointmentPage(self.content)
        self._set_page(page)

    def show_schedule(self):
        from pages.receptionist_schedule_page import ReceptionistSchedulePage

        page = ReceptionistSchedulePage(self.content)
        self._set_page(page)

    def show_records(self):
        from pages.receptionist_records_page import ReceptionistRecordsPage

        page = ReceptionistRecordsPage(self.content)
        self._set_page(page)

    def open_profile(self):
        if self.account_menu is not None and self.account_menu.winfo_exists():
            self.account_menu.destroy()
            self.account_menu = None
            return

        self.account_menu = ctk.CTkToplevel(self)
        self.account_menu.overrideredirect(True)
        self.account_menu.attributes("-topmost", True)

        self.account_menu.update_idletasks()

        bx = self.avatar_button.winfo_rootx()
        by = self.avatar_button.winfo_rooty()
        bw = self.avatar_button.winfo_width()

        width, height = 200, 140
        desired_x = bx - width + bw 
        desired_y = by + self.avatar_button.winfo_height() + 4

        root_x = self.winfo_rootx()
        root_y = self.winfo_rooty()
        root_w = self.winfo_width()
        root_h = self.winfo_height()

        min_x = root_x
        max_x = root_x + max(root_w - width, 0)
        min_y = root_y
        max_y = root_y + max(root_h - height, 0)

        x = max(min_x, min(desired_x, max_x))
        y = max(min_y, min(desired_y, max_y))

        self.account_menu.geometry(f"{width}x{height}+{x}+{y}")

        self.account_menu.grid_columnconfigure(0, weight=1)

        # Container with border
        container = ctk.CTkFrame(
            self.account_menu, 
            fg_color="#1e293b", 
            border_width=2, 
            border_color="#475569", # Slate 600 border
            corner_radius=0
        )
        container.pack(fill="both", expand=True)
        container.grid_columnconfigure(0, weight=1)

        btn_settings = ctk.CTkButton(
            container,
            text="ACCOUNT SETTINGS",
            anchor="w",
            command=self._open_account_settings,
        )
        btn_settings.grid(row=0, column=0, padx=10, pady=(8, 4), sticky="ew")

        btn_security = ctk.CTkButton(
            container,
            text="SECURITY",
            anchor="w",
            command=self._open_security,
        )
        btn_security.grid(row=1, column=0, padx=10, pady=4, sticky="ew")

        btn_logout = ctk.CTkButton(
            container,
            text="LOGOUT",
            anchor="w",
            fg_color="#b91c1c",
            hover_color="#991b1b",
            command=self._logout_from_menu,
        )
        btn_logout.grid(row=2, column=0, padx=10, pady=(4, 8), sticky="ew")

    def _close_account_menu(self):
        if self.account_menu is not None and self.account_menu.winfo_exists():
            self.account_menu.destroy()
        self.account_menu = None

    def _open_account_settings(self):
        if self.account_menu:
            self.account_menu.destroy()
            self.account_menu = None

        if self.profile_window is None or not self.profile_window.winfo_exists():
            from profile_window import ProfileWindow
            self.profile_window = ProfileWindow(self, self.username, anchor_widget=self.avatar_button, mode="settings")
        else:
            self.profile_window.focus()

    def _open_security(self):
        if self.account_menu:
            self.account_menu.destroy()
            self.account_menu = None
            
        if self.profile_window is None or not self.profile_window.winfo_exists():
            from profile_window import ProfileWindow
            self.profile_window = ProfileWindow(self, self.username, anchor_widget=self.avatar_button, mode="security")
        else:
            self.profile_window.focus()        

    def _logout_from_menu(self):
        self._close_account_menu()
        self.logout()

    def logout(self):
        if not messagebox.askyesno("Confirm Logout", "Are you sure you want to logout?"):
            return
        self.should_relogin = True
        self.destroy()

    def _update_status_bar(self):
        """Update the bottom status bar with username and current time every second."""
        now_str = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        self.status_label.configure(text=f"Medisked v1.0   |   User: {self.username}   |   {now_str}")
        self.after(1000, self._update_status_bar)

    def _update_network_status(self):
        """Check internet connectivity and update the indicator color/text."""
        def classify(latency: float | None, error: Exception | None):
            if error is not None:
                return "no_internet", "No internet", "#2563eb"
            if latency is None:
                return "offline", "Offline", "#6b7280"
            if latency > 1.0:
                return "slow", f"Slow ({latency*1000:.0f} ms)", "#f97316"
            return "good", f"Online ({latency*1000:.0f} ms)", "#16a34a"

        start = time.monotonic()
        latency: float | None = None
        err: Exception | None = None
        try:
            req = urllib.request.Request("https://www.google.com", method="HEAD")
            with urllib.request.urlopen(req, timeout=1.5):
                pass
            latency = time.monotonic() - start
        except Exception as e:
            err = e

        status_key, label_text, color = classify(latency, err)
        self._net_status = status_key
        try:
            self.net_status_label.configure(text=f"● {label_text}", text_color=color)
        except Exception:
            pass

        self.after(10000, self._update_network_status)


def main():
    while True:
        
        init_db(DB_NAME)

        login_app = LoginApp()
        login_app.mainloop()

        if not login_app.authenticated:
            return

        username = login_app.logged_in_user
        role = login_app.logged_in_role

        if role == "admin":
            app = AdminDashboard(username=username)
        elif role == "doctor":
            app = DoctorDashboard(username=username)
        elif role == "cashier":
            from cashier_dashboard import CashierDashboard

            app = CashierDashboard(username=username)
        else:
            app = MainApp(username=username, role=role)

        app.mainloop()

        if not getattr(app, "should_relogin", False):
            break


if __name__ == "__main__":
    main()
