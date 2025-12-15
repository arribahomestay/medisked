import customtkinter as ctk

class AdminSidebar(ctk.CTkFrame):
    def __init__(self, master, username: str,
                 on_dashboard, on_records, on_manage_accounts, on_settings,
                 on_profile, on_logout):
        super().__init__(master, width=280, corner_radius=0)

        self._on_dashboard = on_dashboard
        self._on_records = on_records
        self._on_manage_accounts = on_manage_accounts
        self._on_settings = on_settings

        # Modern "Expensive" Theme Colors
        # Modern "Expensive" Theme Colors
        self.sidebar_bg = "#0f172a"  # Deep Slate 900 (High contrast sidebar)
        self.accent_color = "#4f46e5" # Indigo 600 (Deep modern primary)
        self.active_bg = "#1e293b"   # Slate 800
        self.inactive_bg = "transparent"
        self.hover_bg = "#334155"    # Slate 700
        self.text_color = "#f8fafc"  # Slate 50
        self.subtext_color = "#94a3b8" # Slate 400

        self.configure(fg_color=self.sidebar_bg)

        self.grid_rowconfigure(6, weight=1)

        # 1. Header with improved typography
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, padx=24, pady=(32, 24), sticky="ew")
        
        self.logo_label = ctk.CTkLabel(
            self.header_frame,
            text="MEDISKED",
            font=("Inter", 26, "bold"), # Tried to use Inter if available, falls back gracefully
            text_color="white"
        )
        self.logo_label.pack(anchor="w")

        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Admin Portal",
            font=("Inter", 13),
            text_color=self.accent_color
        )
        self.subtitle_label.pack(anchor="w", pady=(2, 0))

        # 2. Navigation Buttons with modern spacing and borders
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
                corner_radius=12, # Soft modern corners
                height=50,
                border_spacing=10
            )
            btn.grid(row=row, column=0, padx=16, pady=6, sticky="ew")
            return btn

        self.dashboard_button = create_nav_btn(2, "DASHBOARD", lambda: self._handle_nav_click("dashboard"), "📊")
        self.records_button = create_nav_btn(3, "RECORDS", lambda: self._handle_nav_click("records"), "📂")
        self.manage_accounts_button = create_nav_btn(4, "ACCOUNTS", lambda: self._handle_nav_click("manage_accounts"), "👥")
        self.settings_button = create_nav_btn(5, "SETTINGS", lambda: self._handle_nav_click("settings"), "⚙️")

        self.active_button = None
        self.set_active("dashboard")

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
                # Active State: Accent color background, white text
                btn.configure(fg_color=self.accent_color, text_color="white")
            else:
                # Inactive State: Transparent background, muted text
                btn.configure(fg_color=self.inactive_bg, text_color=self.subtext_color)
