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
            font=("Segoe UI", 22, "bold"),
        )
        title.grid(row=0, column=0, padx=30, pady=(10, 4), sticky="w")

        content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        content.grid(row=1, column=0, padx=30, pady=(0, 24), sticky="nsew")
        content.grid_rowconfigure(1, weight=1)
        content.grid_columnconfigure(0, weight=2)
        content.grid_columnconfigure(1, weight=3)

        stats_row = ctk.CTkFrame(content, fg_color="transparent")
        stats_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        for i in range(4):
            stats_row.grid_columnconfigure(i, weight=1)

        self.card_users = self._create_stat_card(stats_row, 0, "Users", "0")
        self.card_doctors = self._create_stat_card(stats_row, 1, "Doctors", "0")
        self.card_appointments = self._create_stat_card(stats_row, 2, "Earnings today", "₱0.00")
        self.card_today = self._create_stat_card(stats_row, 3, "Earnings this month", "₱0.00")

        left_frame = ctk.CTkFrame(content, corner_radius=10)
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        left_title = ctk.CTkLabel(
            left_frame,
            text="Appointments Analytics",
            font=("Segoe UI", 16, "bold"),
        )
        left_title.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        self.analytics_list = ctk.CTkScrollableFrame(left_frame, corner_radius=10)
        self.analytics_list.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self.analytics_list.grid_columnconfigure(0, weight=1)

        right_frame = ctk.CTkFrame(content, corner_radius=10)
        right_frame.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        recent_title = ctk.CTkLabel(
            right_frame,
            text="Recent Appointments",
            font=("Segoe UI", 16, "bold"),
        )
        recent_title.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        self.recent_list = ctk.CTkScrollableFrame(right_frame, corner_radius=10)
        self.recent_list.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        self.recent_list.grid_columnconfigure(0, weight=1)

        self._refresh_data()

    def _connect(self):
        return sqlite3.connect(DB_NAME)

    def _create_stat_card(self, parent, column, label, value):
        accent_colors = [
            ("#1f2933", "#3b82f6"),  # users
            ("#1f2933", "#10b981"),  # doctors
            ("#1f2933", "#f97316"),  # appointments
            ("#1f2933", "#e11d48"),  # today
        ]
        bg_color, value_color = accent_colors[column]

        card = ctk.CTkFrame(parent, corner_radius=10, fg_color=bg_color)
        card.grid(row=0, column=column, padx=4, sticky="nsew")
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(card, text=label, font=("Segoe UI", 12))
        title.grid(row=0, column=0, padx=12, pady=(8, 0), sticky="w")

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=("Segoe UI", 22, "bold"),
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
            SELECT patient_name, doctor_name, schedule, notes
            FROM appointments
            ORDER BY schedule DESC
            LIMIT 5
            """
        )
        recent_rows = cur.fetchall()

        conn.close()

        # Update cards
        self.card_users.configure(text=str(total_users))
        self.card_doctors.configure(text=str(total_doctors))
        self.card_appointments.configure(text=f"₱{earnings_today:,.2f}")
        self.card_today.configure(text=f"₱{earnings_month:,.2f}")

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
                font=("Segoe UI", 12),
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
                    font=("Segoe UI", 14, "bold"),
                    fg_color="#2563eb",
                    corner_radius=999,
                    width=32,
                )
                badge.grid(row=0, column=0, padx=(0, 8), pady=2)

                label = ctk.CTkLabel(
                    row_frame,
                    text=f"Appointments for {doc_name}",
                    font=("Segoe UI", 12),
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
                font=("Segoe UI", 12),
            )
            empty.grid(row=0, column=0, padx=8, pady=8, sticky="w")
            return

        for idx, (patient, doctor, schedule, notes) in enumerate(recent_rows):
            row_frame = ctk.CTkFrame(self.recent_list, fg_color="transparent")
            row_frame.grid(row=idx, column=0, sticky="ew", pady=2)
            row_frame.grid_columnconfigure(0, weight=1)

            try:
                dt = datetime.strptime(schedule, "%Y-%m-%d %H:%M")
                when = dt.strftime("%b %d, %Y %I:%M %p")
            except Exception:
                when = schedule

            text = f"{when}  •  {patient} with {doctor}"
            if notes:
                text += f"  –  {notes}"

            lbl = ctk.CTkLabel(row_frame, text=text, anchor="w", justify="left")
            lbl.grid(row=0, column=0, padx=8, pady=2, sticky="ew")
