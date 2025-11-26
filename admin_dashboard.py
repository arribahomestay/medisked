import os
import sys
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox, PhotoImage
from PIL import Image

from sidebar_admin import AdminSidebar
from manage_accounts_window import ManageAccountsWindow
from profile_window import ProfileWindow


class AdminDashboard(ctk.CTk):
    def __init__(self, username: str):
        super().__init__()

        self.title("MEDISKED: HOSPITAL SCHEDULING AND BILLING MANAGMENT SYSTEM - Admin")
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
        self.should_relogin = False
        self.manage_window = None
        self.profile_window = None
        self.account_menu = None

        # Layout: content row + bottom status bar row
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

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

        width, height = 200, 130
        desired_x = bx - width + bw  # align menu under/right of avatar
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
            self.profile_window = ProfileWindow(self, username=self.username, anchor_widget=self.avatar_button)
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

    def _update_status_bar(self):
        """Update the bottom status bar with username and current time every second."""

        now_str = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        self.status_label.configure(text=f"Medisked v1.0   |   User: {self.username}   |   {now_str}")
        self.after(1000, self._update_status_bar)
