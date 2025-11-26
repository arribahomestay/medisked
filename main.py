import os
import sys
from datetime import datetime
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
            on_logout=self.logout,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        self.content = ctk.CTkFrame(self, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # Bottom status bar
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=0)
        self.status_frame.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(self.status_frame, text="", anchor="e")
        self.status_label.grid(row=0, column=0, sticky="e")

        # Top-right avatar: account emoji icon with transparent background
        self.avatar_label = ctk.CTkLabel(
            self,
            text="👤",
            fg_color="transparent",
            text_color="#e5e7eb",
            font=("Segoe UI", 16),
        )
        self.avatar_label.place(relx=1.0, x=-20, y=10, anchor="ne")
        self.avatar_label.bind("<Button-1>", lambda _event: self.open_profile())

        self.current_page = None
        self.show_appointment()
        self._update_status_bar()

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
            self.profile_window = ProfileWindow(self, username=self.username)
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
