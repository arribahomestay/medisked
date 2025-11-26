import customtkinter as ctk
import sqlite3
import calendar
from datetime import date

from database import DB_NAME


class ReceptionistSchedulePage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Schedule",
            font=("Segoe UI", 24, "bold"),
        )
        title.grid(row=0, column=0, padx=30, pady=(10, 4), sticky="w")

        content = ctk.CTkFrame(self, corner_radius=10)
        content.grid(row=1, column=0, padx=30, pady=(0, 16), sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        # Row 2 (calendar) gets the extra vertical space; lower rows keep natural size
        content.grid_rowconfigure(2, weight=1)

        # Top row: doctor selector
        top_row = ctk.CTkFrame(content, fg_color="transparent")
        top_row.grid(row=0, column=0, padx=16, pady=(8, 2), sticky="ew")
        top_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(top_row, text="Doctor").grid(row=0, column=0, padx=(0, 8), pady=4, sticky="w")
        self.doctor_combo = ctk.CTkComboBox(
            top_row,
            values=[],
            state="readonly",
            command=lambda _val: self._on_doctor_changed(),
        )
        self.doctor_combo.grid(row=0, column=1, padx=(0, 0), pady=4, sticky="ew")

        # Month navigation row
        controls = ctk.CTkFrame(content, fg_color="transparent")
        controls.grid(row=1, column=0, padx=16, pady=(2, 0), sticky="ew")
        controls.grid_columnconfigure(1, weight=1)

        self.current_year = date.today().year
        self.current_month = date.today().month

        prev_btn = ctk.CTkButton(controls, text="<", width=32, command=self._prev_month)
        prev_btn.grid(row=0, column=0, padx=(0, 5))

        self.month_label = ctk.CTkLabel(controls, text="", font=("Segoe UI", 14, "bold"))
        self.month_label.grid(row=0, column=1, sticky="w")

        next_btn = ctk.CTkButton(controls, text=">", width=32, command=self._next_month)
        next_btn.grid(row=0, column=2, padx=(5, 0))

        # Calendar grid
        self.calendar_frame = ctk.CTkFrame(content, corner_radius=10)
        self.calendar_frame.grid(row=2, column=0, padx=16, pady=(6, 4), sticky="nsew")
        for col in range(7):
            self.calendar_frame.grid_columnconfigure(col, weight=1)

        # Day slots details
        self.day_detail_label = ctk.CTkLabel(
            content,
            text="Select a day to view configured time slots.",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        self.day_detail_label.grid(row=3, column=0, padx=16, pady=(2, 2), sticky="w")

        # Slots frame sized so everything fits in the fixed main window
        self.slots_frame = ctk.CTkScrollableFrame(content, corner_radius=10, height=120)
        self.slots_frame.grid(row=4, column=0, padx=16, pady=(0, 6), sticky="nsew")
        self.slots_frame.grid_columnconfigure(0, weight=1)

        # Load doctors and initial calendar
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
            # No doctors yet: show message and disable selection
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

        self.month_label.configure(
            text=f"{calendar.month_name[self.current_month]} {self.current_year}"
        )

        # Weekday headers
        for i, wd in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            lbl = ctk.CTkLabel(self.calendar_frame, text=wd, font=("Segoe UI", 12, "bold"))
            lbl.grid(row=0, column=i, pady=(0, 5))

        # Compute days explicitly marked not available for the selected doctor
        not_available_days = set()
        selected_doctor = self.doctor_combo.get().strip()

        if selected_doctor and selected_doctor != "Add doctor first":
            conn = self._connect()
            cur = conn.cursor()
            cur.execute("SELECT id FROM doctors WHERE name = ? AND status = 'active'", (selected_doctor,))
            row = cur.fetchone()
            if row is not None:
                doctor_id = row[0]
                month_start = f"{self.current_year:04d}-{self.current_month:02d}-01"
                month_end = f"{self.current_year:04d}-{self.current_month:02d}-31"
                cur.execute(
                    """
                    SELECT date FROM doctor_availability
                    WHERE doctor_id = ?
                      AND date BETWEEN ? AND ?
                      AND start_time IS NULL
                      AND is_available = 0
                    """,
                    (doctor_id, month_start, month_end),
                )
                not_available_days = {d for (d,) in cur.fetchall()}
            conn.close()

        cal = calendar.Calendar(firstweekday=0)
        from datetime import date as _date
        today_str = _date.today().strftime("%Y-%m-%d")
        row = 1
        for week in cal.monthdayscalendar(self.current_year, self.current_month):
            for col, day_num in enumerate(week):
                if day_num == 0:
                    continue
                d_str = f"{self.current_year:04d}-{self.current_month:02d}-{day_num:02d}"

                # Past dates are gray and disabled
                if d_str < today_str:
                    fg = "#555555"
                    state = "disabled"
                    cmd = None
                elif d_str in not_available_days:
                    fg = "#c0392b"  # red = not available
                    state = "disabled"
                    cmd = None
                else:
                    fg = "#1c9b3b"  # green = available by default
                    state = "normal"
                    cmd = lambda ds=d_str: self._open_day_detail(ds)

                btn = ctk.CTkButton(
                    self.calendar_frame,
                    text=str(day_num),
                    width=40,
                    height=32,
                    fg_color=fg,
                    state=state,
                    command=cmd,
                )
                btn.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
            row += 1

        # Clear slots when month/doctor changes until a day is selected
        self._clear_day_slots()

    def _clear_day_slots(self):
        for child in self.slots_frame.winfo_children():
            child.destroy()
        self.day_detail_label.configure(text="Select a day to view configured time slots.")

    def _open_day_detail(self, d_str: str):
        """Load configured availability slots for the selected doctor and date."""
        for child in self.slots_frame.winfo_children():
            child.destroy()

        selected_doctor = self.doctor_combo.get().strip()
        if not selected_doctor or selected_doctor == "Add doctor first":
            self.day_detail_label.configure(text="Add a doctor first.")
            return

        self.day_detail_label.configure(text=f"Date: {d_str} – configured time slots and bookings")

        conn = self._connect()
        cur = conn.cursor()

        # Resolve doctor id
        cur.execute("SELECT id FROM doctors WHERE name = ? AND status = 'active'", (selected_doctor,))
        row = cur.fetchone()
        if row is None:
            conn.close()
            lbl = ctk.CTkLabel(self.slots_frame, text="Doctor record not found.")
            lbl.grid(row=0, column=0, padx=8, pady=8, sticky="w")
            return

        doctor_id = row[0]

        # Load slot rows for this day
        cur.execute(
            """
            SELECT start_time, end_time, max_appointments, slot_length_minutes
            FROM doctor_availability
            WHERE doctor_id = ? AND date = ? AND is_available = 1 AND start_time IS NOT NULL
            ORDER BY start_time
            """,
            (doctor_id, d_str),
        )
        slots = cur.fetchall()

        # Load booked appointments for this doctor and day
        cur.execute(
            """
            SELECT patient_name, schedule
            FROM appointments
            WHERE doctor_name = ? AND DATE(schedule) = ?
            ORDER BY DATETIME(schedule)
            """,
            (selected_doctor, d_str),
        )
        bookings = cur.fetchall()
        conn.close()

        # Root layout: two side-by-side panels inside slots_frame
        root = ctk.CTkFrame(self.slots_frame, fg_color="transparent")
        root.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=1)

        left_panel = ctk.CTkFrame(root, corner_radius=8)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        left_panel.grid_columnconfigure(0, weight=1)

        right_panel = ctk.CTkFrame(root, corner_radius=8)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
        right_panel.grid_columnconfigure(0, weight=1)

        # Left header: time ranges
        left_header = ctk.CTkLabel(left_panel, text="Time ranges", font=("Segoe UI", 11, "bold"), anchor="w")
        left_header.grid(row=0, column=0, padx=10, pady=(8, 4), sticky="w")

        if not slots:
            ctk.CTkLabel(
                left_panel,
                text="No configured time slots for this day.",
                font=("Segoe UI", 11),
                anchor="w",
            ).grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")
        else:
            for idx, (start_t, end_t, max_appt, slot_len) in enumerate(slots, start=1):
                row_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
                row_frame.grid(row=idx, column=0, sticky="ew", padx=10, pady=2)
                row_frame.grid_columnconfigure(0, weight=1)

                time_range_text = f"{start_t} - {end_t}"
                ctk.CTkLabel(row_frame, text=time_range_text).grid(row=0, column=0, sticky="w")

        # Right header: booked appointments
        right_header = ctk.CTkLabel(right_panel, text="Booked appointments", font=("Segoe UI", 11, "bold"), anchor="w")
        right_header.grid(row=0, column=0, padx=10, pady=(8, 4), sticky="w")

        if not bookings:
            ctk.CTkLabel(
                right_panel,
                text="No appointments booked for this day.",
                font=("Segoe UI", 11),
                anchor="w",
            ).grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")
        else:
            from datetime import datetime as _dt, timedelta as _td

            for idx, (patient_name, schedule_str) in enumerate(bookings, start=1):
                try:
                    start_dt = _dt.strptime(schedule_str, "%Y-%m-%d %H:%M")
                    end_dt = start_dt + _td(hours=2)
                    time_label = f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}"
                except Exception:
                    time_label = schedule_str

                text = f"{idx}. {time_label} · {patient_name}" if patient_name else f"{idx}. {time_label}"

                item = ctk.CTkLabel(
                    right_panel,
                    text=text,
                    anchor="w",
                    justify="left",
                )
                item.grid(row=idx, column=0, padx=10, pady=2, sticky="w")

