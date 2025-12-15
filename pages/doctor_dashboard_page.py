import sqlite3
import customtkinter as ctk
from database import DB_NAME

class DoctorDashboardPage(ctk.CTkFrame):
    def __init__(self, master, doctor_id: int | None, doctor_name: str):
        super().__init__(master, corner_radius=0, fg_color="transparent")

        self.doctor_id = doctor_id
        self.doctor_name = doctor_name

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header
        title = ctk.CTkLabel(
            self,
            text=f"Dashboard Overview",
            font=("Inter", 24, "bold"),
            text_color="white"
        )
        title.grid(row=0, column=0, padx=30, pady=(20, 10), sticky="w")

        # 2. Main Content
        content = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        content.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        content.grid_rowconfigure(1, weight=1)
        content.grid_columnconfigure(0, weight=2)
        content.grid_columnconfigure(1, weight=3)

        # Load Stats
        total_upcoming, earnings_today, earnings_month, patients_month = self._load_stats()
        
        # --- Stats Grid ---
        stats_row = ctk.CTkFrame(content, fg_color="transparent")
        stats_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        for i in range(4):
            stats_row.grid_columnconfigure(i, weight=1)

        self._create_stat_card(stats_row, 0, "UPCOMING", str(total_upcoming), "#3b82f6") # Blue
        self._create_stat_card(stats_row, 1, "EARNED TODAY", f"₱{earnings_today:,.2f}", "#f59e0b") # Amber
        self._create_stat_card(stats_row, 2, "MONTHLY EARNINGS", f"₱{earnings_month:,.2f}", "#f43f5e") # Rose
        self._create_stat_card(stats_row, 3, "TOTAL PATIENTS", str(patients_month), "#8b5cf6") # Violet

        # --- Two Columns ---
        
        # Left: Upcoming/Active Schedule Short List (Since we don't have 'Top Doctors' like admin)
        # Let's call it "Upcoming Appointments" for today to keep it relevant
        left_frame = ctk.CTkFrame(content, corner_radius=16, fg_color="#0f172a") # Darker container
        left_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left_frame,
            text="Today's Schedule",
            font=("Inter", 16, "bold"),
            text_color="#f8fafc"
        ).grid(row=0, column=0, padx=20, pady=(16, 8), sticky="w")

        self.upcoming_list = ctk.CTkScrollableFrame(left_frame, corner_radius=10, fg_color="transparent")
        self.upcoming_list.grid(row=1, column=0, padx=10, pady=(0, 16), sticky="nsew")
        self.upcoming_list.grid_columnconfigure(0, weight=1)

        # Right: Recent Activity
        recent_frame = ctk.CTkFrame(content, corner_radius=16, fg_color="#0f172a") # Darker container
        recent_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 0))
        recent_frame.grid_columnconfigure(0, weight=1)
        recent_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            recent_frame,
            text="Recent Appointments",
            font=("Inter", 16, "bold"),
            text_color="#f8fafc"
        ).grid(row=0, column=0, padx=20, pady=(16, 8), sticky="w")
        
        self.recent_list = ctk.CTkScrollableFrame(recent_frame, corner_radius=10, fg_color="transparent")
        self.recent_list.grid(row=1, column=0, padx=10, pady=(0, 16), sticky="nsew")
        self.recent_list.grid_columnconfigure(0, weight=1)

        self._populate_data()

    def _connect(self):
        return sqlite3.connect(DB_NAME)

    def _create_stat_card(self, parent, column, label, value, fg_color):
        card = ctk.CTkFrame(
            parent, 
            corner_radius=12, 
            fg_color="#334155", # Slate 700
            border_width=0
        )
        card.grid(row=0, column=column, padx=6, sticky="nsew")
        card.grid_rowconfigure(0, weight=0)
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text=label, font=("Inter", 11, "bold"), text_color="#cbd5e1").grid(row=0, column=0, padx=14, pady=(14, 2), sticky="w")

        ctk.CTkLabel(
            card,
            text=value,
            font=("Inter", 22, "bold"),
            text_color="white", 
        ).grid(row=1, column=0, padx=14, pady=(0, 14), sticky="w")
        
        # Indicator line
        ctk.CTkFrame(card, height=3, width=40, fg_color=fg_color, corner_radius=2).grid(row=2, column=0, padx=14, pady=(0, 12), sticky="w")

    def _extract_total_from_notes(self, notes: str | None) -> float | None:
        if not notes: return None
        import re
        matches = re.findall(r"[\d,]+\.?\d*", notes)
        if not matches: return None
        try:
             candidate = matches[-1].replace(",", "")
             return float(candidate)
        except: return None

    def _load_stats(self):
        if not self.doctor_name: return 0, 0, 0, 0
        conn = self._connect()
        cur = conn.cursor()
        
        cur.execute("SELECT COUNT(*) FROM appointments WHERE doctor_name=? AND DATE(schedule) >= DATE('now')", (self.doctor_name,))
        upc = cur.fetchone()[0] or 0
        
        cur.execute("SELECT COALESCE(notes,'') FROM appointments WHERE doctor_name=? AND is_paid=1 AND DATE(schedule)=DATE('now')", (self.doctor_name,))
        etoday = sum(self._extract_total_from_notes(n) or 0 for (n,) in cur.fetchall())
        
        cur.execute("SELECT COALESCE(notes,'') FROM appointments WHERE doctor_name=? AND is_paid=1 AND strftime('%Y-%m', schedule)=strftime('%Y-%m','now')", (self.doctor_name,))
        emonth = sum(self._extract_total_from_notes(n) or 0 for (n,) in cur.fetchall())
        
        cur.execute("SELECT COUNT(DISTINCT patient_name) FROM appointments WHERE doctor_name=? AND strftime('%Y-%m', schedule)=strftime('%Y-%m','now')", (self.doctor_name,))
        pmonth = cur.fetchone()[0] or 0
        
        conn.close()
        return upc, etoday, emonth, pmonth

    def _populate_data(self):
        if not self.doctor_name: return
        conn = self._connect()
        cur = conn.cursor()

        # 1. Upcoming appts (Today)
        # We will use this for the LEFT column "Today's Schedule"
        cur.execute("""
            SELECT patient_name, schedule, COALESCE(notes, ''), COALESCE(is_rescheduled, 0)
            FROM appointments
            WHERE doctor_name = ? AND DATE(schedule) = DATE('now')
            ORDER BY schedule ASC
        """, (self.doctor_name,))
        today_rows = cur.fetchall()

        # 2. Recent appts (Past, Global Recent)
        cur.execute("""
            SELECT patient_name, schedule, COALESCE(notes, ''), COALESCE(is_rescheduled, 0), is_paid
            FROM appointments
            WHERE doctor_name = ?
            ORDER BY DATETIME(schedule) DESC
            LIMIT 10
        """, (self.doctor_name,))
        recent_rows = cur.fetchall()
        
        conn.close()

        # Populate Left List (Today)
        for c in self.upcoming_list.winfo_children(): c.destroy()
        if not today_rows:
            ctk.CTkLabel(self.upcoming_list, text="No appointments today.", font=("Inter", 13), text_color="#94a3b8").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        else:
            from datetime import datetime
            for idx, (pat, sch, notes, resched) in enumerate(today_rows):
                try:
                    dt = datetime.strptime(sch, "%Y-%m-%d %H:%M")
                    t_str = dt.strftime("%I:%M %p")
                except: t_str = sch
                
                row = ctk.CTkFrame(self.upcoming_list, fg_color="#1e293b", corner_radius=8)
                row.grid(row=idx, column=0, sticky="ew", pady=4, padx=4)
                row.grid_columnconfigure(1, weight=1)

                badge_col = "#f97316" if resched else "#3b82f6"
                badge = ctk.CTkLabel(row, text=str(idx+1), font=("Inter", 14, "bold"), fg_color=badge_col, text_color="white", corner_radius=6, width=32, height=24)
                badge.grid(row=0, column=0, padx=12, pady=12)
                
                ctk.CTkLabel(row, text=pat, font=("Inter", 13, "bold"), text_color="#e2e8f0", anchor="w").grid(row=0, column=1, sticky="w", padx=(0,0))
                ctk.CTkLabel(row, text=t_str, font=("Inter", 11), text_color="#64748b").grid(row=0, column=2, sticky="e", padx=12)

        # Populate Right List (Recent Full Cards)
        for c in self.recent_list.winfo_children(): c.destroy()
        if not recent_rows:
            ctk.CTkLabel(self.recent_list, text="No recent activity.", font=("Inter", 13), text_color="#94a3b8").grid(row=0, column=0, padx=10, pady=10, sticky="w")
            return
            
        from datetime import datetime as _dt
        for idx, (pat, sch, notes, resched, is_paid) in enumerate(recent_rows):
            row_frame = ctk.CTkFrame(self.recent_list, fg_color="#1e293b", corner_radius=10)
            row_frame.grid(row=idx, column=0, sticky="ew", padx=4, pady=4)
            row_frame.grid_columnconfigure(0, weight=1)

            try:
                dt = _dt.strptime(sch, "%Y-%m-%d %H:%M")
                when = dt.strftime("%b %d, %Y • %I:%M %p")
            except: when = sch

            # Header: Date + Status
            h_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            h_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
            h_frame.grid_columnconfigure(0, weight=1)
            
            ctk.CTkLabel(h_frame, text=when, font=("Inter", 12, "bold"), text_color="#cbd5e1").grid(row=0, column=0, sticky="w")
            
            st_col = 1
            if resched:
                ctk.CTkLabel(h_frame, text="RESCHED", font=("Inter", 10, "bold"), text_color="#f97316").grid(row=0, column=st_col, padx=(0, 6)); st_col+=1
            
            p_txt, p_col = ("PAID", "#10b981") if is_paid else ("UNPAID", "#ef4444")
            ctk.CTkLabel(h_frame, text=p_txt, font=("Inter", 11, "bold"), text_color=p_col).grid(row=0, column=st_col)

            # Details
            d_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            d_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
            
            ctk.CTkLabel(d_frame, text=f"Patient: {pat}", font=("Inter", 13), text_color="white").pack(anchor="w")
            
            # Since this is doctor view, doctor name is redundant but we can show it or just show notes
            # Mimic admin style: "Doctor: [Name]"
            ctk.CTkLabel(d_frame, text=f"Doctor: {self.doctor_name}", font=("Inter", 12), text_color="#94a3b8").pack(anchor="w")
            
            if notes:
                 preview = (notes[:60] + "...") if len(notes)>60 else notes
                 ctk.CTkLabel(d_frame, text=f"📝 {preview}", font=("Inter", 11, "italic"), text_color="#64748b").pack(anchor="w", pady=(4,0))
