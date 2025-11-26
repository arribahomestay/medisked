import customtkinter as ctk
import sqlite3
from datetime import datetime, date

from database import DB_NAME


class AdminDashboardPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0)

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Dashboard",
            font=("Segoe UI", 24, "bold"),
        )
        title.grid(row=0, column=0, padx=30, pady=(10, 4), sticky="w")

        content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        content.grid(row=1, column=0, padx=30, pady=(0, 24), sticky="nsew")
        content.grid_rowconfigure(1, weight=1)
        content.grid_columnconfigure(0, weight=2)
        content.grid_columnconfigure(1, weight=3)

        stats_row = ctk.CTkFrame(content, fg_color="transparent")
        stats_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        for i in range(5):
            stats_row.grid_columnconfigure(i, weight=1)

        # Users (blue)
        self.card_users = self._create_stat_card(stats_row, 0, "Users", "0", fg_color="#2563eb")
        # Active doctors (green)
        self.card_doctors = self._create_stat_card(stats_row, 1, "Doctors", "0", fg_color="#16a34a")
        # Total appointments (indigo)
        self.card_total_appt = self._create_stat_card(stats_row, 2, "Total appointments", "0", fg_color="#4f46e5")
        # Earnings today (amber)
        self.card_appointments = self._create_stat_card(stats_row, 3, "Earnings today", "₱0.00", fg_color="#f59e0b")
        # Earnings this month (rose)
        self.card_today = self._create_stat_card(stats_row, 4, "Earnings this month", "₱0.00", fg_color="#e11d48")
        # New metric: Average earnings per appointment (teal)
        self.card_avg_earnings = self._create_stat_card(stats_row, 5, "Average earnings per appointment", "₱0.00", fg_color="#2dd4bf")

        left_frame = ctk.CTkFrame(content, corner_radius=10)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        left_title = ctk.CTkLabel(
            left_frame,
            text="Appointments Analytics",
            font=("Segoe UI", 17, "bold"),
        )
        left_title.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        self.analytics_list = ctk.CTkScrollableFrame(left_frame, corner_radius=10)
        self.analytics_list.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self.analytics_list.grid_columnconfigure(0, weight=1)

        recent_frame = ctk.CTkFrame(content, corner_radius=10)
        recent_frame.grid(row=1, column=1, columnspan=1, padx=20, pady=(0, 20), sticky="nsew")
        recent_frame.grid_columnconfigure(0, weight=1)
        recent_frame.grid_rowconfigure(1, weight=1)

        recent_title = ctk.CTkLabel(
            recent_frame,
            text="Recent Appointments",
            font=("Segoe UI", 17, "bold"),
        )
        recent_title.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        self.recent_list = ctk.CTkScrollableFrame(recent_frame, corner_radius=10)
        self.recent_list.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self.recent_list.grid_columnconfigure(0, weight=1)

        self._refresh_data()

    def _connect(self):
        return sqlite3.connect(DB_NAME)

    def _create_stat_card(self, parent, column, label, value, fg_color):
        accent_colors = [
            ("#1f2933", "#3b82f6"),  # users
            ("#1f2933", "#10b981"),  # doctors
            ("#1f2933", "#f97316"),  # appointments
            ("#1f2933", "#e11d48"),  # today
            ("#1f2933", "#f59e0b"),  # appointments
            ("#1f2933", "#2dd4bf"),  # average earnings
        ]
        bg_color, value_color = accent_colors[column]

        card = ctk.CTkFrame(parent, corner_radius=10, fg_color=bg_color)
        card.grid(row=0, column=column, padx=4, sticky="nsew")
        card.grid_rowconfigure(0, weight=0)
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(card, text=label, font=("Segoe UI", 13))
        title.grid(row=0, column=0, padx=14, pady=(10, 2), sticky="w")

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=("Segoe UI", 26, "bold"),
            text_color=value_color,
        )
        value_label.grid(row=1, column=0, padx=12, pady=(0, 10), sticky="w")

        return value_label

    def _refresh_data(self):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM doctors WHERE status = 'active'")
        total_doctors = cur.fetchone()[0]

        today_str = date.today().strftime("%Y-%m-%d")
        cur.execute(
            """
            SELECT COALESCE(SUM(amount_paid), 0)
            FROM appointments
            WHERE is_paid = 1 AND DATE(schedule) = DATE('now')
            """
        )
        earnings_today = cur.fetchone()[0] or 0

        cur.execute(
            """
            SELECT COALESCE(SUM(amount_paid), 0)
            FROM appointments
            WHERE is_paid = 1
              AND strftime('%Y-%m', schedule) = strftime('%Y-%m', 'now')
            """
        )
        earnings_month = cur.fetchone()[0] or 0

        cur.execute(
            """
            SELECT patient_name, doctor_name, schedule, notes, is_paid, is_rescheduled
            FROM appointments
            ORDER BY schedule DESC
            LIMIT 8
            """
        )
        recent_rows = cur.fetchall()

        conn.close()

        # Update cards
        # Additional aggregate for total appointments
        total_appt = 0
        try:
            conn2 = self._connect()
            cur2 = conn2.cursor()
            cur2.execute("SELECT COUNT(*) FROM appointments")
            total_appt = cur2.fetchone()[0] or 0
        finally:
            try:
                conn2.close()
            except Exception:
                pass

        # Additional aggregate for average earnings per appointment
        avg_earnings = 0
        try:
            conn2 = self._connect()
            cur2 = conn2.cursor()
            cur2.execute(
                """
                SELECT COALESCE(SUM(amount_paid) / COUNT(*), 0)
                FROM appointments
                WHERE is_paid = 1
                """
            )
            avg_earnings = cur2.fetchone()[0] or 0
        finally:
            try:
                conn2.close()
            except Exception:
                pass

        self.card_users.configure(text=str(total_users))
        self.card_doctors.configure(text=str(total_doctors))
        self.card_total_appt.configure(text=str(total_appt))
        self.card_appointments.configure(text=f"₱{earnings_today:,.2f}")
        self.card_today.configure(text=f"₱{earnings_month:,.2f}")
        self.card_avg_earnings.configure(text=f"₱{avg_earnings:,.2f}")

        for child in self.analytics_list.winfo_children():
            child.destroy()

        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT doctor_name, COUNT(*) as c
            FROM appointments
            GROUP BY doctor_name
            ORDER BY c DESC
            LIMIT 5
            """
        )
        top_doctors = cur.fetchall()
        conn.close()

        if not top_doctors:
            empty = ctk.CTkLabel(
                self.analytics_list,
                text="No appointment data yet.",
                font=("Segoe UI", 13),
            )
            empty.grid(row=0, column=0, padx=8, pady=8, sticky="w")
        else:
            for idx, (doc_name, count) in enumerate(top_doctors):
                row_frame = ctk.CTkFrame(self.analytics_list, fg_color="transparent")
                row_frame.grid(row=idx, column=0, sticky="ew", pady=3)
                row_frame.grid_columnconfigure(1, weight=1)

                badge = ctk.CTkLabel(
                    row_frame,
                    text=str(count),
                    font=("Segoe UI", 15, "bold"),
                    fg_color="#2563eb",
                    corner_radius=999,
                    width=34,
                )
                badge.grid(row=0, column=0, padx=(0, 8), pady=2)

                label = ctk.CTkLabel(
                    row_frame,
                    text=f"Appointments for {doc_name}",
                    font=("Segoe UI", 13),
                    anchor="w",
                )
                label.grid(row=0, column=1, sticky="ew")

        # Recent appointments list
        for child in self.recent_list.winfo_children():
            child.destroy()

        if not recent_rows:
            empty = ctk.CTkLabel(
                self.recent_list,
                text="No appointments found.",
                font=("Segoe UI", 13),
                anchor="w",
            )
            empty.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            return

        from datetime import datetime as _dt

        for idx, (patient, doctor, schedule, notes, is_paid, is_rescheduled) in enumerate(recent_rows):
            row_frame = ctk.CTkFrame(self.recent_list, fg_color="#111827", corner_radius=8)
            row_frame.grid(row=idx, column=0, sticky="ew", padx=4, pady=3)
            row_frame.grid_columnconfigure(0, weight=1)

            try:
                dt = _dt.strptime(schedule, "%Y-%m-%d %H:%M")
                when = dt.strftime("%b %d, %Y · %I:%M %p")
            except Exception:
                when = schedule

            # Top row: when + status chips
            top = ctk.CTkFrame(row_frame, fg_color="transparent")
            top.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 2))
            top.grid_columnconfigure(0, weight=1)

            when_lbl = ctk.CTkLabel(top, text=when, font=("Segoe UI", 12, "bold"), anchor="w")
            when_lbl.grid(row=0, column=0, sticky="w")

            col_idx = 1
            if is_rescheduled:
                chip = ctk.CTkLabel(
                    top,
                    text="Rescheduled",
                    font=("Segoe UI", 11, "bold"),
                    fg_color="#f97316",
                    corner_radius=999,
                    padx=10,
                    pady=2,
                )
                chip.grid(row=0, column=col_idx, sticky="e", padx=(8, 0))
                col_idx += 1

            status_text = "PAID" if is_paid else "UNPAID"
            status_color = "#16a34a" if is_paid else "#dc2626"
            status_chip = ctk.CTkLabel(
                top,
                text=status_text,
                font=("Segoe UI", 11, "bold"),
                fg_color=status_color,
                corner_radius=999,
                padx=10,
                pady=2,
            )
            status_chip.grid(row=0, column=col_idx, sticky="e", padx=(8, 0))

            # Second row: patient + doctor
            who_text = f"{patient or '(No patient)'} with {doctor or '(No doctor)'}"
            who_lbl = ctk.CTkLabel(row_frame, text=who_text, font=("Segoe UI", 12), anchor="w")
            who_lbl.grid(row=1, column=0, sticky="w", padx=10)

            # Third row: notes (if any)
            if notes:
                notes_lbl = ctk.CTkLabel(
                    row_frame,
                    text=notes,
                    font=("Segoe UI", 11),
                    anchor="w",
                    justify="left",
                )
                notes_lbl.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 6))
