import customtkinter as ctk


class ReceptionistSidebar(ctk.CTkFrame):
    def __init__(self, master, username: str,
                 on_appointment, on_schedule, on_records,
                 on_profile, on_logout=None):
        super().__init__(master, width=220, corner_radius=0)

        self._on_appointment = on_appointment
        self._on_schedule = on_schedule
        self._on_records = on_records

        self.active_fg = "#0d74d1"
        self.inactive_fg = "#020617"
        self.hover_fg = "#1d4ed8"

        self.configure(fg_color="#020617")

        # Spacer row will be row 5 (after three main nav buttons)
        self.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(
            self,
            text="RECEPTIONIST",
            font=("Segoe UI", 20, "bold"),
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.appointment_button = ctk.CTkButton(
            self,
            text="APPOINTMENT",
            command=lambda: self._handle_nav_click("appointment"),
            anchor="w",
            fg_color=self.inactive_fg,
            hover_color=self.hover_fg,
            corner_radius=10,
        )
        self.appointment_button.grid(row=2, column=0, padx=12, pady=(0, 10), sticky="ew")

        self.schedule_button = ctk.CTkButton(
            self,
            text="SCHEDULE",
            command=lambda: self._handle_nav_click("schedule"),
            anchor="w",
            fg_color=self.inactive_fg,
            hover_color=self.hover_fg,
            corner_radius=10,
        )
        self.schedule_button.grid(row=3, column=0, padx=12, pady=(0, 10), sticky="ew")

        self.records_button = ctk.CTkButton(
            self,
            text="RECORDS",
            command=lambda: self._handle_nav_click("records"),
            anchor="w",
            fg_color=self.inactive_fg,
            hover_color=self.hover_fg,
            corner_radius=10,
        )
        self.records_button.grid(row=4, column=0, padx=12, pady=(0, 10), sticky="ew")

        self.active_button = None
        self.set_active("appointment")

        # Spacer row grows to keep nav grouped at top

    def _handle_nav_click(self, name: str):
        self.set_active(name)
        if name == "appointment":
            self._on_appointment()
        elif name == "schedule":
            self._on_schedule()
        elif name == "records":
            self._on_records()

    def set_active(self, name: str):
        buttons = {
            "appointment": self.appointment_button,
            "schedule": self.schedule_button,
            "records": self.records_button,
        }

        for key, btn in buttons.items():
            if btn is None:
                continue
            if key == name:
                btn.configure(fg_color=self.active_fg)
            else:
                btn.configure(fg_color=self.inactive_fg)
