import customtkinter as ctk
import sqlite3
import calendar
from datetime import date
from tkinter import messagebox

from database import DB_NAME


class DoctorManagePage(ctk.CTkFrame):
    def __init__(self, master, doctor_id, doctor_name: str):
        super().__init__(master, corner_radius=0)

        self.doctor_id = doctor_id
        self.doctor_name = doctor_name

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text=f"Manage Availability - {self.doctor_name}",
            font=("Segoe UI", 24, "bold"),
        )
        title.grid(row=0, column=0, padx=30, pady=(10, 4), sticky="w")

        content = ctk.CTkFrame(self, corner_radius=10)
        content.grid(row=1, column=0, padx=30, pady=(0, 24), sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        # Month controls
        controls = ctk.CTkFrame(content, fg_color="transparent")
        controls.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")
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
        # Tighter vertical padding so calendar has more room above day details
        self.calendar_frame.grid(row=1, column=0, padx=10, pady=(8, 4), sticky="nsew")
        for col in range(7):
            self.calendar_frame.grid_columnconfigure(col, weight=1)

        # Day detail (very compact so calendar stays fully visible)
        self.day_detail_frame = ctk.CTkFrame(content, corner_radius=10)
        self.day_detail_frame.grid(row=2, column=0, padx=10, pady=(2, 8), sticky="ew")
        self.day_detail_frame.grid_columnconfigure(0, weight=1)

        self.selected_date = None

        self._refresh_calendar()

    def _edit_slot(self, slot_id: int, start_t: str, end_t: str, slot_len: int | None, max_appt: int | None):
        """Open a small window to edit an existing time slot, including slot count."""
        if self.selected_date is None or self.doctor_id is None:
            return

        root = self.winfo_toplevel()
        win = ctk.CTkToplevel(root)
        win.title("Edit Time Slot")

        width, height = 560, 260
        win.geometry(f"{width}x{height}")

        # Center relative to main window
        root.update_idletasks()
        master_x = root.winfo_rootx()
        master_y = root.winfo_rooty()
        master_w = root.winfo_width()
        master_h = root.winfo_height()
        x = master_x + (master_w - width) // 2
        y = master_y + (master_h - height) // 2
        win.geometry(f"{width}x{height}+{x}+{y}")

        win.transient(root)
        win.grab_set()
        win.lift()
        win.focus_force()

        win.grid_columnconfigure(1, weight=1)

        hours = [f"{h:02d}" for h in range(1, 13)]
        minutes = ["00", "30"]
        periods = ["AM", "PM"]

        def _from_24h(t: str):
            try:
                h, m = map(int, t.split(":"))
            except Exception:
                return "09", "00", "AM"
            period = "AM"
            if h == 0:
                h12 = 12
            elif h == 12:
                h12 = 12
                period = "PM"
            elif h > 12:
                h12 = h - 12
                period = "PM"
            else:
                h12 = h
            return f"{h12:02d}", f"{m:02d}", period

        s_h, s_m, s_p = _from_24h(start_t)
        e_h, e_m, e_p = _from_24h(end_t)

        # How many appointments are already booked in this time range
        booked_count = 0
        try:
            conn = self._connect()
            cur = conn.cursor()
            start_dt_str = f"{self.selected_date} {start_t}"
            end_dt_str = f"{self.selected_date} {end_t}"
            cur.execute(
                """
                SELECT COUNT(*) FROM appointments
                WHERE doctor_name = ? AND schedule >= ? AND schedule < ?
                """,
                (self.doctor_name, start_dt_str, end_dt_str),
            )
            booked_count = cur.fetchone()[0]
            conn.close()
        except Exception:
            booked_count = 0

        ctk.CTkLabel(win, text="Start time").grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        start_frame = ctk.CTkFrame(win, fg_color="transparent")
        start_frame.grid(row=0, column=1, padx=20, pady=(20, 5), sticky="w")
        start_frame.grid_columnconfigure((0, 1, 2), weight=0)

        start_hour_combo = ctk.CTkComboBox(start_frame, values=hours, width=80)
        start_hour_combo.set(s_h)
        start_hour_combo.grid(row=0, column=0, padx=(0, 5), sticky="w")

        start_min_combo = ctk.CTkComboBox(start_frame, values=minutes, width=80)
        start_min_combo.set(s_m)
        start_min_combo.grid(row=0, column=1, padx=5, sticky="w")

        start_period_combo = ctk.CTkComboBox(start_frame, values=periods, width=80)
        start_period_combo.set(s_p)
        start_period_combo.grid(row=0, column=2, padx=(5, 0), sticky="w")

        ctk.CTkLabel(win, text="End time").grid(row=1, column=0, padx=20, pady=5, sticky="w")
        end_frame = ctk.CTkFrame(win, fg_color="transparent")
        end_frame.grid(row=1, column=1, padx=20, pady=5, sticky="w")
        end_frame.grid_columnconfigure((0, 1, 2), weight=0)

        end_hour_combo = ctk.CTkComboBox(end_frame, values=hours, width=80)
        end_hour_combo.set(e_h)
        end_hour_combo.grid(row=0, column=0, padx=(0, 5), sticky="w")

        end_min_combo = ctk.CTkComboBox(end_frame, values=minutes, width=80)
        end_min_combo.set(e_m)
        end_min_combo.grid(row=0, column=1, padx=5, sticky="w")

        end_period_combo = ctk.CTkComboBox(end_frame, values=periods, width=80)
        end_period_combo.set(e_p)
        end_period_combo.grid(row=0, column=2, padx=(5, 0), sticky="w")

        ctk.CTkLabel(win, text="Slot length (minutes)").grid(row=2, column=0, padx=20, pady=5, sticky="w")
        slot_len_entry = ctk.CTkEntry(win)
        slot_len_entry.insert(0, str(slot_len or 30))
        slot_len_entry.grid(row=2, column=1, padx=20, pady=5, sticky="ew")

        # Slot count for this time range
        ctk.CTkLabel(win, text="Slot:").grid(row=3, column=0, padx=20, pady=(5, 0), sticky="w")
        slot_count_entry = ctk.CTkEntry(win)
        slot_count_entry.insert(0, "1" if max_appt is None else str(max_appt))
        slot_count_entry.grid(row=3, column=1, padx=20, pady=(5, 2), sticky="ew")

        # Indicator: how many appointments already booked in this time range
        booked_label = ctk.CTkLabel(
            win,
            text=f"Booked in this time range: {booked_count}",
            anchor="w",
        )
        booked_label.grid(row=4, column=0, columnspan=2, padx=20, pady=(0, 8), sticky="w")

        def _to_24h(hour_str: str, minute_str: str, period: str) -> str:
            try:
                h = int(hour_str)
                m = int(minute_str)
            except ValueError:
                return ""

            if period == "AM":
                if h == 12:
                    h = 0
            else:  # PM
                if h != 12:
                    h += 12

            return f"{h:02d}:{m:02d}"

        def save_changes():
            new_start = _to_24h(start_hour_combo.get(), start_min_combo.get(), start_period_combo.get())
            new_end = _to_24h(end_hour_combo.get(), end_min_combo.get(), end_period_combo.get())
            slot_len_str = slot_len_entry.get().strip()
            slot_count_str = slot_count_entry.get().strip()

            if not new_start or not new_end:
                win.destroy()
                return

            # Validate numbers
            if not slot_len_str.isdigit() or int(slot_len_str) <= 0:
                messagebox.showerror("Slot length", "Slot length must be a positive number of minutes.")
                return
            slot_len_val = int(slot_len_str)

            if not slot_count_str.isdigit() or int(slot_count_str) <= 0:
                messagebox.showerror("Slots", "Slot count must be a positive whole number.")
                return
            requested_slots = int(slot_count_str)

            # Do not allow decreasing slots: doctor can only increase or keep the same
            if max_appt is not None and requested_slots < max_appt:
                messagebox.showerror(
                    "Slots",
                    f"You currently have {max_appt} slots. You can only increase this number, not decrease it.",
                )
                return

            # Check that the requested slots fit in the time range
            from datetime import datetime as _dt

            try:
                start_dt = _dt.strptime(f"{self.selected_date} {new_start}", "%Y-%m-%d %H:%M")
                end_dt = _dt.strptime(f"{self.selected_date} {new_end}", "%Y-%m-%d %H:%M")
            except ValueError:
                messagebox.showerror("Time", "Invalid start or end time.")
                return

            total_minutes = max(0, int((end_dt - start_dt).total_seconds() // 60))
            if total_minutes <= 0:
                messagebox.showerror("Time", "End time must be after start time.")
                return

            max_slots_possible = total_minutes // slot_len_val
            if max_slots_possible <= 0:
                messagebox.showerror(
                    "Slots",
                    "Time range is too short for even 1 slot with the chosen duration.",
                )
                return

            if requested_slots > max_slots_possible:
                messagebox.showerror(
                    "Slots",
                    f"Not enough time for {requested_slots} slots. Maximum possible is {max_slots_possible}",
                )
                return

            conn = self._connect()
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE doctor_availability
                SET start_time = ?, end_time = ?, slot_length_minutes = ?, max_appointments = ?
                WHERE id = ?
                """,
                (new_start, new_end, slot_len_val, requested_slots, slot_id),
            )
            conn.commit()
            conn.close()

            win.destroy()
            self._load_day_data(self.selected_date)
            self._refresh_calendar()

        save_btn = ctk.CTkButton(win, text="Save", command=save_changes)
        save_btn.grid(row=5, column=0, columnspan=2, pady=(16, 20))

    def _connect(self):
        return sqlite3.connect(DB_NAME)

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

        availability_map = {}
        if self.doctor_id is not None:
            conn = self._connect()
            cur = conn.cursor()
            month_start = f"{self.current_year:04d}-{self.current_month:02d}-01"
            month_end = f"{self.current_year:04d}-{self.current_month:02d}-31"
            cur.execute(
                """
                SELECT date, is_available
                FROM doctor_availability
                WHERE doctor_id = ? AND date BETWEEN ? AND ?
                GROUP BY date
                """,
                (self.doctor_id, month_start, month_end),
            )
            for d_str, is_avail in cur.fetchall():
                availability_map[d_str] = is_avail
            conn.close()

        cal = calendar.Calendar(firstweekday=0)
        today_str = date.today().strftime("%Y-%m-%d")
        row = 1
        for week in cal.monthdayscalendar(self.current_year, self.current_month):
            for col, day_num in enumerate(week):
                if day_num == 0:
                    continue
                d_str = f"{self.current_year:04d}-{self.current_month:02d}-{day_num:02d}"
                status = availability_map.get(d_str)

                # Dates in the past are gray and not clickable
                if d_str < today_str:
                    fg = "#555555"
                    cmd = None
                else:
                    # By default, all days are considered available (green).
                    # Only days explicitly marked with is_available = 0 are shown as not available (red).
                    if status == 0:
                        fg = "#c0392b"  # not available
                    else:
                        fg = "#1c9b3b"  # available
                    cmd = lambda d=d_str: self._open_day_detail(d)

                btn = ctk.CTkButton(
                    self.calendar_frame,
                    text=str(day_num),
                    width=40,
                    height=28,
                    fg_color=fg,
                    state=("disabled" if cmd is None else "normal"),
                    command=cmd,
                )
                btn.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
            row += 1

        self._render_day_detail(None)

    def _open_day_detail(self, d_str: str):
        self.selected_date = d_str
        self._render_day_detail(d_str)

    def _render_day_detail(self, d_str: str):
        for child in self.day_detail_frame.winfo_children():
            child.destroy()

        if d_str is None:
            info = ctk.CTkLabel(
                self.day_detail_frame,
                text="Select a day to manage availability.",
            )
            info.grid(row=0, column=0, padx=10, pady=10, sticky="w")
            return

        header = ctk.CTkLabel(
            self.day_detail_frame,
            text=f"Date: {d_str}",
            font=("Segoe UI", 14, "bold"),
        )
        header.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        controls = ctk.CTkFrame(self.day_detail_frame, fg_color="transparent")
        controls.grid(row=1, column=0, padx=10, pady=(0, 2), sticky="ew")
        controls.grid_columnconfigure(0, weight=0)
        controls.grid_columnconfigure(1, weight=1)

        self.day_status_switch = ctk.CTkSwitch(
            controls,
            text="Day available",
            command=self._toggle_day_status,
        )
        self.day_status_switch.grid(row=0, column=0, padx=(0, 8), pady=0)

        add_slot_btn = ctk.CTkButton(
            controls,
            text="+ Add Time Slot",
            command=self._open_add_slot,
        )
        add_slot_btn.grid(row=0, column=1, padx=(0, 0), pady=5, sticky="e")

        # Fixed-height scrollable frame so it doesn't grow too tall
        self.slots_frame = ctk.CTkScrollableFrame(self.day_detail_frame, corner_radius=10, height=90)
        self.slots_frame.grid(row=2, column=0, padx=10, pady=(2, 6), sticky="nsew")
        self.slots_frame.grid_columnconfigure(0, weight=1)

        self._load_day_data(d_str)

    def _load_day_data(self, d_str: str):
        if self.doctor_id is None:
            return

        conn = self._connect()
        cur = conn.cursor()

        cur.execute(
            "SELECT is_available FROM doctor_availability WHERE doctor_id = ? AND date = ? GROUP BY date",
            (self.doctor_id, d_str),
        )
        row = cur.fetchone()
        is_available = 1 if row is None else row[0]
        self.day_status_switch.select() if is_available == 1 else self.day_status_switch.deselect()

        cur.execute(
            """
            SELECT id, start_time, end_time, max_appointments, slot_length_minutes
            FROM doctor_availability
            WHERE doctor_id = ? AND date = ? AND is_available = 1 AND start_time IS NOT NULL
            ORDER BY start_time
            """,
            (self.doctor_id, d_str),
        )
        slots = cur.fetchall()

        for child in self.slots_frame.winfo_children():
            child.destroy()

        for idx, (sid, start_t, end_t, max_appt, slot_len) in enumerate(slots):
            row_frame = ctk.CTkFrame(self.slots_frame, fg_color="transparent")
            row_frame.grid(row=idx, column=0, sticky="ew", pady=2)
            row_frame.grid_columnconfigure(0, weight=1)

            info_text = f"{start_t} - {end_t}"
            if slot_len:
                info_text += f"  ({slot_len} min)"
            if max_appt is not None:
                # Compute how many appointments already booked within this time range
                start_dt_str = f"{d_str} {start_t}"
                end_dt_str = f"{d_str} {end_t}"
                cur.execute(
                    """
                    SELECT COUNT(*) FROM appointments
                    WHERE doctor_name = ? AND schedule >= ? AND schedule < ?
                    """,
                    (self.doctor_name, start_dt_str, end_dt_str),
                )
                used = cur.fetchone()[0]
                remaining = max(0, (max_appt or 0) - used)

                label = "slot" if remaining == 1 else "slots"
                info_text += f"  {remaining} {label}"

            lbl = ctk.CTkLabel(row_frame, text=info_text, anchor="w")
            lbl.grid(row=0, column=0, sticky="ew")

            # Edit existing slot
            edit_btn = ctk.CTkButton(
                row_frame,
                text="Edit",
                width=60,
                command=lambda sid=sid, st=start_t, et=end_t, sl=slot_len, ma=max_appt: self._edit_slot(
                    sid, st, et, sl, ma
                ),
            )
            edit_btn.grid(row=0, column=1, padx=(5, 0))

        conn.close()

    def _toggle_day_status(self):
        if self.selected_date is None or self.doctor_id is None:
            return

        is_available = 1 if self.day_status_switch.get() else 0

        conn = self._connect()
        cur = conn.cursor()

        cur.execute(
            "DELETE FROM doctor_availability WHERE doctor_id = ? AND date = ? AND start_time IS NULL",
            (self.doctor_id, self.selected_date),
        )
        cur.execute(
            "INSERT INTO doctor_availability (doctor_id, date, is_available) VALUES (?, ?, ?)",
            (self.doctor_id, self.selected_date, is_available),
        )
        conn.commit()
        conn.close()

        self._refresh_calendar()

    def _open_add_slot(self):
        if self.selected_date is None or self.doctor_id is None:
            return

        root = self.winfo_toplevel()
        win = ctk.CTkToplevel(root)
        win.title("Add Time Slot")

        # Desired size (a bit wider so AM/PM selectors are not cropped)
        width, height = 560, 280
        win.geometry(f"{width}x{height}")

        # Center relative to main window
        root.update_idletasks()
        master_x = root.winfo_rootx()
        master_y = root.winfo_rooty()
        master_w = root.winfo_width()
        master_h = root.winfo_height()
        x = master_x + (master_w - width) // 2
        y = master_y + (master_h - height) // 2
        win.geometry(f"{width}x{height}+{x}+{y}")

        # Keep on top of main window
        win.transient(root)
        win.grab_set()
        win.lift()
        win.focus_force()

        win.grid_columnconfigure(1, weight=1)

        hours = [f"{h:02d}" for h in range(1, 13)]
        minutes = ["00", "30"]
        periods = ["AM", "PM"]

        ctk.CTkLabel(win, text="Start time").grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        start_frame = ctk.CTkFrame(win, fg_color="transparent")
        start_frame.grid(row=0, column=1, padx=20, pady=(20, 5), sticky="w")
        start_frame.grid_columnconfigure((0, 1, 2), weight=0)

        start_hour_combo = ctk.CTkComboBox(start_frame, values=hours, width=80)
        start_hour_combo.set("09")
        start_hour_combo.grid(row=0, column=0, padx=(0, 5), sticky="w")

        start_min_combo = ctk.CTkComboBox(start_frame, values=minutes, width=80)
        start_min_combo.set("00")
        start_min_combo.grid(row=0, column=1, padx=5, sticky="w")

        start_period_combo = ctk.CTkComboBox(start_frame, values=periods, width=80)
        start_period_combo.set("AM")
        start_period_combo.grid(row=0, column=2, padx=(5, 0), sticky="w")

        ctk.CTkLabel(win, text="End time").grid(row=1, column=0, padx=20, pady=5, sticky="w")
        end_frame = ctk.CTkFrame(win, fg_color="transparent")
        end_frame.grid(row=1, column=1, padx=20, pady=5, sticky="w")
        end_frame.grid_columnconfigure((0, 1, 2), weight=0)

        end_hour_combo = ctk.CTkComboBox(end_frame, values=hours, width=80)
        end_hour_combo.set("05")
        end_hour_combo.grid(row=0, column=0, padx=(0, 5), sticky="w")

        end_min_combo = ctk.CTkComboBox(end_frame, values=minutes, width=80)
        end_min_combo.set("00")
        end_min_combo.grid(row=0, column=1, padx=5, sticky="w")

        end_period_combo = ctk.CTkComboBox(end_frame, values=periods, width=80)
        end_period_combo.set("PM")
        end_period_combo.grid(row=0, column=2, padx=(5, 0), sticky="w")

        ctk.CTkLabel(win, text="Slot length (minutes)").grid(row=2, column=0, padx=20, pady=5, sticky="w")
        slot_len_entry = ctk.CTkEntry(win)
        slot_len_entry.insert(0, "30")
        slot_len_entry.grid(row=2, column=1, padx=20, pady=5, sticky="ew")

        # Slot count entered by doctor (intended number of 30-min appointments for this range)
        ctk.CTkLabel(win, text="Slot:").grid(row=3, column=0, padx=20, pady=(5, 0), sticky="w")
        max_appt_entry = ctk.CTkEntry(win)
        max_appt_entry.insert(0, "1")
        max_appt_entry.grid(row=3, column=1, padx=20, pady=(5, 8), sticky="ew")

        def _to_24h(hour_str: str, minute_str: str, period: str) -> str:
            try:
                h = int(hour_str)
                m = int(minute_str)
            except ValueError:
                return ""

            if period == "AM":
                if h == 12:
                    h = 0
            else:  # PM
                if h != 12:
                    h += 12

            return f"{h:02d}:{m:02d}"

        def save_slot():
            start_t = _to_24h(
                start_hour_combo.get(), start_min_combo.get(), start_period_combo.get()
            )
            end_t = _to_24h(
                end_hour_combo.get(), end_min_combo.get(), end_period_combo.get()
            )
            slot_len = slot_len_entry.get().strip()
            slot_count_str = max_appt_entry.get().strip()

            if not start_t or not end_t:
                win.destroy()
                return

            # Basic validation for inputs
            if not slot_len.isdigit() or int(slot_len) <= 0:
                messagebox.showerror("Slot length", "Slot length must be a positive number of minutes.")
                return
            slot_len_val = int(slot_len)

            if not slot_count_str.isdigit() or int(slot_count_str) <= 0:
                messagebox.showerror("Slots", "Slot count must be a positive whole number.")
                return
            requested_slots = int(slot_count_str)

            # Compute how many slots actually fit in the selected time range
            from datetime import datetime as _dt

            try:
                start_dt = _dt.strptime(f"{self.selected_date} {start_t}", "%Y-%m-%d %H:%M")
                end_dt = _dt.strptime(f"{self.selected_date} {end_t}", "%Y-%m-%d %H:%M")
            except ValueError:
                messagebox.showerror("Time", "Invalid start or end time.")
                return

            total_minutes = max(0, int((end_dt - start_dt).total_seconds() // 60))
            if total_minutes <= 0:
                messagebox.showerror("Time", "End time must be after start time.")
                return

            max_slots_possible = total_minutes // slot_len_val
            if max_slots_possible <= 0:
                messagebox.showerror(
                    "Slots",
                    "Time range is too short for even 1 slot with the chosen duration.",
                )
                return

            if requested_slots > max_slots_possible:
                messagebox.showerror(
                    "Slots",
                    f"Not enough time for {requested_slots} slots. Maximum possible is {max_slots_possible}",
                )
                return

            # Store the requested Slot count as the max total appointments for this time range
            max_appt_val = requested_slots

            conn = self._connect()
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO doctor_availability
                (doctor_id, date, start_time, end_time, is_available, max_appointments, slot_length_minutes)
                VALUES (?, ?, ?, ?, 1, ?, ?)
                """,
                (self.doctor_id, self.selected_date, start_t, end_t, max_appt_val, slot_len_val),
            )
            conn.commit()
            conn.close()

            win.destroy()
            self._load_day_data(self.selected_date)
            self._refresh_calendar()

        save_btn = ctk.CTkButton(win, text="Save", command=save_slot)
        save_btn.grid(row=4, column=0, columnspan=2, pady=(16, 20))

    def _delete_slot(self, slot_id: int):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM doctor_availability WHERE id = ?", (slot_id,))
        conn.commit()
        conn.close()

        if self.selected_date:
            self._load_day_data(self.selected_date)
            self._refresh_calendar()
