import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox

from database import get_setting, set_setting, get_activity_logs, log_activity


class AdminSettingsPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Header & Controls Card
        header_card = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=16) # Slate 800
        header_card.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        header_card.grid_columnconfigure(0, weight=1)

        # Title
        title_frame = ctk.CTkFrame(header_card, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=24, pady=24, sticky="ew")
        
        ctk.CTkLabel(
            title_frame, 
            text="System Settings", 
            font=("Inter", 20, "bold"), 
            text_color="white"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame, 
            text="Configure global system preferences and view logs.", 
            font=("Inter", 13), 
            text_color="#94a3b8"
        ).pack(anchor="w", pady=(2, 0))

        # Controls (Tabs)
        controls_frame = ctk.CTkFrame(header_card, fg_color="transparent")
        controls_frame.grid(row=0, column=1, padx=24, pady=24, sticky="e")

        def _tab_btn(txt, cmd, color="#3b82f6"): 
            return ctk.CTkButton(
                controls_frame,
                text=txt,
                font=("Inter", 13, "bold"),
                fg_color=color,
                hover_color="#2563eb",
                height=36,
                corner_radius=8,
                command=cmd
            )

        self.btn_system = _tab_btn("General", self._show_system_tab)
        self.btn_system.pack(side="left", padx=(0, 10))

        self.btn_logs = _tab_btn("Activity Logs", self._show_logs_tab, "#8b5cf6") # Violet
        self.btn_logs.pack(side="left")

        # 2. Content Area
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 20))
        self.content_area.grid_columnconfigure(0, weight=1)
        self.content_area.grid_rowconfigure(0, weight=1)

        # -- VIEW: System Settings --
        self.system_frame = ctk.CTkFrame(self.content_area, corner_radius=16, fg_color="#1e293b")
        self.system_frame.grid_columnconfigure(0, weight=1)

        # Inner Content for System Settings (Card Style)
        sys_content = ctk.CTkFrame(
            self.system_frame, 
            fg_color="#334155", # Slate 700
            border_width=1, 
            border_color="#475569", # Slate 600
            corner_radius=12
        )
        sys_content.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(sys_content, text="Preferences", font=("Inter", 18, "bold"), text_color="white").pack(pady=(20, 20), padx=40, anchor="center")

        self.logging_switch = ctk.CTkSwitch(sys_content, text="Enable Activity Logging", font=("Inter", 13), text_color="#e2e8f0", progress_color="#10b981")
        self.logging_switch.pack(pady=10, padx=40, anchor="w")
        
        self.login_popup_switch = ctk.CTkSwitch(sys_content, text="Show Login Success Popup", font=("Inter", 13), text_color="#e2e8f0", progress_color="#10b981")
        self.login_popup_switch.pack(pady=10, padx=40, anchor="w")

        ctk.CTkButton(sys_content, text="Save Changes", width=200, height=40, font=("Inter", 13, "bold"), fg_color="#3b82f6", hover_color="#2563eb", command=self._save_settings).pack(pady=(30, 20), padx=40)


        # -- VIEW: Logs --
        self.logs_frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.logs_frame.grid_columnconfigure(0, weight=1)
        self.logs_frame.grid_rowconfigure(1, weight=1)
        
        # Logs Filter Bar
        logs_controls = ctk.CTkFrame(self.logs_frame, fg_color="#1e293b", corner_radius=12)
        logs_controls.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        ctk.CTkLabel(logs_controls, text="Filter Date:", font=("Inter", 13, "bold"), text_color="#94a3b8").pack(side="left", padx=(15, 10), pady=12)
        
        self.logs_date_filter = ctk.CTkComboBox(
            logs_controls,
            values=["All dates"],
            state="readonly",
            width=160,
            font=("Inter", 13),
            fg_color="#334155",
            border_color="#475569",
            button_color="#475569",
            text_color="white",
            command=lambda _v: self._reload_logs(),
        )
        self.logs_date_filter.set("All dates")
        self.logs_date_filter.pack(side="left", pady=12)
        
        ctk.CTkButton(
            logs_controls, 
            text="Refresh", 
            width=80, 
            height=30,
            font=("Inter", 12),
            fg_color="#334155", 
            hover_color="#475569", 
            command=self._reload_logs
        ).pack(side="right", padx=15, pady=12)

        # Logs List Container
        self.logs_list = ctk.CTkScrollableFrame(self.logs_frame, corner_radius=16, fg_color="#1e293b")
        self.logs_list.grid(row=1, column=0, sticky="nsew")

        # Start on System Settings tab
        self._load_settings()
        self._show_system_tab()

    def _show_system_tab(self):
        self.logs_frame.grid_forget()
        self.system_frame.grid(row=0, column=0, sticky="nsew")

    def _show_logs_tab(self):
        self.system_frame.grid_forget()
        self.logs_frame.grid(row=0, column=0, sticky="nsew")
        self._reload_logs()

    def _load_settings(self):
        """Load current system settings into the UI."""
        logging_enabled = get_setting("activity_logging_enabled", "1") == "1"
        show_popup = get_setting("show_login_success_popup", "1") == "1"

        self.logging_switch.select() if logging_enabled else self.logging_switch.deselect()
        self.login_popup_switch.select() if show_popup else self.login_popup_switch.deselect()

    def _save_settings(self):
        """Persist system settings from the UI to the database."""
        set_setting("activity_logging_enabled", "1" if self.logging_switch.get() else "0")
        set_setting("show_login_success_popup", "1" if self.login_popup_switch.get() else "0")
        
        try:
            top = self.winfo_toplevel()
            username = getattr(top, "username", "admin")
            log_activity(username, "admin", "update_system_settings", "Updated global preferences")
        except Exception:
            pass
        
        messagebox.showinfo("Settings Saved", "System preferences have been updated successfully.")

    def _reload_logs(self):
        """Reload activity logs into the list using batched rendering."""
        for child in self.logs_list.winfo_children():
            child.destroy()

        # Fetch more logs now that we have optimized rendering
        rows = get_activity_logs(limit=200) 
        
        # Build list of unique dates
        dates: set[str] = set()
        for ts, _, _, _, _ in rows:
            if ts: dates.add(ts.split()[0])

        current = self.logs_date_filter.get()
        date_list = sorted(dates)
        values = ["All dates"] + date_list
        self.logs_date_filter.configure(values=values)
        if current not in values: current = "All dates"
        self.logs_date_filter.set(current)

        selected_date = current if current != "All dates" else None

        filtered_rows = []
        for r in rows:
            ts = r[0]
            if not ts: continue
            if selected_date and not ts.startswith(selected_date): continue
            filtered_rows.append(r)

        if not filtered_rows:
            ctk.CTkLabel(self.logs_list, text="No activity found.", font=("Inter", 14), text_color="#64748b").pack(pady=40)
            return

        # Header
        h_frame = ctk.CTkFrame(self.logs_list, fg_color="transparent")
        h_frame.pack(fill="x", padx=10, pady=(10,5))
        h_frame.grid_columnconfigure(0, weight=0, minsize=160) # Time
        h_frame.grid_columnconfigure(1, weight=0, minsize=120) # User
        h_frame.grid_columnconfigure(2, weight=0, minsize=140) # Action
        h_frame.grid_columnconfigure(3, weight=1)              # Details

        def _hl(t, c):
             ctk.CTkLabel(h_frame, text=t.upper(), font=("Inter", 11, "bold"), text_color="#64748b", anchor="w").grid(row=0, column=c, sticky="ew", padx=10)
        
        _hl("TIMESTAMP", 0)
        _hl("USER", 1)
        _hl("ACTION", 2)
        _hl("DETAILS", 3)

        # Start batch rendering
        self._render_batch(filtered_rows, 0)

    def _render_batch(self, rows, start_index):
        """Render a small batch of log rows to prevent UI freeze."""
        BATCH_SIZE = 10
        end_index = min(start_index + BATCH_SIZE, len(rows))
        
        for i in range(start_index, end_index):
            ts, username, role, action, details = rows[i]
            
            # Parse TS
            pretty_ts = ts
            try:
                dt = datetime.strptime(ts, "%Y-%m-%d %I:%M:%S %p")
                pretty_ts = dt.strftime("%b %d, %I:%M %p")
            except: pass

            row_card = ctk.CTkFrame(self.logs_list, fg_color="#334155", corner_radius=8, border_width=1, border_color="#475569")
            row_card.pack(fill="x", padx=10, pady=4)
            
            row_card.grid_columnconfigure(0, weight=0, minsize=160)
            row_card.grid_columnconfigure(1, weight=0, minsize=120)
            row_card.grid_columnconfigure(2, weight=0, minsize=140)
            row_card.grid_columnconfigure(3, weight=1)

            # 1. Timestamp
            ctk.CTkLabel(row_card, text=pretty_ts, font=("Inter", 12), text_color="#cbd5e1", anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=12)
            
            # 2. User info
            u_frame = ctk.CTkFrame(row_card, fg_color="transparent")
            u_frame.grid(row=0, column=1, sticky="w", padx=10)
            ctk.CTkLabel(u_frame, text=username or "?", font=("Inter", 13, "bold"), text_color="white", anchor="w").pack(anchor="w")
            if role:
                ctk.CTkLabel(u_frame, text=role.upper(), font=("Inter", 9, "bold"), text_color="#94a3b8", anchor="w").pack(anchor="w")
            
            # 3. Action
            ctk.CTkLabel(row_card, text=action, font=("Inter", 12, "bold"), text_color="#3b82f6", anchor="w").grid(row=0, column=2, sticky="ew", padx=10)
            
            # 4. Details
            ctk.CTkLabel(row_card, text=details or "-", font=("Inter", 12), text_color="#94a3b8", anchor="w", wraplength=400, justify="left").grid(row=0, column=3, sticky="ew", padx=10)

        if end_index < len(rows):
            # Schedule next batch
            self.after(10, lambda: self._render_batch(rows, end_index))
