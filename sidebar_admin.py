import customtkinter as ctk


class AdminSidebar(ctk.CTkFrame):
    def __init__(self, master, username: str,
                 on_dashboard, on_records, on_settings,
                 on_profile, on_logout):
        super().__init__(master, width=220, corner_radius=0)

        self._on_dashboard = on_dashboard
        self._on_records = on_records
        self._on_settings = on_settings

        self.active_fg = "#0d74d1"
        self.inactive_fg = "transparent"

        self.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(
            self,
            text="ADMIN PANEL",
            font=("Segoe UI", 20, "bold"),
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Username row
        self.user_label = ctk.CTkLabel(
            self,
            text=username,
            font=("Segoe UI", 12),
        )
        self.user_label.grid(row=1, column=0, padx=20, pady=(0, 16), sticky="w")

        self.dashboard_button = ctk.CTkButton(
            self,
            text="DASHBOARD",
            command=lambda: self._handle_nav_click("dashboard"),
            anchor="w",
        )
        self.dashboard_button.grid(row=2, column=0, padx=12, pady=(0, 10), sticky="ew")

        self.records_button = ctk.CTkButton(
            self,
            text="RECORDS",
            command=lambda: self._handle_nav_click("records"),
            anchor="w",
        )
        self.records_button.grid(row=3, column=0, padx=12, pady=(0, 10), sticky="ew")

        self.settings_button = ctk.CTkButton(
            self,
            text="SETTINGS",
            command=lambda: self._handle_nav_click("settings"),
            anchor="w",
        )
        self.settings_button.grid(row=4, column=0, padx=12, pady=(0, 10), sticky="ew")

        self.active_button = None
        self.set_active("dashboard")

        # Spacer row 5 grows to push avatar+logout to bottom

        self.avatar_button = ctk.CTkButton(
            self,
            text="👤",
            width=26,
            height=26,
            corner_radius=13,
            fg_color="transparent",
            border_width=0,
            command=on_profile,
        )
        self.avatar_button.grid(row=6, column=0, padx=16, pady=(0, 6), sticky="w")

        self.logout_button = ctk.CTkButton(
            self,
            text="Logout",
            command=on_logout,
            anchor="w",
        )
        self.logout_button.grid(row=7, column=0, padx=12, pady=(0, 20), sticky="ew")

    def _handle_nav_click(self, name: str):
        self.set_active(name)
        if name == "dashboard":
            self._on_dashboard()
        elif name == "records":
            self._on_records()
        elif name == "settings":
            self._on_settings()

    def set_active(self, name: str):
        buttons = {
            "dashboard": self.dashboard_button,
            "records": self.records_button,
            "settings": self.settings_button,
        }

        for key, btn in buttons.items():
            if btn is None:
                continue
            if key == name:
                btn.configure(fg_color=self.active_fg)
            else:
                btn.configure(fg_color=self.inactive_fg)
