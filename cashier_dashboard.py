import os
import sys
from datetime import datetime
import sqlite3

import customtkinter as ctk
from tkinter import messagebox, PhotoImage

from database import DB_NAME
from sidebar_cashier import CashierSidebar
from pages.cashier_pos_page import CashierPOSPage


class CashierDashboard(ctk.CTk):
    def __init__(self, username: str):
        super().__init__()

        self.title("MEDISKED: HOSPITAL SCHEDULING AND BILLING MANAGMENT SYSTEM - Cashier")
        self.geometry("1100x650")
        self.resizable(False, False)

        # Window icon (works both in source run and PyInstaller EXE)
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

        # Center window on screen
        self.update_idletasks()
        width = 1100
        height = 650
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.username = username
        self.should_relogin = False

        # Layout: sidebar + content + bottom status bar
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self.sidebar = CashierSidebar(
            self,
            username=self.username,
            on_pos=self.show_pos,
            on_records=self.show_records,
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

        self.current_page = None
        self.show_pos()
        self._update_status_bar()

    def _set_page(self, widget: ctk.CTkFrame):
        if self.current_page is not None:
            self.current_page.destroy()
        self.current_page = widget
        self.current_page.grid(row=0, column=0, sticky="nsew")

    def show_pos(self):
        page = CashierPOSPage(self.content)
        self._set_page(page)

    def show_records(self):
        from pages.cashier_records_page import CashierRecordsPage

        page = CashierRecordsPage(self.content)
        self._set_page(page)

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
