import os
import sys
import customtkinter as ctk
from tkinter import messagebox, PhotoImage

from sidebar_admin import AdminSidebar
from manage_accounts_window import ManageAccountsWindow
from profile_window import ProfileWindow


class AdminDashboard(ctk.CTk):
    def __init__(self, username: str):
        super().__init__()

        self.title("MEDISKED: HOSPITAL SCHEDULING AND BILLING MANAGMENT SYSTEM - Admin")
        self.geometry("1100x650")
        self.resizable(True, True)

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
        self.manage_window = None
        self.profile_window = None
        self.account_menu = None

        # Layout: 1 row, 2 columns (sidebar + content)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = AdminSidebar(
            self,
            username=self.username,
            on_dashboard=self.show_dashboard,
            on_records=self.show_records,
            on_settings=self.show_settings,
            on_profile=self.open_profile,
            on_logout=self.logout,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        # Content area
        self.content = ctk.CTkFrame(self, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # Lazy-import pages when needed
        self.current_page = None
        self.show_dashboard()

    def _set_page(self, widget: ctk.CTkFrame):
        if self.current_page is not None:
            self.current_page.destroy()
        self.current_page = widget
        self.current_page.grid(row=0, column=0, sticky="nsew")

    def show_dashboard(self):
        from pages.admin_dashboard_page import AdminDashboardPage

        page = AdminDashboardPage(self.content)
        self._set_page(page)

    def show_records(self):
        from pages.admin_records_page import AdminRecordsPage

        page = AdminRecordsPage(self.content)
        self._set_page(page)

    def show_settings(self):
        from pages.admin_settings_page import AdminSettingsPage

        page = AdminSettingsPage(self.content)
        self._set_page(page)

    def open_profile(self):
        # Toggle small popup menu near avatar button
        if self.account_menu is not None and self.account_menu.winfo_exists():
            self.account_menu.destroy()
            self.account_menu = None
            return

        self.account_menu = ctk.CTkToplevel(self)
        self.account_menu.overrideredirect(True)
        self.account_menu.attributes("-topmost", True)

        # Position next to the avatar button but keep inside main window
        self.account_menu.update_idletasks()

        bx = self.sidebar.avatar_button.winfo_rootx()
        by = self.sidebar.avatar_button.winfo_rooty()
        bw = self.sidebar.avatar_button.winfo_width()

        width, height = 200, 130
        desired_x = bx + bw + 8
        desired_y = by

        # Bounds of the main admin window on the screen
        root_x = self.winfo_rootx()
        root_y = self.winfo_rooty()
        root_w = self.winfo_width()
        root_h = self.winfo_height()

        # Clamp so the menu stays fully inside the window
        min_x = root_x
        max_x = root_x + max(root_w - width, 0)
        min_y = root_y
        max_y = root_y + max(root_h - height, 0)

        x = max(min_x, min(desired_x, max_x))
        y = max(min_y, min(desired_y, max_y))

        self.account_menu.geometry(f"{width}x{height}+{x}+{y}")

        self.account_menu.grid_columnconfigure(0, weight=1)

        btn1 = ctk.CTkButton(
            self.account_menu,
            text="ACCOUNT SETTINGS",
            anchor="w",
            command=self._open_account_settings,
        )
        btn1.grid(row=0, column=0, padx=10, pady=(8, 4), sticky="ew")

        btn2 = ctk.CTkButton(
            self.account_menu,
            text="MANAGE ACCOUNTS",
            anchor="w",
            command=self._open_manage_accounts,
        )
        btn2.grid(row=1, column=0, padx=10, pady=4, sticky="ew")

        btn3 = ctk.CTkButton(
            self.account_menu,
            text="SECURITY",
            anchor="w",
            command=self._open_security,
        )
        btn3.grid(row=2, column=0, padx=10, pady=(4, 8), sticky="ew")

    def _close_account_menu(self):
        if self.account_menu is not None and self.account_menu.winfo_exists():
            self.account_menu.destroy()
        self.account_menu = None

    def _open_account_settings(self):
        self._close_account_menu()
        if self.profile_window is None or not self.profile_window.winfo_exists():
            self.profile_window = ProfileWindow(self, username=self.username)
        else:
            self.profile_window.focus()

    def _open_manage_accounts(self):
        self._close_account_menu()
        if self.manage_window is None or not self.manage_window.winfo_exists():
            self.manage_window = ManageAccountsWindow(self, username=self.username)
        else:
            self.manage_window.focus()

    def _open_security(self):
        self._close_account_menu()
        messagebox.showinfo("Security", "WALA PANI")

    def logout(self):
        if not messagebox.askyesno("Confirm Logout", "Are you sure you want to logout?"):
            return
        self.should_relogin = True
        self.destroy()
