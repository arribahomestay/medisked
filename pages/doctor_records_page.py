import customtkinter as ctk
import sqlite3
from datetime import datetime

from database import DB_NAME


class DoctorRecordsPage(ctk.CTkFrame):
    def __init__(self, master, doctor_name: str):
        super().__init__(master, corner_radius=0)

        self.doctor_name = doctor_name

        # Filter mode: 'recent', 'today', 'all'
        self.filter_mode = "recent"

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Records",
            font=("Segoe UI", 24, "bold"),
        )
        title.grid(row=0, column=0, padx=30, pady=(10, 4), sticky="w")

        container = ctk.CTkFrame(self, corner_radius=10)
        container.grid(row=1, column=0, padx=30, pady=(0, 24), sticky="nsew")
        container.grid_rowconfigure(2, weight=1)
        container.grid_columnconfigure(0, weight=1)

        summary = ctk.CTkLabel(
            container,
            text=f"Completed 2-hour appointments for {self.doctor_name}",
            font=("Segoe UI", 15, "bold"),
        )
        summary.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        # Filters + actions row
        controls = ctk.CTkFrame(container, fg_color="transparent")
        controls.grid(row=1, column=0, padx=16, pady=(0, 6), sticky="ew")
        controls.grid_columnconfigure(0, weight=1)
        controls.grid_columnconfigure(1, weight=0)

        filters_frame = ctk.CTkFrame(controls, fg_color="transparent")
        filters_frame.grid(row=0, column=0, sticky="w")

        self.recent_btn = ctk.CTkButton(
            filters_frame,
            text="Recent",
            width=90,
            command=lambda: self._set_filter("recent"),
        )
        self.recent_btn.grid(row=0, column=0, padx=(0, 6))

        self.today_btn = ctk.CTkButton(
            filters_frame,
            text="Today",
            width=80,
            command=lambda: self._set_filter("today"),
        )
        self.today_btn.grid(row=0, column=1, padx=6)

        self.all_btn = ctk.CTkButton(
            filters_frame,
            text="All",
            width=70,
            command=lambda: self._set_filter("all"),
        )
        self.all_btn.grid(row=0, column=2, padx=6)

        refresh_btn = ctk.CTkButton(
            controls,
            text="Refresh",
            width=90,
            fg_color="#16a34a",
            hover_color="#15803d",
            command=self._load_records,
        )
        refresh_btn.grid(row=0, column=1, padx=(6, 0), sticky="e")

        self.list_frame = ctk.CTkScrollableFrame(container, corner_radius=10)
        self.list_frame.grid(row=2, column=0, padx=16, pady=(4, 12), sticky="nsew")
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

        # Completed = past or now (schedule <= now)
        if self.filter_mode == "today":
            cur.execute(
                """
                SELECT patient_name, schedule, notes
                FROM appointments
                WHERE doctor_name = ?
                  AND DATE(schedule) = DATE('now')
                  AND DATETIME(schedule) <= DATETIME('now')
                ORDER BY DATETIME(schedule) DESC
                """,
                (self.doctor_name,),
            )
        elif self.filter_mode == "recent":
            cur.execute(
                """
                SELECT patient_name, schedule, notes
                FROM appointments
                WHERE doctor_name = ?
                  AND DATETIME(schedule) <= DATETIME('now')
                ORDER BY DATETIME(schedule) DESC
                """,
                (self.doctor_name,),
            )
        else:  # all (same as recent for now, but kept for future extension)
            cur.execute(
                """
                SELECT patient_name, schedule, notes
                FROM appointments
                WHERE doctor_name = ?
                  AND DATETIME(schedule) <= DATETIME('now')
                ORDER BY DATETIME(schedule) DESC
                """,
                (self.doctor_name,),
            )

        completed_rows = cur.fetchall()
        conn.close()

        if not completed_rows:
            lbl = ctk.CTkLabel(
                self.list_frame,
                text="No completed appointments found.",
                font=("Segoe UI", 12),
            )
            lbl.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            return

        for idx, (patient, schedule_str, notes) in enumerate(completed_rows):
            try:
                dt = datetime.strptime(schedule_str, "%Y-%m-%d %H:%M")
                pretty_date = dt.strftime("%b %d, %Y")
                pretty_time = dt.strftime("%I:%M %p")
            except Exception:
                parts = schedule_str.split()
                pretty_date = parts[0] if parts else schedule_str
                pretty_time = parts[1] if len(parts) > 1 else ""
            row_frame = ctk.CTkFrame(self.list_frame, corner_radius=6, border_width=1, border_color="#3d3d3d", fg_color="transparent")
            row_frame.grid(row=idx, column=0, sticky="ew", padx=4, pady=4)
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=0)

            # Left side content
            left_content = ctk.CTkFrame(row_frame, fg_color="transparent")
            left_content.grid(row=0, column=0, sticky="nsew", padx=12, pady=8)
            
            # Date/Time
            ctk.CTkLabel(left_content, text=f"{pretty_date} • {pretty_time}", font=("Segoe UI", 13, "bold"), text_color="white").pack(anchor="w")
            # Patient
            ctk.CTkLabel(left_content, text=f"Patient: {patient}", font=("Segoe UI", 12), text_color="gray80").pack(anchor="w")
            # Notes preview (truncated if long)
            if notes:
               note_preview = (notes[:50] + '...') if len(notes) > 50 else notes
               ctk.CTkLabel(left_content, text=f"Notes: {note_preview}", font=("Segoe UI", 11), text_color="gray60").pack(anchor="w")

            # View details button
            details_btn = ctk.CTkButton(
                row_frame,
                text="View Details",
                width=100,
                height=32,
                font=("Segoe UI", 12),
                fg_color="transparent",
                border_width=1,
                border_color="#3b82f6",
                text_color="#3b82f6",
                hover_color="#1e293b",
                command=lambda p=patient, s=schedule_str, n=notes: self._open_details(p, s, n),
            )
            details_btn.grid(row=0, column=1, padx=12, pady=8, sticky="e")

    def _set_filter(self, mode: str):
        if mode not in {"recent", "today", "all"}:
            return
        self.filter_mode = mode
        self._update_filter_buttons()
        self._load_records()

    def _update_filter_buttons(self):
        # Active filter is blue, others are gray
        active_fg = "#0d74d1"
        active_hover = "#0b63b3"
        inactive_fg = "transparent"
        inactive_hover = "#2b2b2b"

        def style(btn, active: bool):
            if active:
                btn.configure(fg_color=active_fg, hover_color=active_hover, border_width=0, text_color="white")
            else:
                btn.configure(fg_color=inactive_fg, hover_color=inactive_hover, border_width=1, border_color="#3d3d3d", text_color="gray80")

        style(self.recent_btn, self.filter_mode == "recent")
        style(self.today_btn, self.filter_mode == "today")
        style(self.all_btn, self.filter_mode == "all")

    def _open_details(self, patient: str, schedule_str: str, notes: str | None):
        """Show a compact popup with completed appointment details."""
        master = self.winfo_toplevel()
        win = ctk.CTkToplevel(master)
        win.title("")
        width, height = 500, 450
        win.geometry(f"{width}x{height}")
        win.resizable(False, False)
        win.transient(master)
        win.grab_set()

        win.grid_rowconfigure(2, weight=1)
        win.grid_columnconfigure(0, weight=1)

        try:
            dt = datetime.strptime(schedule_str, "%Y-%m-%d %H:%M")
            pretty_date = dt.strftime("%Y-%m-%d")
            pretty_time = dt.strftime("%I:%M %p")
        except Exception:
            parts = schedule_str.split()
            pretty_date = parts[0] if parts else "-"
            pretty_time = parts[1] if len(parts) > 1 else "-"

        ctk.CTkLabel(win, text="Record Details", font=("Segoe UI", 20, "bold")).grid(row=0, column=0, padx=25, pady=(25, 5), sticky="w")
        ctk.CTkLabel(win, text="Completed Appointment", font=("Segoe UI", 13), text_color="#16a34a").grid(row=1, column=0, padx=25, pady=(0, 20), sticky="w")

        body = ctk.CTkScrollableFrame(win, corner_radius=0, fg_color="transparent")
        body.grid(row=2, column=0, padx=0, pady=(0, 20), sticky="nsew")
        body.grid_columnconfigure(0, weight=1)

        rows = [
            ("Doctor", self.doctor_name or "-"),
            ("Patient", patient or "-"),
            ("Date", pretty_date),
            ("Time", pretty_time),
            ("Notes", notes or "-"),
        ]

        for idx, (label, value) in enumerate(rows):
            row_f = ctk.CTkFrame(body, corner_radius=6, border_width=1, border_color="#3d3d3d", fg_color="transparent")
            row_f.grid(row=idx, column=0, sticky="ew", padx=25, pady=5)
            row_f.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(row_f, text=label, font=("Segoe UI", 12, "bold"), text_color="gray70", width=80, anchor="w").grid(row=0, column=0, padx=15, pady=10)
            ctk.CTkLabel(row_f, text=value, font=("Segoe UI", 13), anchor="w", justify="left", wraplength=280).grid(row=0, column=1, padx=10, pady=10, sticky="w")

        close_btn = ctk.CTkButton(
            win, 
            text="Close", 
            width=100,
            fg_color="transparent", 
            border_width=1,
            border_color="#4b5563",
            text_color="#9ca3af",
            hover_color="#374151", 
            command=win.destroy
        )
        close_btn.grid(row=3, column=0, padx=25, pady=(0, 25), sticky="e")

        # Center popup over the main doctor window
        win.update_idletasks()
        master.update_idletasks()
        master_x = master.winfo_rootx()
        master_y = master.winfo_rooty()
        master_w = master.winfo_width()
        master_h = master.winfo_height()
        win_w = win.winfo_width()
        win_h = win.winfo_height()
        x = master_x + (master_w - win_w) // 2
        y = master_y + (master_h - win_h) // 2
        win.geometry(f"{win_w}x{win_h}+{x}+{y}")
