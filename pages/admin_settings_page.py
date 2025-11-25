import customtkinter as ctk

from database import get_setting, set_setting, get_activity_logs


class AdminSettingsPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0)

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Settings",
            font=("Segoe UI", 24, "bold"),
        )
        title.grid(row=0, column=0, padx=30, pady=(30, 10), sticky="w")

        # Main content container
        content = ctk.CTkFrame(self, corner_radius=10)
        content.grid(row=1, column=0, padx=30, pady=(0, 30), sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        # Tab buttons row (like Manage Accounts window)
        tab_row = ctk.CTkFrame(content, fg_color="transparent")
        tab_row.grid(row=0, column=0, padx=20, pady=(16, 10), sticky="w")
        tab_row.grid_columnconfigure(0, weight=0)
        tab_row.grid_columnconfigure(1, weight=0)
        tab_row.grid_columnconfigure(2, weight=1)

        self.system_tab_btn = ctk.CTkButton(tab_row, text="System Settings", command=self._show_system_tab)
        self.system_tab_btn.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="w")

        self.logs_tab_btn = ctk.CTkButton(tab_row, text="Activity Logs", command=self._show_logs_tab)
        self.logs_tab_btn.grid(row=0, column=1, padx=(0, 0), pady=0, sticky="w")

        # System Settings content frame
        self.system_frame = ctk.CTkFrame(content, corner_radius=10)
        self.system_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.system_frame.grid_columnconfigure(0, weight=1)
        self.system_frame.grid_rowconfigure(2, weight=1)

        system_title = ctk.CTkLabel(
            self.system_frame,
            text="SYSTEM SETTINGS",
            font=("Segoe UI", 16, "bold"),
        )
        system_title.grid(row=0, column=0, padx=16, pady=(14, 6), sticky="w")

        system_hint = ctk.CTkLabel(
            self.system_frame,
            text="Configure global system preferences here.",
            font=("Segoe UI", 11),
            anchor="w",
        )
        system_hint.grid(row=1, column=0, padx=16, pady=(0, 10), sticky="w")

        # System options body
        system_body = ctk.CTkFrame(self.system_frame, corner_radius=8, fg_color="transparent")
        system_body.grid(row=2, column=0, padx=16, pady=(0, 14), sticky="nsew")
        system_body.grid_columnconfigure(0, weight=1)

        self.logging_switch = ctk.CTkCheckBox(
            system_body,
            text="Enable activity logging",
        )
        self.logging_switch.grid(row=0, column=0, padx=4, pady=(4, 2), sticky="w")

        self.login_popup_switch = ctk.CTkCheckBox(
            system_body,
            text="Show login success popup",
        )
        self.login_popup_switch.grid(row=1, column=0, padx=4, pady=(2, 4), sticky="w")

        save_btn = ctk.CTkButton(self.system_frame, text="Save changes", command=self._save_settings)
        save_btn.grid(row=3, column=0, padx=16, pady=(0, 16), sticky="e")

        # Activity Logs content frame (initially hidden)
        self.logs_frame = ctk.CTkFrame(content, corner_radius=10)
        self.logs_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.logs_frame.grid_columnconfigure(0, weight=1)
        self.logs_frame.grid_rowconfigure(1, weight=1)
        self.logs_frame.grid_remove()

        logs_title = ctk.CTkLabel(
            self.logs_frame,
            text="ACTIVITY LOGS",
            font=("Segoe UI", 16, "bold"),
        )
        logs_title.grid(row=0, column=0, padx=16, pady=(14, 6), sticky="w")

        self.logs_text = ctk.CTkTextbox(self.logs_frame, height=220)
        self.logs_text.grid(row=1, column=0, padx=16, pady=(0, 14), sticky="nsew")
        self.logs_text.insert("1.0", "No activity logs to display.")
        self.logs_text.configure(state="disabled")

        # Start on System Settings tab
        self._set_active_tab("system")
        self._load_settings()

    def _set_active_tab(self, name: str):
        # Simple visual feedback: active tab has blue fg_color, other is transparent
        if name == "system":
            self.system_tab_btn.configure(fg_color="#0d74d1")
            self.logs_tab_btn.configure(fg_color="transparent")
        else:
            self.system_tab_btn.configure(fg_color="transparent")
            self.logs_tab_btn.configure(fg_color="#0d74d1")

    def _show_system_tab(self):
        self._set_active_tab("system")
        self.logs_frame.grid_remove()
        self.system_frame.grid()

    def _show_logs_tab(self):
        self._set_active_tab("logs")
        self.system_frame.grid_remove()
        self._reload_logs()
        self.logs_frame.grid()

    def _load_settings(self):
        """Load current system settings into the UI."""
        logging_enabled = get_setting("activity_logging_enabled", "1") == "1"
        show_popup = get_setting("show_login_success_popup", "1") == "1"

        # Set checkboxes without triggering extra logic
        self.logging_switch.select() if logging_enabled else self.logging_switch.deselect()
        self.login_popup_switch.select() if show_popup else self.login_popup_switch.deselect()

    def _save_settings(self):
        """Persist system settings from the UI to the database."""
        set_setting("activity_logging_enabled", "1" if self.logging_switch.get() else "0")
        set_setting("show_login_success_popup", "1" if self.login_popup_switch.get() else "0")

    def _reload_logs(self):
        """Reload activity logs into the text box."""
        rows = get_activity_logs(limit=200)
        self.logs_text.configure(state="normal")
        self.logs_text.delete("1.0", "end")

        if not rows:
            self.logs_text.insert("1.0", "No activity logs to display.")
        else:
            lines = []
            for ts, username, role, action, details in rows:
                user_part = username or "(system)"
                role_part = f"[{role}]" if role else ""
                detail_part = f" - {details}" if details else ""
                lines.append(f"{ts}  {user_part} {role_part}  {action}{detail_part}")
            self.logs_text.insert("1.0", "\n".join(lines))

        self.logs_text.configure(state="disabled")
