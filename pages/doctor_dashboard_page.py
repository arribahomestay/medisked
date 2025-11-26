import sqlite3

import customtkinter as ctk

from database import DB_NAME


class DoctorDashboardPage(ctk.CTkFrame):
    def __init__(self, master, doctor_id: int | None, doctor_name: str):
        super().__init__(master, corner_radius=0)

        self.doctor_id = doctor_id
        self.doctor_name = doctor_name

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text=f"Dashboard - {self.doctor_name}",
            font=("Segoe UI", 24, "bold"),
        )
        title.grid(row=0, column=0, padx=30, pady=(20, 8), sticky="w")

        content = ctk.CTkFrame(self, corner_radius=10)
        content.grid(row=1, column=0, padx=30, pady=(0, 24), sticky="nsew")
        content.grid_rowconfigure(1, weight=1)
        content.grid_columnconfigure((0, 1, 2), weight=1)

        # Load basic stats for this doctor
        total_upcoming, earnings_today, earnings_month, patients_month = self._load_stats()

        # Statistic cards row
        cards_row = ctk.CTkFrame(content, fg_color="transparent")
        cards_row.grid(row=0, column=0, columnspan=3, padx=20, pady=(16, 12), sticky="ew")
        cards_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Total upcoming appointments
        self._stat_card(
            cards_row,
            column=0,
            title="Upcoming appointments",
            value=str(total_upcoming),
            fg_color="#2563eb",  # blue
        )

        # Today's earnings
        self._stat_card(
            cards_row,
            column=1,
            title="Earnings today",
            value=f"₱{earnings_today:,.2f}",
            fg_color="#16a34a",  # green
        )

        # This month's earnings
        self._stat_card(
            cards_row,
            column=2,
            title="Earnings this month",
            value=f"₱{earnings_month:,.2f}",
            fg_color="#f59e0b",  # amber
        )

        # Unique patients seen this month
        self._stat_card(
            cards_row,
            column=3,
            title="Patients this month",
            value=str(patients_month),
            fg_color="#8b5cf6",  # violet
        )

        # Recent appointments list
        recent_frame = ctk.CTkFrame(content, corner_radius=10)
        recent_frame.grid(row=1, column=0, columnspan=3, padx=20, pady=(0, 20), sticky="nsew")
        recent_frame.grid_columnconfigure(0, weight=1)
        recent_frame.grid_rowconfigure(1, weight=1)

        header_frame = ctk.CTkFrame(recent_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        header = ctk.CTkLabel(
            header_frame,
            text="Recent appointments",
            font=("Segoe UI", 16, "bold"),
            anchor="w",
        )
        header.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        self.list_frame = ctk.CTkScrollableFrame(recent_frame, corner_radius=8)
        self.list_frame.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="nsew")
        self.list_frame.grid_columnconfigure(0, weight=1)

        self._populate_recent()

    def _connect(self):
        return sqlite3.connect(DB_NAME)

    def _load_stats(self):
        """Return (total_upcoming, earnings_today, earnings_month, patients_month)."""
        if not self.doctor_name:
            return 0, 0, 0, 0

        conn = self._connect()
        cur = conn.cursor()
        try:
            # Total upcoming (today and future)
            cur.execute(
                """
                SELECT COUNT(*)
                FROM appointments
                WHERE doctor_name = ?
                  AND DATE(schedule) >= DATE('now')
                """,
                (self.doctor_name,),
            )
            total_upcoming = cur.fetchone()[0] or 0

            # Earnings today (sum of amount_paid for this doctor)
            cur.execute(
                """
                SELECT COALESCE(SUM(amount_paid), 0)
                FROM appointments
                WHERE doctor_name = ?
                  AND is_paid = 1
                  AND DATE(schedule) = DATE('now')
                """,
                (self.doctor_name,),
            )
            earnings_today = cur.fetchone()[0] or 0

            # Earnings this month
            cur.execute(
                """
                SELECT COALESCE(SUM(amount_paid), 0)
                FROM appointments
                WHERE doctor_name = ?
                  AND is_paid = 1
                  AND strftime('%Y-%m', schedule) = strftime('%Y-%m', 'now')
                """,
                (self.doctor_name,),
            )
            earnings_month = cur.fetchone()[0] or 0

            # Unique patients this month
            cur.execute(
                """
                SELECT COUNT(DISTINCT patient_name)
                FROM appointments
                WHERE doctor_name = ?
                  AND strftime('%Y-%m', schedule) = strftime('%Y-%m', 'now')
                """,
                (self.doctor_name,),
            )
            patients_month = cur.fetchone()[0] or 0
        finally:
            conn.close()

        return total_upcoming, earnings_today, earnings_month, patients_month

    def _populate_recent(self):
        """Fill the recent appointments list for this doctor."""
        for child in self.list_frame.winfo_children():
            child.destroy()

        if not self.doctor_name:
            return

        conn = self._connect()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT patient_name, schedule, COALESCE(notes, ''), COALESCE(is_rescheduled, 0)
                FROM appointments
                WHERE doctor_name = ?
                ORDER BY DATETIME(schedule) DESC
                LIMIT 10
                """,
                (self.doctor_name,),
            )
            rows = cur.fetchall()
        finally:
            conn.close()

        if not rows:
            lbl = ctk.CTkLabel(
                self.list_frame,
                text="No recent appointments.",
                font=("Segoe UI", 13),
                anchor="w",
            )
            lbl.grid(row=0, column=0, padx=12, pady=10, sticky="w")
            return

        from datetime import datetime as _dt

        for idx, (patient_name, schedule_str, notes, is_rescheduled) in enumerate(rows):
            row_frame = ctk.CTkFrame(self.list_frame, fg_color="#111827", corner_radius=8)
            row_frame.grid(row=idx, column=0, sticky="ew", padx=4, pady=3)
            row_frame.grid_columnconfigure(0, weight=1)

            try:
                dt = _dt.strptime(schedule_str, "%Y-%m-%d %H:%M")
                when = dt.strftime("%b %d, %Y · %I:%M %p")
            except Exception:
                when = schedule_str

            # First line: date/time and optional status pill
            top_row = ctk.CTkFrame(row_frame, fg_color="transparent")
            top_row.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 2))
            top_row.grid_columnconfigure(0, weight=1)

            when_lbl = ctk.CTkLabel(top_row, text=when, font=("Segoe UI", 12, "bold"), anchor="w")
            when_lbl.grid(row=0, column=0, sticky="w")

            if is_rescheduled:
                status_lbl = ctk.CTkLabel(
                    top_row,
                    text="Rescheduled",
                    font=("Segoe UI", 11, "bold"),
                    fg_color="#f97316",
                    corner_radius=999,
                    padx=10,
                    pady=2,
                )
                status_lbl.grid(row=0, column=1, sticky="e", padx=(8, 0))

            # Second line: patient name
            patient_lbl = ctk.CTkLabel(
                row_frame,
                text=patient_name or "(No patient name)",
                font=("Segoe UI", 12),
                anchor="w",
            )
            patient_lbl.grid(row=1, column=0, sticky="w", padx=10)

            # Third line: notes (trimmed) if present
            if notes:
                notes_lbl = ctk.CTkLabel(
                    row_frame,
                    text=notes,
                    font=("Segoe UI", 11),
                    anchor="w",
                    justify="left",
                )
                notes_lbl.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 6))

            # Add a bit of bottom padding if there are no notes
            if not notes:
                row_frame.grid_configure(pady=(3, 6))

    def _stat_card(self, parent, column: int, title: str, value: str, fg_color: str):
        card = ctk.CTkFrame(parent, corner_radius=12, fg_color=fg_color)
        card.grid(row=0, column=column, padx=6, pady=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(card, text=title, font=("Segoe UI", 13, "bold"))
        title_label.grid(row=0, column=0, padx=12, pady=(10, 0), sticky="w")

        value_label = ctk.CTkLabel(card, text=value, font=("Segoe UI", 24, "bold"))
        value_label.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="w")
