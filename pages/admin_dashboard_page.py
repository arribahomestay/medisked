import customtkinter as ctk
import sqlite3
from datetime import datetime, date

from database import DB_NAME


class AdminDashboardPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0, fg_color="transparent")

        self.grid_rowconfigure(0, weight=0, minsize=80)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Dashboard Overview",
            font=("Inter", 24, "bold"),
            text_color="white"
        )
        title.grid(row=0, column=0, padx=30, pady=(20, 10), sticky="w")

        content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        content.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        content.grid_rowconfigure(1, weight=1)
        content.grid_columnconfigure(0, weight=2)
        content.grid_columnconfigure(1, weight=3)

        stats_row = ctk.CTkFrame(content, fg_color="transparent")
        stats_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        for i in range(5):
            stats_row.grid_columnconfigure(i, weight=1)

        # Users (blue)
        self.card_users = self._create_stat_card(stats_row, 0, "TOTAL USERS", "0", fg_color="#3b82f6")
        # Active doctors (green)
        self.card_doctors = self._create_stat_card(stats_row, 1, "ACTIVE DOCTORS", "0", fg_color="#10b981")
        # Total appointments (indigo)
        self.card_total_appt = self._create_stat_card(stats_row, 2, "APPOINTMENTS", "0", fg_color="#6366f1")
        # Earnings today (amber)
        self.card_appointments = self._create_stat_card(stats_row, 3, "EARNED TODAY", "₱0.00", fg_color="#f59e0b")
        # Earnings this month (rose)
        self.card_today = self._create_stat_card(stats_row, 4, "MONTHLY EARNINGS", "₱0.00", fg_color="#f43f5e")
        # New metric: Average earnings per appointment (teal)
        self.card_avg_earnings = self._create_stat_card(stats_row, 5, "AVG. PER APPT", "₱0.00", fg_color="#14b8a6")

        left_frame = ctk.CTkFrame(content, corner_radius=16, fg_color="#0f172a") # Darker inner container
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        left_title = ctk.CTkLabel(
            left_frame,
            text="Top Doctors",
            font=("Inter", 16, "bold"),
            text_color="#f8fafc"
        )
        left_title.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="w")

        self.analytics_list = ctk.CTkScrollableFrame(left_frame, corner_radius=10, fg_color="transparent")
        self.analytics_list.grid(row=1, column=0, padx=10, pady=(0, 16), sticky="nsew")
        self.analytics_list.grid_columnconfigure(0, weight=1)

        recent_frame = ctk.CTkFrame(content, corner_radius=16, fg_color="#0f172a") # Darker inner container
        recent_frame.grid(row=1, column=1, columnspan=1, padx=(10, 0), pady=(0, 0), sticky="nsew")
        recent_frame.grid_columnconfigure(0, weight=1)
        recent_frame.grid_rowconfigure(1, weight=1)

        recent_title = ctk.CTkLabel(
            recent_frame,
            text="Recent Appointments",
            font=("Inter", 16, "bold"),
            text_color="#f8fafc"
        )
        recent_title.grid(row=0, column=0, padx=20, pady=(16, 8), sticky="w")

        self.recent_list = ctk.CTkScrollableFrame(recent_frame, corner_radius=10, fg_color="transparent")
        self.recent_list.grid(row=1, column=0, padx=10, pady=(0, 16), sticky="nsew")
        self.recent_list.grid_columnconfigure(0, weight=1)

        self._refresh_data()

    def _connect(self):
        return sqlite3.connect(DB_NAME)

    def _create_stat_card(self, parent, column, label, value, fg_color):
        # Modern filled stat card
        card = ctk.CTkFrame(
            parent, 
            corner_radius=12, 
            fg_color="#334155", # Slate 700 (Lighter than background)
            border_width=0
        )
        card.grid(row=0, column=column, padx=6, sticky="nsew")
        card.grid_rowconfigure(0, weight=0)
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(card, text=label, font=("Inter", 11, "bold"), text_color="#cbd5e1")
        title.grid(row=0, column=0, padx=14, pady=(14, 2), sticky="w")

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=("Inter", 22, "bold"),
            text_color="white", 
        )
        value_label.grid(row=1, column=0, padx=14, pady=(0, 14), sticky="w")
        
        # Indicator line
        indicator = ctk.CTkFrame(card, height=3, width=40, fg_color=fg_color, corner_radius=2)
        indicator.grid(row=2, column=0, padx=14, pady=(0, 12), sticky="w")

        return value_label

    def _extract_total_from_notes(self, notes: str | None) -> float | None:
        if not notes:
            return None
        raw = notes
        if "About:" in raw:
            after = raw.split("About:", 1)[1]
        else:
            after = raw
        digits: list[str] = []
        token = ""
        for ch in after:
            if ch.isdigit() or ch in ",.":
                token += ch
            else:
                if token:
                    digits.append(token)
                    token = ""
        if token:
            digits.append(token)
        if not digits:
            return None
        candidate = digits[-1].replace(",", "")
        try:
            value = float(candidate)
        except ValueError:
            return None
        return value

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
            SELECT COALESCE(notes, '')
            FROM appointments
            WHERE is_paid = 1 AND DATE(schedule) = DATE('now')
            """
        )
        rows_today = cur.fetchall()
        earnings_today = 0.0
        for (notes,) in rows_today:
            total = self._extract_total_from_notes(notes)
            if total is not None:
                earnings_today += total

        cur.execute(
            """
            SELECT COALESCE(notes, '')
            FROM appointments
            WHERE is_paid = 1
              AND strftime('%Y-%m', schedule) = strftime('%Y-%m', 'now')
            """
        )
        rows_month = cur.fetchall()
        earnings_month = 0.0
        for (notes,) in rows_month:
            total = self._extract_total_from_notes(notes)
            if total is not None:
                earnings_month += total

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
        avg_earnings = 0.0
        try:
            conn2 = self._connect()
            cur2 = conn2.cursor()
            cur2.execute(
                """
                SELECT COALESCE(notes, '')
                FROM appointments
                WHERE is_paid = 1
                """
            )
            rows = cur2.fetchall()
            totals: list[float] = []
            for (notes,) in rows:
                total = self._extract_total_from_notes(notes)
                if total is not None:
                    totals.append(total)
            if totals:
                avg_earnings = sum(totals) / len(totals)
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
                text_color="#94a3b8"
            )
            empty.grid(row=0, column=0, padx=8, pady=8, sticky="w")
        else:
            for idx, (doc_name, count) in enumerate(top_doctors):
                row_frame = ctk.CTkFrame(
                    self.analytics_list, 
                    fg_color="#1e293b", # Card on dark bg
                    corner_radius=8, 
                    border_width=0
                )
                row_frame.grid(row=idx, column=0, sticky="ew", pady=4, padx=4)
                row_frame.grid_columnconfigure(1, weight=1)

                # Badge
                badge = ctk.CTkLabel(
                    row_frame,
                    text=str(count),
                    font=("Inter", 14, "bold"),
                    fg_color="#3b82f6", # Blue accent
                    text_color="white",
                    corner_radius=6,
                    width=32,
                    height=24
                )
                badge.grid(row=0, column=0, padx=12, pady=12)

                label = ctk.CTkLabel(
                    row_frame,
                    text=f"{doc_name}",
                    font=("Inter", 13, "bold"),
                    text_color="#e2e8f0",
                    anchor="w",
                )
                label.grid(row=0, column=1, sticky="w", padx=(0, 10))

                # Optional descriptive suffix
                sub = ctk.CTkLabel(
                    row_frame, 
                    text="appointments", 
                    font=("Segoe UI", 11), 
                    text_color="#64748b"
                )
                sub.grid(row=0, column=2, sticky="e", padx=12)

        # Recent appointments list
        for child in self.recent_list.winfo_children():
            child.destroy()

        if not recent_rows:
            empty = ctk.CTkLabel(
                self.recent_list,
                text="No appointments found.",
                font=("Segoe UI", 13),
                text_color="#94a3b8",
                anchor="w",
            )
            empty.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            return

        from datetime import datetime as _dt

        for idx, (patient, doctor, schedule, notes, is_paid, is_rescheduled) in enumerate(recent_rows):
            # Filled card style
            row_frame = ctk.CTkFrame(
                self.recent_list, 
                fg_color="#1e293b", # Card on dark bg
                border_width=0, 
                corner_radius=10
            )
            row_frame.grid(row=idx, column=0, sticky="ew", padx=4, pady=4)
            row_frame.grid_columnconfigure(0, weight=1)

            try:
                dt = _dt.strptime(schedule, "%Y-%m-%d %H:%M")
                when = dt.strftime("%b %d, %Y • %I:%M %p")
            except Exception:
                when = schedule

            # 1. Header Row (Date + Status Chips)
            header_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            header_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
            header_frame.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(header_frame, text=when, font=("Inter", 12, "bold"), text_color="#cbd5e1").grid(row=0, column=0, sticky="w")

            status_text = "PAID" if is_paid else "UNPAID"
            status_color = "#10b981" if is_paid else "#ef4444" # Green / Red
            
            # Use small text or icon for status? Chip is good.
            if is_rescheduled:
                ctk.CTkLabel(header_frame, text="RESCHED", font=("Inter", 10, "bold"), text_color="#f97316").grid(row=0, column=1, padx=(0, 8))
            
            # Simple text label for status instead of heavy button-like chip
            ctk.CTkLabel(header_frame, text=status_text, font=("Inter", 11, "bold"), text_color=status_color).grid(row=0, column=2)

            # 2. Details Row
            details_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            details_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
            
            # Patient Info
            ctk.CTkLabel(details_frame, text=f"Patient: {patient or '-'}", font=("Inter", 13), text_color="white").pack(anchor="w")
            ctk.CTkLabel(details_frame, text=f"Doctor: {doctor or '-'}", font=("Inter", 12), text_color="#94a3b8").pack(anchor="w")

            if notes:
                # Truncate notes if too long
                preview = (notes[:60] + '...') if len(notes) > 60 else notes
                ctk.CTkLabel(details_frame, text=f"📝 {preview}", font=("Inter", 11, "italic"), text_color="#64748b").pack(anchor="w", pady=(4,0))
