import customtkinter as ctk


class CashierSidebar(ctk.CTkFrame):
    def __init__(self, master, username: str, on_pos, on_logout):
        super().__init__(master, width=220, corner_radius=0)

        self._on_pos = on_pos
        self._on_logout = on_logout

        self.active_fg = "#0d74d1"
        self.inactive_fg = "transparent"

        self.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(
            self,
            text="CASHIER",
            font=("Segoe UI", 20, "bold"),
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.user_label = ctk.CTkLabel(
            self,
            text=username,
            font=("Segoe UI", 12),
        )
        self.user_label.grid(row=1, column=0, padx=20, pady=(0, 16), sticky="w")

        self.pos_button = ctk.CTkButton(
            self,
            text="POS",
            command=lambda: self._handle_nav_click("pos"),
            anchor="w",
        )
        self.pos_button.grid(row=2, column=0, padx=12, pady=(0, 10), sticky="ew")

        self.active_button = None
        self.set_active("pos")

        # Spacer pushes logout to bottom (row 4 grows)

        self.logout_button = ctk.CTkButton(
            self,
            text="Logout",
            command=self._on_logout,
            anchor="w",
        )
        self.logout_button.grid(row=5, column=0, padx=12, pady=(0, 20), sticky="ew")

    def _handle_nav_click(self, name: str):
        self.set_active(name)
        if name == "pos":
            self._on_pos()

    def set_active(self, name: str):
        buttons = {
            "pos": self.pos_button,
        }
        for key, btn in buttons.items():
            if btn is None:
                continue
            if key == name:
                btn.configure(fg_color=self.active_fg)
            else:
                btn.configure(fg_color=self.inactive_fg)
