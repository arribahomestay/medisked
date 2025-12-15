import customtkinter as ctk
import sqlite3
import calendar
from datetime import date
from datetime import datetime as _dt, timedelta as _td

from database import DB_NAME


class ReceptionistSchedulePage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0, fg_color="transparent")

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header Card
        header_card = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=16)
        header_card.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        header_card.grid_columnconfigure(0, weight=1)

        title_frame = ctk.CTkFrame(header_card, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=24, pady=24, sticky="ew")
        
        ctk.CTkLabel(
            title_frame, 
            text="Scheduling", 
            font=("Inter", 20, "bold"), 
            text_color="white"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame, 
            text="View availability and booked time slots.", 
            font=("Inter", 13), 
            text_color="#94a3b8"
        ).pack(anchor="w", pady=(2, 0))

        # 2. Controls & Calendar Card
        content_card = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=16)
        content_card.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        content_card.grid_columnconfigure(0, weight=1)
        content_card.grid_rowconfigure(1, weight=1)

        # Filters Row
        controls_frame = ctk.CTkFrame(content_card, fg_color="transparent")
        controls_frame.grid(row=0, column=0, padx=24, pady=(24, 0), sticky="ew")
        controls_frame.grid_columnconfigure(1, weight=1)
        controls_frame.grid_columnconfigure(2, weight=0)

        ctk.CTkLabel(controls_frame, text="Doctor:", font=("Inter", 13, "bold"), text_color="#cbd5e1").pack(side="left", padx=(0, 10))
        self.doctor_combo = ctk.CTkComboBox(
            controls_frame,
            values=[],
            state="readonly",
            height=36,
            width=200,
            font=("Inter", 13),
            fg_color="#334155",
            border_color="#475569",
            text_color="white",
            dropdown_fg_color="#334155",
            command=lambda _val: self._on_doctor_changed(),
        )
        self.doctor_combo.pack(side="left")

        # Month Nav
        nav_frame = ctk.CTkFrame(controls_frame, fg_color="#0f172a", corner_radius=8)
        nav_frame.pack(side="right")
        
        self.current_year = date.today().year
        self.current_month = date.today().month

        ctk.CTkButton(
            nav_frame, text="<", width=32, height=32, fg_color="transparent", hover_color="#334155", 
            command=self._prev_month
        ).pack(side="left", padx=2, pady=2)
        
        self.month_label = ctk.CTkLabel(nav_frame, text="", font=("Inter", 13, "bold"), text_color="white", width=140)
        self.month_label.pack(side="left", padx=5)
        
        ctk.CTkButton(
            nav_frame, text=">", width=32, height=32, fg_color="transparent", hover_color="#334155", 
            command=self._next_month
        ).pack(side="left", padx=2, pady=2)

        # Calendar Grid
        self.calendar_frame = ctk.CTkFrame(content_card, corner_radius=12, fg_color="#0f172a", border_width=1, border_color="#334155")
        self.calendar_frame.grid(row=1, column=0, padx=24, pady=20, sticky="nsew")
        for col in range(7):
            self.calendar_frame.grid_columnconfigure(col, weight=1, uniform="cal_cols")
        for r in range(7): # max rows
            self.calendar_frame.grid_rowconfigure(r, weight=1, uniform="cal_rows")

        # Detail Section
        details_container = ctk.CTkFrame(content_card, fg_color="transparent")
        details_container.grid(row=2, column=0, padx=24, pady=(0, 24), sticky="nsew")
        details_container.grid_columnconfigure(0, weight=1)
        details_container.grid_rowconfigure(1, weight=1)

        self.day_detail_label = ctk.CTkLabel(
            details_container, 
            text="Select a day to view configured time slots.", 
            font=("Inter", 14, "bold"), 
            text_color="#f8fafc",
            anchor="w"
        )
        self.day_detail_label.grid(row=0, column=0, pady=(0, 10), sticky="w")

        # Slots Details Frame
        self.slots_frame = ctk.CTkScrollableFrame(details_container, corner_radius=10, fg_color="#0f172a", height=150)
        self.slots_frame.grid(row=1, column=0, sticky="nsew")
        self.slots_frame.grid_columnconfigure(0, weight=1)

        self._load_doctors()
        self._refresh_calendar()

    def _connect(self):
        return sqlite3.connect(DB_NAME)

    def _load_doctors(self):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT name FROM doctors WHERE status = 'active' ORDER BY name")
        names = [row[0] for row in cur.fetchall()]
        conn.close()

        if names:
            self.doctor_combo.configure(values=names, state="readonly")
            self.doctor_combo.set(names[0])
        else:
            self.doctor_combo.configure(values=["Add doctor first"], state="disabled")
            self.doctor_combo.set("Add doctor first")

    def _on_doctor_changed(self):
        self._refresh_calendar()

    def _prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self._refresh_calendar()

    def _next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self._refresh_calendar()

    def _refresh_calendar(self):
        for child in self.calendar_frame.winfo_children():
            child.destroy()

        self.month_label.configure(text=f"{calendar.month_name[self.current_month]} {self.current_year}")

        # Headings
        for i, wd in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            ctk.CTkLabel(self.calendar_frame, text=wd, font=("Inter", 12, "bold"), text_color="#94a3b8").grid(row=0, column=i, pady=(10, 5))

        not_available_days = set()
        selected_doctor = self.doctor_combo.get().strip()

        if selected_doctor and selected_doctor != "Add doctor first":
            conn = self._connect()
            cur = conn.cursor()
            cur.execute("SELECT id FROM doctors WHERE name = ? AND status = 'active'", (selected_doctor,))
            row = cur.fetchone()
            if row:
                doctor_id = row[0]
                month_start = f"{self.current_year:04d}-{self.current_month:02d}-01"
                month_end = f"{self.current_year:04d}-{self.current_month:02d}-31"
                cur.execute(
                    "SELECT date FROM doctor_availability WHERE doctor_id = ? AND date BETWEEN ? AND ? AND start_time IS NULL AND is_available = 0",
                    (doctor_id, month_start, month_end),
                )
                not_available_days = {d for (d,) in cur.fetchall()}
            conn.close()

        cal = calendar.Calendar(firstweekday=0)
        today_str = date.today().strftime("%Y-%m-%d")
        
        row = 1
        for week in cal.monthdayscalendar(self.current_year, self.current_month):
            for col, day_num in enumerate(week):
                if day_num == 0: continue
                d_str = f"{self.current_year:04d}-{self.current_month:02d}-{day_num:02d}"

                if d_str < today_str:
                    bg, hover, state = "#1e293b", "#1e293b", "disabled" # Past
                    fg = "#64748b"
                    cmd = None
                elif d_str in not_available_days:
                    bg, hover, state = "#991b1b", "#991b1b", "disabled" # Unavailable (Red)
                    fg = "white"
                    cmd = None
                else:
                    bg, hover, state = "#10b981", "#059669", "normal" # Available (Green)
                    fg = "white"
                    cmd = lambda ds=d_str: self._open_day_detail(ds)

                btn = ctk.CTkButton(
                    self.calendar_frame,
                    text=str(day_num),
                    width=40,
                    height=40,
                    font=("Inter", 14),
                    fg_color=bg,
                    hover_color=hover,
                    text_color=fg,
                    state=state,
                    command=cmd,
                )
                btn.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
            row += 1

        self._clear_day_slots()

    def _clear_day_slots(self):
        for child in self.slots_frame.winfo_children():
            child.destroy()
        self.day_detail_label.configure(text="Select a day to view configured time slots.")

    def _open_day_detail(self, d_str: str):
        for child in self.slots_frame.winfo_children():
            child.destroy()

        selected_doctor = self.doctor_combo.get().strip()
        if not selected_doctor or selected_doctor == "Add doctor first":
            self.day_detail_label.configure(text="Add a doctor first.")
            return

        pretty_date = _dt.strptime(d_str, "%Y-%m-%d").strftime("%B %d, %Y")
        self.day_detail_label.configure(text=f"{pretty_date} – Schedule for Dr. {selected_doctor}")

        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT id FROM doctors WHERE name = ? AND status = 'active'", (selected_doctor,))
        row = cur.fetchone()
        if not row:
            conn.close(); return

        doctor_id = row[0]

        # Load Availability
        cur.execute(
            "SELECT start_time, end_time FROM doctor_availability WHERE doctor_id = ? AND date = ? AND is_available = 1 AND start_time IS NOT NULL ORDER BY start_time",
            (doctor_id, d_str),
        )
        slots = cur.fetchall()

        # Load Bookings
        cur.execute(
            "SELECT patient_name, schedule FROM appointments WHERE doctor_name = ? AND DATE(schedule) = ? ORDER BY DATETIME(schedule)",
            (selected_doctor, d_str),
        )
        bookings = cur.fetchall()
        conn.close()

        # Layout: 2 Columns (Configured Slots | Bookings) inside the Frame
        grid_layout = ctk.CTkFrame(self.slots_frame, fg_color="transparent")
        grid_layout.pack(fill="both", expand=True, padx=10, pady=10)
        grid_layout.grid_columnconfigure(0, weight=1)
        grid_layout.grid_columnconfigure(1, weight=1)

        # Left: Configured Ranges
        l_frame = ctk.CTkFrame(grid_layout, fg_color="#1e293b", corner_radius=8)
        l_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(l_frame, text="OPEN TIME WINDOWS", font=("Inter", 11, "bold"), text_color="#94a3b8").pack(anchor="w", padx=10, pady=(10, 5))
        
        if not slots:
             ctk.CTkLabel(l_frame, text="No availability set (Standard 9-5).", font=("Inter", 12), text_color="#64748b").pack(anchor="w", padx=10)
        else:
            for s, e in slots:
                # 12hr fmt
                s_fmt = _dt.strptime(s, "%H:%M").strftime("%I:%M %p").lstrip("0")
                e_fmt = _dt.strptime(e, "%H:%M").strftime("%I:%M %p").lstrip("0")
                row_item = ctk.CTkFrame(l_frame, fg_color="#334155", corner_radius=6)
                row_item.pack(fill="x", padx=10, pady=2)
                ctk.CTkLabel(row_item, text=f"{s_fmt} - {e_fmt}", font=("Inter", 12), text_color="white").pack(anchor="w", padx=10, pady=5)

        # Right: Real Appointments
        r_frame = ctk.CTkFrame(grid_layout, fg_color="#1e293b", corner_radius=8)
        r_frame.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(r_frame, text="CONFIRMED BOOKINGS", font=("Inter", 11, "bold"), text_color="#94a3b8").pack(anchor="w", padx=10, pady=(10, 5))

        if not bookings:
             ctk.CTkLabel(r_frame, text="No appointments yet.", font=("Inter", 12), text_color="#64748b").pack(anchor="w", padx=10)
        else:
             for idx, (p_name, sch) in enumerate(bookings, 1):
                try:
                    s_dt = _dt.strptime(sch, "%Y-%m-%d %H:%M")
                    e_dt = s_dt + _td(hours=2)
                    time_str = f"{s_dt.strftime('%I:%M %p')} - {e_dt.strftime('%I:%M %p')}".replace(" 0", " ")
                except: time_str = sch
                
                row_item = ctk.CTkFrame(r_frame, fg_color="#334155", corner_radius=6)
                row_item.pack(fill="x", padx=10, pady=2)
                
                # Time
                ctk.CTkLabel(row_item, text=time_str, font=("Inter", 12, "bold"), text_color="#3b82f6").pack(side="left", padx=10, pady=5)
                # Patient
                ctk.CTkLabel(row_item, text=p_name, font=("Inter", 12), text_color="white").pack(side="left", padx=5)
