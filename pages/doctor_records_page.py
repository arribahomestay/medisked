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
            text=f"Completed appointments for {self.doctor_name}",
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
            row_frame = ctk.CTkFrame(self.list_frame, corner_radius=10)
            row_frame.grid(row=idx, column=0, sticky="ew", padx=4, pady=4)
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=0)

            # Main info block
            text_lines = [
                f"{pretty_date}  {pretty_time}  ·  Patient: {patient}",
            ]
            if notes:
                text_lines.append(f"Notes: {notes}")

            info_label = ctk.CTkLabel(
                row_frame,
                text="\n".join(text_lines),
                font=("Segoe UI", 12),
                anchor="w",
                justify="left",
            )
            info_label.grid(row=0, column=0, padx=12, pady=8, sticky="nsew")

            # View details button
            details_btn = ctk.CTkButton(
                row_frame,
                text="View details",
                width=110,
                fg_color="#0d74d1",
                hover_color="#0b63b3",
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
        inactive_fg = "#4b5563"
        inactive_hover = "#374151"

        def style(btn, active: bool):
            if active:
                btn.configure(fg_color=active_fg, hover_color=active_hover)
            else:
                btn.configure(fg_color=inactive_fg, hover_color=inactive_hover)

        style(self.recent_btn, self.filter_mode == "recent")
        style(self.today_btn, self.filter_mode == "today")
        style(self.all_btn, self.filter_mode == "all")

    def _open_details(self, patient: str, schedule_str: str, notes: str | None):
        """Show a compact popup with completed appointment details."""
        master = self.winfo_toplevel()
        win = ctk.CTkToplevel(master)
        win.title("Record details")
        width, height = 520, 320
        win.geometry(f"{width}x{height}")
        win.resizable(False, False)
        win.transient(master)
        win.grab_set()

        win.grid_rowconfigure(1, weight=1)
        win.grid_columnconfigure(0, weight=1)

        try:
            dt = datetime.strptime(schedule_str, "%Y-%m-%d %H:%M")
            pretty_date = dt.strftime("%Y-%m-%d")
            pretty_time = dt.strftime("%I:%M %p")
        except Exception:
            parts = schedule_str.split()
            pretty_date = parts[0] if parts else "-"
            pretty_time = parts[1] if len(parts) > 1 else "-"

        title = ctk.CTkLabel(win, text="Completed appointment", font=("Segoe UI", 18, "bold"))
        title.grid(row=0, column=0, padx=16, pady=(14, 4), sticky="w")

        body = ctk.CTkFrame(win, corner_radius=10)
        body.grid(row=1, column=0, padx=16, pady=(4, 12), sticky="nsew")
        body.grid_columnconfigure(1, weight=1)

        rows = [
            ("Doctor", self.doctor_name or "-"),
            ("Patient", patient or "-"),
            ("Date", pretty_date),
            ("Time", pretty_time),
            ("Notes", notes or "-"),
        ]

        for idx, (label, value) in enumerate(rows):
            ctk.CTkLabel(body, text=f"{label}:", font=("Segoe UI", 12, "bold")).grid(
                row=idx, column=0, padx=10, pady=4, sticky="w"
            )
            ctk.CTkLabel(body, text=value, font=("Segoe UI", 12), anchor="w", justify="left").grid(
                row=idx, column=1, padx=10, pady=4, sticky="w"
            )

        close_btn = ctk.CTkButton(win, text="Close", fg_color="#4b5563", hover_color="#374151", command=win.destroy)
        close_btn.grid(row=2, column=0, padx=16, pady=(0, 12), sticky="e")

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
