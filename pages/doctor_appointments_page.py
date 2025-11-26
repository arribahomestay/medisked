import customtkinter as ctk
import sqlite3
from datetime import datetime

from database import DB_NAME


class DoctorAppointmentsPage(ctk.CTkFrame):
    def __init__(self, master, doctor_name: str):
        super().__init__(master, corner_radius=0)

        self.doctor_name = doctor_name

        # Filter mode: 'upcoming', 'today', 'all'
        self.filter_mode = "upcoming"

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Appointments",
            font=("Segoe UI", 24, "bold"),
        )
        title.grid(row=0, column=0, padx=30, pady=(10, 4), sticky="w")

        container = ctk.CTkFrame(self, corner_radius=10)
        container.grid(row=1, column=0, padx=30, pady=(0, 24), sticky="nsew")
        container.grid_rowconfigure(2, weight=1)
        container.grid_columnconfigure(0, weight=1)

        summary = ctk.CTkLabel(
            container,
            text=f"Upcoming appointments for {self.doctor_name}",
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

        self.upcoming_btn = ctk.CTkButton(
            filters_frame,
            text="Upcoming",
            width=90,
            command=lambda: self._set_filter("upcoming"),
        )
        self.upcoming_btn.grid(row=0, column=0, padx=(0, 6))

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
            command=self._load_appointments,
        )
        refresh_btn.grid(row=0, column=1, padx=(6, 0), sticky="e")

        self.list_frame = ctk.CTkScrollableFrame(container, corner_radius=10)
        self.list_frame.grid(row=2, column=0, padx=16, pady=(4, 12), sticky="nsew")
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

        # Build query based on current filter mode
        if self.filter_mode == "today":
            cur.execute(
                """
                SELECT patient_name, schedule, notes, COALESCE(is_rescheduled, 0), COALESCE(is_paid, 0)
                FROM appointments
                WHERE doctor_name = ?
                  AND DATE(schedule) = DATE('now')
                ORDER BY DATETIME(schedule)
                """,
                (self.doctor_name,),
            )
        elif self.filter_mode == "upcoming":
            cur.execute(
                """
                SELECT patient_name, schedule, notes, COALESCE(is_rescheduled, 0), COALESCE(is_paid, 0)
                FROM appointments
                WHERE doctor_name = ?
                  AND DATETIME(schedule) >= DATETIME('now')
                ORDER BY DATETIME(schedule)
                """,
                (self.doctor_name,),
            )
        else:  # all
            cur.execute(
                """
                SELECT patient_name, schedule, notes, COALESCE(is_rescheduled, 0), COALESCE(is_paid, 0)
                FROM appointments
                WHERE doctor_name = ?
                ORDER BY DATETIME(schedule)
                """,
                (self.doctor_name,),
            )

        rows = cur.fetchall()
        conn.close()

        if not rows:
            lbl = ctk.CTkLabel(
                self.list_frame,
                text="No appointments scheduled.",
                font=("Segoe UI", 12),
            )
            lbl.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            return

        for idx, (patient, schedule_str, notes, is_rescheduled, is_paid) in enumerate(rows):
            try:
                dt = datetime.strptime(schedule_str, "%Y-%m-%d %H:%M")
                pretty_date = dt.strftime("%b %d, %Y")
                pretty_time = dt.strftime("%I:%M %p")
            except Exception:
                pretty_date = schedule_str.split()[0]
                pretty_time = schedule_str.split()[1] if " " in schedule_str else ""
            row = ctk.CTkFrame(self.list_frame, corner_radius=10)
            row.grid(row=idx, column=0, sticky="ew", padx=4, pady=4)
            row.grid_columnconfigure(0, weight=1)
            row.grid_columnconfigure(1, weight=0)

            # Main info block
            status_suffix = " (Rescheduled)" if is_rescheduled else ""
            paid_status = "PAID" if is_paid else "UNPAID"
            text_lines = [
                f"{pretty_date}  {pretty_time}{status_suffix}  ·  Patient: {patient}",
                f"Status: {paid_status}",
            ]
            if notes:
                text_lines.append(f"Notes: {notes}")

            info_label = ctk.CTkLabel(
                row,
                text="\n".join(text_lines),
                font=("Segoe UI", 12),
                anchor="w",
                justify="left",
            )
            info_label.grid(row=0, column=0, padx=12, pady=8, sticky="nsew")

            # View details button
            details_btn = ctk.CTkButton(
                row,
                text="View details",
                width=110,
                fg_color="#0d74d1",
                hover_color="#0b63b3",
                command=lambda p=patient, s=schedule_str, n=notes, paid=is_paid: self._open_details(p, s, n, paid),
            )
            details_btn.grid(row=0, column=1, padx=12, pady=8, sticky="e")

    def _set_filter(self, mode: str):
        if mode not in {"upcoming", "today", "all"}:
            return
        self.filter_mode = mode
        self._update_filter_buttons()
        self._load_appointments()

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

        style(self.upcoming_btn, self.filter_mode == "upcoming")
        style(self.today_btn, self.filter_mode == "today")
        style(self.all_btn, self.filter_mode == "all")

    def _open_details(self, patient: str, schedule_str: str, notes: str | None, is_paid: int):
        """Show a compact popup with appointment details."""
        master = self.winfo_toplevel()
        win = ctk.CTkToplevel(master)
        win.title("Appointment details")
        # Slightly larger so all information is visible
        width, height = 560, 420
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

        title = ctk.CTkLabel(win, text="Appointment", font=("Segoe UI", 18, "bold"))
        title.grid(row=0, column=0, padx=16, pady=(14, 4), sticky="w")

        body = ctk.CTkFrame(win, corner_radius=10)
        body.grid(row=1, column=0, padx=16, pady=(4, 12), sticky="nsew")
        body.grid_columnconfigure(1, weight=1)

        raw = notes or ""
        parts = [p.strip() for p in raw.split("|") if p.strip()]
        values = {"Contact": "", "Address": "", "About": "", "Notes": ""}
        for p in parts:
            if ":" in p:
                key, val = p.split(":", 1)
                key = key.strip()
                val = val.strip()
                if key in values:
                    values[key] = val
                else:
                    if values["Notes"]:
                        values["Notes"] += " " + p
                    else:
                        values["Notes"] = p
            else:
                if values["Notes"]:
                    values["Notes"] += " " + p
                else:
                    values["Notes"] = p

        rows = [
            ("Doctor", self.doctor_name or "-"),
            ("Patient", patient or "-"),
            ("Date", pretty_date),
            ("Time", pretty_time),
            ("Status", "PAID" if is_paid else "UNPAID"),
            ("Contact", values["Contact"] or "-"),
            ("Address", values["Address"] or "-"),
            ("About", values["About"] or "-"),
            ("Notes", values["Notes"] or "-"),
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

        # Center the popup relative to the main doctor window
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
