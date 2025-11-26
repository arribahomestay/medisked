import os
import sys
from datetime import datetime
import time
import urllib.request
import customtkinter as ctk
from tkinter import messagebox, PhotoImage
from PIL import Image

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
        base_bg = "#1f2933"
        self.configure(fg_color=base_bg)

        self.username = username
        self.role = role
        self.should_relogin = False
        self.profile_window = None

        
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
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=base_bg)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # Bottom status bar
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=0)
        self.status_frame.grid_columnconfigure(0, weight=0)
        self.status_frame.grid_columnconfigure(1, weight=1)

        self.net_status_label = ctk.CTkLabel(
            self.status_frame,
            text="● Checking...",
            anchor="w",
            text_color="#9ca3af",
        )
        self.net_status_label.grid(row=0, column=0, sticky="w", padx=(0, 12))

        self.status_label = ctk.CTkLabel(self.status_frame, text="", anchor="e")
        self.status_label.grid(row=0, column=1, sticky="e")

        self._net_status = "unknown"

        # Top-right avatar: image button using user.png with transparent background
        user_png_path = os.path.join(base_dir, "images", "user.png")
        try:
            avatar_image = Image.open(user_png_path)
            self._avatar_icon = ctk.CTkImage(light_image=avatar_image, dark_image=avatar_image, size=(20, 20))
        except Exception:
            self._avatar_icon = None

        self.avatar_button = ctk.CTkButton(
            self,
            image=self._avatar_icon,
            text="",
            width=28,
            height=28,
            fg_color="transparent",
            hover=False,
            border_width=0,
            command=self.open_profile,
        )
        self.avatar_button.place(relx=1.0, x=-20, y=10, anchor="ne")

        self.current_page = None
        self.show_appointment()
        self._update_status_bar()
        self._update_network_status()

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
        if self.profile_window is None or not self.profile_window.winfo_exists():
            self.profile_window = ProfileWindow(self, username=self.username, anchor_widget=self.avatar_button)
        else:
            self.profile_window.focus()

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
        except Exception as e:  # noqa: BLE001
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
