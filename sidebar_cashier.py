import customtkinter as ctk


class CashierSidebar(ctk.CTkFrame):
    def __init__(self, master, username: str, on_pos, on_records, on_logout):
        super().__init__(master, width=220, corner_radius=0)

        self._on_pos = on_pos
        self._on_records = on_records
        self._on_logout = on_logout

        self.active_fg = "#0d74d1"
        self.inactive_fg = "#020617"
        self.hover_fg = "#1d4ed8"

        self.configure(fg_color="#020617")

        self.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(
            self,
            text="CASHIER",
            font=("Segoe UI", 20, "bold"),
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.pos_button = ctk.CTkButton(
            self,
            text="POS",
            command=lambda: self._handle_nav_click("pos"),
            anchor="w",
            fg_color=self.inactive_fg,
            hover_color=self.hover_fg,
            corner_radius=10,
        )
        self.pos_button.grid(row=2, column=0, padx=12, pady=(0, 10), sticky="ew")

        self.records_button = ctk.CTkButton(
            self,
            text="Records",
            command=lambda: self._handle_nav_click("records"),
            anchor="w",
            fg_color=self.inactive_fg,
            hover_color=self.hover_fg,
            corner_radius=10,
        )
        self.records_button.grid(row=3, column=0, padx=12, pady=(0, 10), sticky="ew")

        self.active_button = None
        self.set_active("pos")

        # Spacer pushes content away from bottom (row 4 grows)

    def _handle_nav_click(self, name: str):
        self.set_active(name)
        if name == "pos":
            self._on_pos()
        elif name == "records":
            self._on_records()

    def set_active(self, name: str):
        buttons = {
            "pos": self.pos_button,
            "records": self.records_button,
        }
        for key, btn in buttons.items():
            if btn is None:
                continue
            if key == name:
                btn.configure(fg_color=self.active_fg)
            else:
                btn.configure(fg_color=self.inactive_fg)
