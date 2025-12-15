import customtkinter as ctk
import sqlite3
from datetime import datetime

from database import DB_NAME


class DoctorRecordsPage(ctk.CTkFrame):
    def __init__(self, master, doctor_name: str):
        super().__init__(master, corner_radius=0, fg_color="transparent")

        self.doctor_name = doctor_name
        self.filter_mode = "recent"

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header & Controls Card
        controls_frame = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=16)
        controls_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        controls_frame.grid_columnconfigure(0, weight=1)
        controls_frame.grid_columnconfigure(1, weight=0)

        # Title
        title_sub_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        title_sub_frame.grid(row=0, column=0, padx=24, pady=24, sticky="ew")
        
        ctk.CTkLabel(
            title_sub_frame,
            text="My Records", 
            font=("Inter", 20, "bold"),
            text_color="white"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_sub_frame,
            text=f"History of completed appointments for Dr. {self.doctor_name or 'Unknown'}",
            font=("Inter", 13),
            text_color="#94a3b8"
        ).pack(anchor="w", pady=(2, 0))

        # Actions (Buttons)
        actions_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        actions_frame.grid(row=0, column=1, padx=24, pady=24, sticky="e")

        self.recent_btn = ctk.CTkButton(
            actions_frame,
            text="Recent",
            width=80,
            height=36,
            corner_radius=8,
            font=("Inter", 13, "bold"),
            command=lambda: self._set_filter("recent"),
        )
        self.recent_btn.pack(side="left", padx=(0, 10))

        self.today_btn = ctk.CTkButton(
            actions_frame,
            text="Today",
            width=80,
            height=36,
            corner_radius=8,
            font=("Inter", 13, "bold"),
            command=lambda: self._set_filter("today"),
        )
        self.today_btn.pack(side="left", padx=(0, 10))

        self.all_btn = ctk.CTkButton(
            actions_frame,
            text="All",
            width=70,
            height=36,
            corner_radius=8,
            font=("Inter", 13, "bold"),
            command=lambda: self._set_filter("all"),
        )
        self.all_btn.pack(side="left", padx=(0, 10))

        self.refresh_btn = ctk.CTkButton(
            actions_frame,
            text="Refresh",
            width=80,
            height=36,
            corner_radius=8,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            font=("Inter", 13, "bold"),
            command=self._load_records,
        )
        self.refresh_btn.pack(side="left")

        # 2. Results List Container (Solid Card)
        list_container = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=16)
        list_container.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")
        list_container.grid_rowconfigure(1, weight=1)
        list_container.grid_columnconfigure(0, weight=1)

        # Header Row
        header_row = ctk.CTkFrame(list_container, fg_color="transparent", height=40)
        header_row.grid(row=0, column=0, sticky="ew", padx=(5, 20), pady=(10, 0))
        
        # Grid Cols
        header_row.grid_columnconfigure(0, weight=1) # Date
        header_row.grid_columnconfigure(1, weight=1) # Time
        header_row.grid_columnconfigure(2, weight=2) # Patient
        header_row.grid_columnconfigure(3, weight=2) # Notes
        header_row.grid_columnconfigure(4, weight=0, minsize=100) # Actions

        def _hlabel(col, text, align="w", px=10):
            ctk.CTkLabel(
                header_row, 
                text=text.upper(), 
                font=("Inter", 11, "bold"), 
                text_color="#64748b",
                anchor=align
            ).grid(row=0, column=col, sticky="ew", padx=px)

        _hlabel(0, "DATE")
        _hlabel(1, "TIME")
        _hlabel(2, "PATIENT")
        _hlabel(3, "NOTES")
        _hlabel(4, "ACTIONS", "e")

        self.list_frame = ctk.CTkScrollableFrame(list_container, corner_radius=0, fg_color="transparent")
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(10, 10))
        self.list_frame.grid_columnconfigure(0, weight=1)

        self._update_filter_buttons()
        self._load_records()

    def _connect(self):
        return sqlite3.connect(DB_NAME)

    def _load_records(self):
        for child in self.list_frame.winfo_children():
            child.destroy()

        conn = self._connect()
        cur = conn.cursor()

        # Logic: Completed = past or now (schedule <= now)
        base_query = """
            SELECT patient_name, schedule, notes
            FROM appointments
            WHERE doctor_name = ?
            AND DATETIME(schedule) <= DATETIME('now')
        """
        
        params = [self.doctor_name]

        if self.filter_mode == "today":
            base_query += " AND DATE(schedule) = DATE('now')"
        # recent/all logic same base
        
        base_query += " ORDER BY DATETIME(schedule) DESC"

        if self.filter_mode == "recent":
             base_query += " LIMIT 20"

        cur.execute(base_query, tuple(params))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            ctk.CTkLabel(
                self.list_frame,
                text="No completed appointments found.",
                font=("Inter", 14),
                text_color="#64748b"
            ).pack(pady=40)
            return

        for idx, (patient, schedule_str, notes) in enumerate(rows):
            try:
                dt = datetime.strptime(schedule_str, "%Y-%m-%d %H:%M")
                pretty_date = dt.strftime("%b %d, %Y")
                pretty_time = dt.strftime("%I:%M %p")
            except Exception:
                pretty_date = schedule_str
                pretty_time = ""

            # Row Card -> Slate 700 with outline
            row = ctk.CTkFrame(
                self.list_frame, 
                corner_radius=8, 
                fg_color="#334155", 
                border_width=1, 
                border_color="#475569",
                height=50
            )
            row.pack(fill="x", pady=5, padx=5)
            
            row.grid_columnconfigure(0, weight=1)
            row.grid_columnconfigure(1, weight=1)
            row.grid_columnconfigure(2, weight=2)
            row.grid_columnconfigure(3, weight=2)
            row.grid_columnconfigure(4, weight=0, minsize=100)

            # Date
            ctk.CTkLabel(row, text=pretty_date, font=("Inter", 13, "bold"), text_color="white", anchor="w").grid(row=0, column=0, padx=15, pady=12, sticky="ew")
            # Time
            ctk.CTkLabel(row, text=pretty_time, font=("Inter", 13), text_color="#cbd5e1", anchor="w").grid(row=0, column=1, padx=10, sticky="ew")
            # Patient
            ctk.CTkLabel(row, text=patient, font=("Inter", 13), text_color="white", anchor="w").grid(row=0, column=2, padx=10, sticky="ew")
            
            # Notes (Truncated) display as plain text or icon? Text is better for records.
            note_txt = (notes[:50] + "...") if notes and len(notes) > 50 else (notes or "-")
            ctk.CTkLabel(row, text=note_txt, font=("Inter", 12), text_color="#94a3b8", anchor="w").grid(row=0, column=3, padx=10, sticky="ew")

            # Actions
            actions_panel = ctk.CTkFrame(row, fg_color="transparent")
            actions_panel.grid(row=0, column=4, padx=10, sticky="e")
            
            btn = ctk.CTkButton(
                actions_panel,
                text="Details",
                width=60,
                height=28,
                font=("Inter", 12),
                fg_color="transparent",
                border_width=1,
                border_color="#3b82f6",
                text_color="#3b82f6",
                hover_color=("#1e293b", "#0f172a"),
                command=lambda p=patient, s=schedule_str, n=notes: self._open_details(p, s, n)
            )
            btn.pack(side="right")

    def _set_filter(self, mode: str):
        if mode not in {"recent", "today", "all"}:
            return
        self.filter_mode = mode
        self._update_filter_buttons()
        self._load_records()

    def _update_filter_buttons(self):
        # Active: Blue, Inactive: Slate 700 (#334155)
        active_fg = "#3b82f6"
        active_hover = "#2563eb"
        inactive_fg = "#334155"
        inactive_hover = "#475569"

        def style(btn, active: bool):
            if active:
                btn.configure(fg_color=active_fg, hover_color=active_hover, text_color="white")
            else:
                btn.configure(fg_color=inactive_fg, hover_color=inactive_hover, text_color="#cbd5e1")

        style(self.recent_btn, self.filter_mode == "recent")
        style(self.today_btn, self.filter_mode == "today")
        style(self.all_btn, self.filter_mode == "all")

    def _open_details(self, patient: str, schedule_str: str, notes: str | None):
        """Show a compact popup with completed appointment details."""
        master = self.winfo_toplevel()
        win = ctk.CTkToplevel(master)
        win.title("Record Details")
        win.geometry("500x500")
        win.resizable(False, False)
        win.transient(master)
        win.grab_set()
        win.configure(fg_color="#0f172a")

        win.grid_rowconfigure(2, weight=1)
        win.grid_columnconfigure(0, weight=1)

        try:
            dt = datetime.strptime(schedule_str, "%Y-%m-%d %H:%M")
            pretty_date = dt.strftime("%B %d, %Y")
            pretty_time = dt.strftime("%I:%M %p")
        except Exception:
            pretty_date = schedule_str
            pretty_time = "-"

        # Header
        ctk.CTkLabel(win, text="Record Details", font=("Inter", 20, "bold"), text_color="white").grid(row=0, column=0, padx=25, pady=(25, 5), sticky="w")
        ctk.CTkLabel(win, text="Completed Appointment", font=("Inter", 13), text_color="#10b981").grid(row=1, column=0, padx=25, pady=(0, 20), sticky="w")

        # Body Card
        body_card = ctk.CTkFrame(win, fg_color="#1e293b", corner_radius=16)
        body_card.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        body_card.grid_columnconfigure(0, weight=1)

        rows = [
            ("Doctor", self.doctor_name or "-"),
            ("Patient", patient or "-"),
            ("Date", pretty_date),
            ("Time", pretty_time),
            ("Notes", notes or "-"),
        ]

        for idx, (label, value) in enumerate(rows):
            row_f = ctk.CTkFrame(body_card, corner_radius=8, fg_color="#334155")
            row_f.pack(fill="x", padx=15, pady=6)
            
            ctk.CTkLabel(row_f, text=label, font=("Inter", 12, "bold"), text_color="#94a3b8", width=80, anchor="w").pack(side="left", padx=15, pady=12)
            ctk.CTkLabel(row_f, text=value, font=("Inter", 13), text_color="white", justify="left", wraplength=300).pack(side="left", padx=10, pady=12)

        # Close
        close_btn = ctk.CTkButton(
            win, 
            text="Close", 
            width=100,
            fg_color="transparent", 
            border_width=1,
            border_color="#64748b",
            text_color="#cbd5e1",
            hover_color="#334155", 
            font=("Inter", 13),
            command=win.destroy
        )
        close_btn.grid(row=3, column=0, padx=25, pady=(0, 25), sticky="e")

        # Center popup
        win.update_idletasks()
        try:
            x = master.winfo_rootx() + (master.winfo_width() - win.winfo_width()) // 2
            y = master.winfo_rooty() + (master.winfo_height() - win.winfo_height()) // 2
            win.geometry(f"+{x}+{y}")
        except: pass
