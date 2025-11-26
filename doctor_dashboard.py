import os
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox, PhotoImage
from PIL import Image

from sidebar_doctor import DoctorSidebar
from doctor_profile_window import DoctorProfileWindow
from database import DB_NAME
import sqlite3


class DoctorDashboard(ctk.CTk):
    def __init__(self, username: str):
        super().__init__()

        self.title("MEDISKED: HOSPITAL SCHEDULING AND BILLING MANAGMENT SYSTEM - Doctor")
        self.geometry("1100x650")
        self.resizable(True, True)

        # Window icon
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

        # Center window on screen
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
        self.should_relogin = False
        self.profile_window = None

        # Resolve doctor id from doctors table
        self.doctor_id, self.doctor_name = self._resolve_doctor()

        # Layout: sidebar + content + bottom status bar
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self.sidebar = DoctorSidebar(
            self,
            username=self.doctor_name or self.username,
            on_dashboard=self.show_dashboard,
            on_appointments=self.show_appointments,
            on_records=self.show_records,
            on_manage=self.show_manage,
            on_profile=self.open_profile,
            on_logout=self.logout,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color=base_bg)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # Bottom status bar
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=0)
        self.status_frame.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(self.status_frame, text="", anchor="e")
        self.status_label.grid(row=0, column=0, sticky="e")

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
        self.show_dashboard()
        self._update_status_bar()

    def _connect(self):
        return sqlite3.connect(DB_NAME)

    def _resolve_doctor(self):
        """Map the logged-in username to a doctor record by name.

        If no active record exists yet, create one automatically so that
        the doctor can manage their own availability.
        """
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM doctors WHERE name = ? AND status = 'active'", (self.username,))
        row = cur.fetchone()
        if row is None:
            # Create a simple active doctor record using the username as the name.
            cur.execute(
                "INSERT INTO doctors (name, specialty, status, notes) VALUES (?, NULL, 'active', NULL)",
                (self.username,),
            )
            conn.commit()
            cur.execute("SELECT id, name FROM doctors WHERE name = ? AND status = 'active'", (self.username,))
            row = cur.fetchone()
        conn.close()
        if row is None:
            return None, self.username
        return row[0], row[1]

    def _set_page(self, widget: ctk.CTkFrame):
        if self.current_page is not None:
            self.current_page.destroy()
        self.current_page = widget
        self.current_page.grid(row=0, column=0, sticky="nsew")

    def show_dashboard(self):
        from pages.doctor_dashboard_page import DoctorDashboardPage

        page = DoctorDashboardPage(
            self.content,
            doctor_id=self.doctor_id,
            doctor_name=self.doctor_name or self.username,
        )
        self._set_page(page)

    def show_appointments(self):
        from pages.doctor_appointments_page import DoctorAppointmentsPage

        page = DoctorAppointmentsPage(self.content, doctor_name=self.doctor_name or self.username)
        self._set_page(page)

    def show_records(self):
        from pages.doctor_records_page import DoctorRecordsPage

        page = DoctorRecordsPage(self.content, doctor_name=self.doctor_name or self.username)
        self._set_page(page)

    def show_manage(self):
        from pages.doctor_manage_page import DoctorManagePage

        page = DoctorManagePage(self.content, doctor_id=self.doctor_id, doctor_name=self.doctor_name or self.username)
        self._set_page(page)

    def open_profile(self):
        if self.profile_window is None or not self.profile_window.winfo_exists():
            self.profile_window = DoctorProfileWindow(
                self,
                username=self.username,
                doctor_id=self.doctor_id,
                anchor_widget=self.avatar_button,
            )
        else:
            self.profile_window.focus()

    def logout(self):
        if not messagebox.askyesno("Confirm Logout", "Are you sure you want to logout?"):
            return
        self.should_relogin = True
        self.destroy()

    def _update_status_bar(self):
        """Update the bottom status bar with doctor name and current time every second."""

        display_name = self.doctor_name or self.username
        now_str = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        self.status_label.configure(text=f"Medisked v1.0   |   User: {display_name}   |   {now_str}")
        self.after(1000, self._update_status_bar)
