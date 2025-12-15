import customtkinter as ctk
import sqlite3
from datetime import datetime

from database import DB_NAME


class DoctorAppointmentsPage(ctk.CTkFrame):
    def __init__(self, master, doctor_name: str):
        super().__init__(master, corner_radius=0, fg_color="transparent")

        self.doctor_name = doctor_name
        self.filter_mode = "upcoming"

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header & Controls Card
        controls_frame = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=16)
        controls_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        controls_frame.grid_columnconfigure(0, weight=1)
        controls_frame.grid_columnconfigure(1, weight=0)

        # Title Group
        title_sub_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        title_sub_frame.grid(row=0, column=0, padx=24, pady=24, sticky="ew")
        
        ctk.CTkLabel(
            title_sub_frame,
            text="Appointments", 
            font=("Inter", 20, "bold"),
            text_color="white"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_sub_frame,
            text=f"Upcoming schedule for Dr. {self.doctor_name or 'Unknown'}",
            font=("Inter", 13),
            text_color="#94a3b8"
        ).pack(anchor="w", pady=(2, 0))

        # Actions (Buttons)
        actions_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        actions_frame.grid(row=0, column=1, padx=24, pady=24, sticky="e")

        self.upcoming_btn = ctk.CTkButton(
            actions_frame,
            text="Upcoming",
            width=90,
            height=36,
            corner_radius=8,
            font=("Inter", 13, "bold"),
            command=lambda: self._set_filter("upcoming"),
        )
        self.upcoming_btn.pack(side="left", padx=(0, 10))

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
            command=self._load_appointments,
        )
        self.refresh_btn.pack(side="left")

        # 2. Results List Container 
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
        header_row.grid_columnconfigure(3, weight=1) # Status
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
        _hlabel(3, "STATUS")
        _hlabel(4, "ACTIONS", "e")

        self.list_frame = ctk.CTkScrollableFrame(list_container, corner_radius=0, fg_color="transparent")
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(10, 10))
        self.list_frame.grid_columnconfigure(0, weight=1)

        self._update_filter_buttons()
        self._load_appointments()

    def _connect(self):
        return sqlite3.connect(DB_NAME)

    def _load_appointments(self):
        for child in self.list_frame.winfo_children():
            child.destroy()

        conn = self._connect()
        cur = conn.cursor()

        base_query = """
            SELECT patient_name, schedule, notes, COALESCE(is_rescheduled, 0), COALESCE(is_paid, 0)
            FROM appointments
            WHERE doctor_name = ?
        """
        params = [self.doctor_name]

        if self.filter_mode == "today":
            base_query += " AND DATE(schedule) = DATE('now')"
        elif self.filter_mode == "upcoming":
            base_query += " AND DATETIME(schedule) >= DATETIME('now')"
        
        base_query += " ORDER BY DATETIME(schedule)"

        cur.execute(base_query, tuple(params))
        rows = cur.fetchall()
        conn.close()

        if not rows:
            ctk.CTkLabel(
                self.list_frame,
                text="No appointments found.",
                font=("Inter", 14),
                text_color="#64748b"
            ).pack(pady=40)
            return

        for idx, (patient, schedule_str, notes, is_rescheduled, is_paid) in enumerate(rows):
            try:
                dt = datetime.strptime(schedule_str, "%Y-%m-%d %H:%M")
                pretty_date = dt.strftime("%b %d, %Y")
                pretty_time = dt.strftime("%I:%M %p")
            except Exception:
                pretty_date = schedule_str.split()[0]
                pretty_time = ""

            status_suffix = " (Rescheduled)" if is_rescheduled else ""
            paid_status = "PAID" if is_paid else "UNPAID"
            paid_color = "#10b981" if is_paid else "#ef4444"

            # Row Card -> Slate 700 (#334155) with outline
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
            row.grid_columnconfigure(3, weight=1)
            row.grid_columnconfigure(4, weight=0, minsize=100)

            # Date
            ctk.CTkLabel(row, text=pretty_date, font=("Inter", 13, "bold"), text_color="white", anchor="w").grid(row=0, column=0, padx=15, pady=12, sticky="ew")
            # Time
            t_txt = f"{pretty_time}{status_suffix}"
            ctk.CTkLabel(row, text=t_txt, font=("Inter", 13), text_color="#cbd5e1", anchor="w").grid(row=0, column=1, padx=10, sticky="ew")
            # Patient
            ctk.CTkLabel(row, text=patient, font=("Inter", 13), text_color="white", anchor="w").grid(row=0, column=2, padx=10, sticky="ew")
            
            # Status Badge Container
            status_container = ctk.CTkFrame(row, fg_color="transparent")
            status_container.grid(row=0, column=3, padx=10, sticky="w")
            
            # Rescheduled Chip?
            if is_rescheduled:
                res_chip = ctk.CTkFrame(status_container, fg_color="#f97316", corner_radius=6)
                res_chip.pack(side="left", padx=(0, 6))
                ctk.CTkLabel(res_chip, text="RESCHED", font=("Inter", 10, "bold"), text_color="white").pack(padx=6, pady=2)

            # Paid Chip
            paid_chip = ctk.CTkFrame(status_container, fg_color=paid_color, corner_radius=6)
            paid_chip.pack(side="left")
            ctk.CTkLabel(paid_chip, text=paid_status, font=("Inter", 10, "bold"), text_color="white").pack(padx=8, pady=2)

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
                command=lambda p=patient, s=schedule_str, n=notes, pd=is_paid: self._open_details(p, s, n, pd)
            )
            btn.pack(side="right")

    def _set_filter(self, mode: str):
        if mode not in {"upcoming", "today", "all"}:
            return
        self.filter_mode = mode
        self._update_filter_buttons()
        self._load_appointments()

    def _update_filter_buttons(self):
        active_fg = "#3b82f6"
        active_hover = "#2563eb"
        inactive_fg = "transparent" # Changed to transparent for tab-like feel on the slate BG? Or keep filled?
        # If we keep filled:
        inactive_fg = "#0f172a" # Darker than content (#1e293b) to look like 'slot' or lighter?
        # Admin uses #334155 (Slate 700) for unselected.
        inactive_fg = "#334155" 
        inactive_hover = "#475569"

        def style(btn, active: bool):
            if active:
                btn.configure(fg_color=active_fg, hover_color=active_hover, text_color="white")
            else:
                btn.configure(fg_color=inactive_fg, hover_color=inactive_hover, text_color="#cbd5e1")

        style(self.upcoming_btn, self.filter_mode == "upcoming")
        style(self.today_btn, self.filter_mode == "today")
        style(self.all_btn, self.filter_mode == "all")

    def _open_details(self, patient: str, schedule_str: str, notes: str | None, is_paid: int):
        master = self.winfo_toplevel()
        win = ctk.CTkToplevel(master)
        win.title("Appointment Details")
        win.geometry("500x550")
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
            pretty_time = ""

        ctk.CTkLabel(win, text="Appointment Details", font=("Inter", 20, "bold"), text_color="white").grid(row=0, column=0, padx=25, pady=(25, 5), sticky="w")
        ctk.CTkLabel(win, text=f"Scheduled for {pretty_date}", font=("Inter", 13), text_color="#94a3b8").grid(row=1, column=0, padx=25, pady=(0, 20), sticky="w")

        body = ctk.CTkScrollableFrame(win, fg_color="#1e293b", corner_radius=16)
        body.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")
        body.grid_columnconfigure(0, weight=1)

        raw = notes or ""
        
        info_lines = [
            ("Patient", patient or "-"),
            ("Date", pretty_date),
            ("Time", pretty_time),
            ("Status", "PAID" if is_paid else "UNPAID"),
        ]
        
        for label, val in info_lines:
            row_f = ctk.CTkFrame(body, corner_radius=8, fg_color="#334155")
            row_f.pack(fill="x", padx=15, pady=6)
            ctk.CTkLabel(row_f, text=label, font=("Inter", 12, "bold"), text_color="#94a3b8", width=80, anchor="w").pack(side="left", padx=15, pady=12)
            ctk.CTkLabel(row_f, text=val, font=("Inter", 13), text_color="white").pack(side="left", padx=10)

        if raw:
            notes_f = ctk.CTkFrame(body, corner_radius=8, fg_color="#334155")
            notes_f.pack(fill="x", padx=15, pady=6)
            ctk.CTkLabel(notes_f, text="DETAILS", font=("Inter", 12, "bold"), text_color="#94a3b8", width=80, anchor="w").pack(anchor="nw",padx=15, pady=(12,0))
            ctk.CTkLabel(notes_f, text=raw.replace("|", "\n"), font=("Inter", 13), text_color="white", justify="left", wraplength=400).pack(anchor="w", padx=15, pady=(5, 12))

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

        win.update_idletasks()
        try:
            x = master.winfo_rootx() + (master.winfo_width() - win.winfo_width()) // 2
            y = master.winfo_rooty() + (master.winfo_height() - win.winfo_height()) // 2
            win.geometry(f"+{x}+{y}")
        except: pass
