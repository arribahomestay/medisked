import customtkinter as ctk


class CashierSidebar(ctk.CTkFrame):
    def __init__(self, master, username: str, on_pos, on_records, on_logout):
        super().__init__(master, width=240, corner_radius=0)

        self._on_pos = on_pos
        self._on_records = on_records
        self._on_logout = on_logout

        # Theme Colors (Matching Admin)
        self.sidebar_bg = "#0f172a"
        self.accent_color = "#4f46e5" # Indigo 600
        self.active_bg = "#1e293b"
        self.inactive_bg = "transparent"
        self.hover_bg = "#334155"
        self.text_color = "#f8fafc"
        self.subtext_color = "#94a3b8"

        self.configure(fg_color=self.sidebar_bg)

        # Spacer row 4 grows to push content up
        self.grid_rowconfigure(4, weight=1)

        # 1. Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=24, pady=(32, 24), sticky="ew")
        
        self.logo_label = ctk.CTkLabel(
            self.header_frame,
            text="MEDISKED",
            font=("Inter", 26, "bold"),
            text_color="white"
        )
        self.logo_label.pack(anchor="w")

        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Cashier Workspace",
            font=("Inter", 13),
            text_color=self.accent_color
        )
        self.subtitle_label.pack(anchor="w", pady=(2, 0))

        # 2. Navigation Helper
        def create_nav_btn(row, text, command, icon):
            btn = ctk.CTkButton(
                self,
                text=f"  {icon}    {text}",
                command=command,
                font=("Inter", 14, "bold"),
                anchor="w",
                fg_color=self.inactive_bg,
                text_color=self.subtext_color,
                hover_color=self.hover_bg,
                corner_radius=12,
                height=50,
                border_spacing=10
            )
            btn.grid(row=row, column=0, padx=16, pady=6, sticky="ew")
            return btn

        self.pos_button = create_nav_btn(2, "POS", lambda: self._handle_nav_click("pos"), "💳")
        self.records_button = create_nav_btn(3, "RECORDS", lambda: self._handle_nav_click("records"), "📂")

        self.active_button = None
        self.set_active("pos")

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
                btn.configure(fg_color=self.accent_color, text_color="white")
            else:
                btn.configure(fg_color=self.inactive_bg, text_color=self.subtext_color)
