import customtkinter as ctk


class DoctorSidebar(ctk.CTkFrame):
    def __init__(self, master, username: str, on_dashboard, on_appointments, on_records, on_manage, on_profile, on_logout):
        super().__init__(master, width=220, corner_radius=0)

        self._on_dashboard = on_dashboard
        self._on_appointments = on_appointments
        self._on_records = on_records
        self._on_manage = on_manage
        self._on_profile = on_profile

        self.active_fg = "#0d74d1"
        self.inactive_fg = "transparent"

        # Spacer row 7 grows to push avatar+logout to the bottom
        self.grid_rowconfigure(7, weight=1)

        self.logo_label = ctk.CTkLabel(
            self,
            text="DOCTOR",
            font=("Segoe UI", 20, "bold"),
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.user_label = ctk.CTkLabel(
            self,
            text=username,
            font=("Segoe UI", 12),
        )
        self.user_label.grid(row=1, column=0, padx=20, pady=(0, 16), sticky="w")

        # Dashboard button
        self.dashboard_button = ctk.CTkButton(
            self,
            text="DASHBOARD",
            command=lambda: self._handle_nav_click("dashboard"),
            anchor="w",
        )
        self.dashboard_button.grid(row=2, column=0, padx=12, pady=(0, 10), sticky="ew")

        self.appointments_button = ctk.CTkButton(
            self,
            text="APPOINTMENTS",
            command=lambda: self._handle_nav_click("appointments"),
            anchor="w",
        )
        self.appointments_button.grid(row=3, column=0, padx=12, pady=(0, 10), sticky="ew")

        self.records_button = ctk.CTkButton(
            self,
            text="RECORDS",
            command=lambda: self._handle_nav_click("records"),
            anchor="w",
        )
        self.records_button.grid(row=4, column=0, padx=12, pady=(0, 10), sticky="ew")

        self.manage_button = ctk.CTkButton(
            self,
            text="MANAGE",
            command=lambda: self._handle_nav_click("manage"),
            anchor="w",
        )
        self.manage_button.grid(row=5, column=0, padx=12, pady=(0, 10), sticky="ew")

        self.active_button = None
        self.set_active("dashboard")

        self.avatar_button = ctk.CTkButton(
            self,
            text="👤",
            width=26,
            height=26,
            corner_radius=13,
            fg_color="transparent",
            border_width=0,
            command=self._on_profile,
        )
        self.avatar_button.grid(row=8, column=0, padx=16, pady=(0, 2), sticky="w")

        self.logout_button = ctk.CTkButton(
            self,
            text="Logout",
            command=on_logout,
            anchor="w",
        )
        self.logout_button.grid(row=9, column=0, padx=12, pady=(0, 20), sticky="ew")

    def _handle_nav_click(self, name: str):
        self.set_active(name)
        if name == "dashboard":
            self._on_dashboard()
        elif name == "appointments":
            self._on_appointments()
        elif name == "records":
            self._on_records()
        elif name == "manage":
            self._on_manage()

    def set_active(self, name: str):
        buttons = {
            "dashboard": self.dashboard_button,
            "appointments": self.appointments_button,
            "records": self.records_button,
            "manage": self.manage_button,
        }
        for key, btn in buttons.items():
            if btn is None:
                continue
            if key == name:
                btn.configure(fg_color=self.active_fg)
            else:
                btn.configure(fg_color=self.inactive_fg)
