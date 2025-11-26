import customtkinter as ctk


class AdminSidebar(ctk.CTkFrame):
    def __init__(self, master, username: str,
                 on_dashboard, on_records, on_manage_accounts, on_settings,
                 on_profile, on_logout):
        super().__init__(master, width=220, corner_radius=0)

        self._on_dashboard = on_dashboard
        self._on_records = on_records
        self._on_manage_accounts = on_manage_accounts
        self._on_settings = on_settings

        self.active_fg = "#0d74d1"
        self.inactive_fg = "#020617"
        self.hover_fg = "#1d4ed8"

        self.configure(fg_color="#020617")

        self.grid_rowconfigure(6, weight=1)

        self.logo_label = ctk.CTkLabel(
            self,
            text="ADMIN PANEL",
            font=("Segoe UI", 20, "bold"),
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.dashboard_button = ctk.CTkButton(
            self,
            text="DASHBOARD",
            command=lambda: self._handle_nav_click("dashboard"),
            anchor="w",
            fg_color=self.inactive_fg,
            hover_color=self.hover_fg,
            corner_radius=10,
        )
        self.dashboard_button.grid(row=2, column=0, padx=12, pady=(0, 10), sticky="ew")

        self.records_button = ctk.CTkButton(
            self,
            text="RECORDS",
            command=lambda: self._handle_nav_click("records"),
            anchor="w",
            fg_color=self.inactive_fg,
            hover_color=self.hover_fg,
            corner_radius=10,
        )
        self.records_button.grid(row=3, column=0, padx=12, pady=(0, 10), sticky="ew")

        self.manage_accounts_button = ctk.CTkButton(
            self,
            text="MANAGE ACCOUNTS",
            command=lambda: self._handle_nav_click("manage_accounts"),
            anchor="w",
            fg_color=self.inactive_fg,
            hover_color=self.hover_fg,
            corner_radius=10,
        )
        self.manage_accounts_button.grid(row=4, column=0, padx=12, pady=(0, 10), sticky="ew")

        self.settings_button = ctk.CTkButton(
            self,
            text="SETTINGS",
            command=lambda: self._handle_nav_click("settings"),
            anchor="w",
            fg_color=self.inactive_fg,
            hover_color=self.hover_fg,
            corner_radius=10,
        )
        self.settings_button.grid(row=5, column=0, padx=12, pady=(0, 10), sticky="ew")

        self.active_button = None
        self.set_active("dashboard")

        # Spacer row 6 grows to keep nav grouped at top

    def _handle_nav_click(self, name: str):
        self.set_active(name)
        if name == "dashboard":
            self._on_dashboard()
        elif name == "records":
            self._on_records()
        elif name == "manage_accounts":
            self._on_manage_accounts()
        elif name == "settings":
            self._on_settings()

    def set_active(self, name: str):
        buttons = {
            "dashboard": self.dashboard_button,
            "records": self.records_button,
            "manage_accounts": self.manage_accounts_button,
            "settings": self.settings_button,
        }

        for key, btn in buttons.items():
            if btn is None:
                continue
            if key == name:
                btn.configure(fg_color=self.active_fg)
            else:
                btn.configure(fg_color=self.inactive_fg)
