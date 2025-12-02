import customtkinter as ctk
import sqlite3
import calendar
from datetime import datetime, timedelta, date
from uuid import uuid4
import os

from tkinter import messagebox

from database import DB_NAME, log_activity


class ReceptionistAppointmentPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0)

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Appointment",
            font=("Segoe UI", 24, "bold"),
        )
        title.grid(row=0, column=0, padx=30, pady=(10, 4), sticky="w")

        form = ctk.CTkScrollableFrame(self, corner_radius=10)
        form.grid(row=1, column=0, padx=30, pady=(0, 30), sticky="nsew")
        form.grid_columnconfigure(1, weight=1)
        # Only the slots area should take extra vertical space so the notes field isn't cropped
        form.grid_rowconfigure(11, weight=1)  # slots area grows, pushes actions row to bottom

        # Patient details section (now first)
        ctk.CTkLabel(form, text="Patient details", font=("Segoe UI", 15, "bold")).grid(
            row=0, column=0, columnspan=2, padx=20, pady=(16, 8), sticky="w"
        )

        # Full name
        ctk.CTkLabel(form, text="Full name").grid(row=1, column=0, padx=20, pady=4, sticky="w")
        self.patient_entry = ctk.CTkEntry(form)
        self.patient_entry.grid(row=1, column=1, padx=20, pady=4, sticky="ew")

        # Contact number (digits only)
        ctk.CTkLabel(form, text="Contact no.").grid(row=2, column=0, padx=20, pady=4, sticky="w")
        self.contact_entry = ctk.CTkEntry(form)
        self.contact_entry.grid(row=2, column=1, padx=20, pady=4, sticky="ew")

        # Limit contact entry to digits only
        vcmd = self.register(self._validate_contact_digits)
        try:
            self.contact_entry.configure(validate="key", validatecommand=(vcmd, "%P"))
        except Exception:
            pass

        # Address
        ctk.CTkLabel(form, text="Address").grid(row=3, column=0, padx=20, pady=4, sticky="w")
        self.address_entry = ctk.CTkEntry(form)
        self.address_entry.grid(row=3, column=1, padx=20, pady=4, sticky="ew")

        # Appointment about
        ctk.CTkLabel(form, text="Appointment about").grid(row=4, column=0, padx=20, pady=4, sticky="w")
        services = [
            "General Consultation - 400 PHP",
            "Pediatrics Consultation - 450 PHP",
            "Internal Medicine - 500 PHP",
            "Cardiology Consultation - 800 PHP",
            "OB-GYN Consultation - 700 PHP",
            "Dermatology Consultation - 600 PHP",
            "ENT Consultation - 550 PHP",
            "Orthopedic Consultation - 750 PHP",
            "Ophthalmology Consultation - 500 PHP",
            "Dental Consultation - 350 PHP",
            "CBC (Complete Blood Count) - 250 PHP",
            "Urinalysis - 150 PHP",
            "Stool Examination - 150 PHP",
            "Fasting Blood Sugar (FBS) - 200 PHP",
            "HbA1c - 800 PHP",
            "Lipid Profile - 700 PHP",
            "Creatinine Test - 300 PHP",
            "BUN (Blood Urea Nitrogen) - 250 PHP",
            "Liver Function Test (LFT) - 500 PHP",
            "TSH / Thyroid Test - 700 PHP",
            "Chest X-Ray (PA View) - 650 PHP",
            "Lumbar X-Ray - 800 PHP",
            "Ultrasound – Whole Abdomen - 1000 PHP",
            "Ultrasound – Pelvic / OB - 900 PHP",
            "Ultrasound – Thyroid - 800 PHP",
            "2D Echo - 2500 PHP",
            "ECG - 600 PHP",
            "CT Scan (Plain) - 6000 PHP",
            "MRI (Plain) - 10000 PHP",
            "Mammogram - 2000 PHP",
            "Wound Dressing - 300 PHP",
            "Nebulization - 200 PHP",
            "Injection Service - 200 PHP",
            "Suturing (small wound) - 1000 PHP",
            "Ear Cleaning - 400 PHP",
            "Incision and Drainage - 800 PHP",
            "ECG with Interpretation - 800 PHP",
            "Cast / Splint Application - 1000 PHP",
            "Pap Smear - 500 PHP",
            "Pregnancy Test (Urine) - 200 PHP",
            "Medical Certificate - 250 PHP",
            "Vital Signs Check - 100 PHP",
            "ECG Print Request - 150 PHP",
            "X-Ray CD Copy - 150 PHP",
            "Laboratory Results Printing - 100 PHP",
            "Doctor Follow-Up Consultation - 300 PHP",
            "Teleconsultation - 400 PHP",
            "Nutritional Counseling - 500 PHP",
            "Family Planning Consultation - 400 PHP",
            "Vaccination Service (Service Fee) - 400 PHP",
        ]
        self._about_services = services

        about_row = ctk.CTkFrame(form, fg_color="transparent")
        about_row.grid(row=4, column=1, padx=20, pady=4, sticky="ew")
        about_row.grid_columnconfigure(0, weight=1)

        # 'Appointment about' is filled via Select button only (read-only to typing)
        self.about_entry = ctk.CTkEntry(about_row, state="readonly")
        self.about_entry.grid(row=0, column=0, padx=(0, 6), pady=0, sticky="ew")

        select_service_btn = ctk.CTkButton(
            about_row,
            text="Select",
            width=70,
            command=self._open_service_picker,
        )
        select_service_btn.grid(row=0, column=1, padx=(0, 0), pady=0)

        # Notes / reason
        ctk.CTkLabel(form, text="Reason / notes").grid(row=5, column=0, padx=20, pady=4, sticky="nw")
        self.notes_entry = ctk.CTkTextbox(form, height=80)
        self.notes_entry.grid(row=5, column=1, padx=20, pady=4, sticky="nsew")

        # Appointment details section
        ctk.CTkLabel(form, text="Appointment details", font=("Segoe UI", 15, "bold")).grid(
            row=6, column=0, columnspan=2, padx=20, pady=(16, 8), sticky="w"
        )

        # Doctor
        ctk.CTkLabel(form, text="Doctor").grid(row=7, column=0, padx=20, pady=4, sticky="w")
        doctor_row = ctk.CTkFrame(form, fg_color="transparent")
        doctor_row.grid(row=7, column=1, padx=20, pady=4, sticky="ew")
        doctor_row.grid_columnconfigure(0, weight=1)

        self.doctor_combo = ctk.CTkComboBox(
            doctor_row,
            values=[],
            state="readonly",
            command=lambda _value: self._load_dates(),
        )
        self.doctor_combo.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        clear_doc_btn = ctk.CTkButton(
            doctor_row,
            text="✖",
            width=28,
            command=self._clear_doctor,
        )
        clear_doc_btn.grid(row=0, column=1, padx=(0, 0), sticky="e")

        ctk.CTkLabel(form, text="Date").grid(row=8, column=0, padx=20, pady=4, sticky="w")
        date_row = ctk.CTkFrame(form, fg_color="transparent")
        date_row.grid(row=8, column=1, padx=20, pady=4, sticky="ew")
        date_row.grid_columnconfigure(0, weight=1)
        date_row.grid_columnconfigure(1, weight=0)

        months = [f"{m:02d}" for m in range(1, 13)]
        days = [f"{d:02d}" for d in range(1, 32)]
        current_year = date.today().year
        years = [str(current_year + offset) for offset in range(0, 3)]

        # Keep month/day/year combos for internal logic and clamping,
        # but hide them from the modern receptionist UI.
        self.date_month_combo = ctk.CTkComboBox(date_row, values=months, width=70, state="readonly")
        self.date_day_combo = ctk.CTkComboBox(date_row, values=days, width=70, state="readonly")
        self.date_year_combo = ctk.CTkComboBox(date_row, values=years, width=70, state="readonly")

        self.date_entry = ctk.CTkEntry(date_row)
        self.date_entry.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        # Inline calendar (like Schedule tab) lives directly in the appointment page;
        # we keep the popup date-picker button hidden / unused.
        self._date_picker_button = ctk.CTkButton(
            date_row,
            text="\ud83d\udcc5",
            width=32,
            command=self._open_date_picker,
        )
        self._date_picker_button.grid_remove()

        # Inline calendar header + grid (full-width like Schedule tab)
        cal_container = ctk.CTkFrame(form, fg_color="transparent")
        cal_container.grid(row=9, column=0, columnspan=2, padx=20, pady=(0, 4), sticky="ew")
        cal_container.grid_columnconfigure(1, weight=1)

        self.appt_cal_prev_btn = ctk.CTkButton(cal_container, text="<", width=32, command=self._appt_prev_month)
        self.appt_cal_prev_btn.grid(row=0, column=0, padx=(0, 5), pady=(0, 2))

        self.appt_month_label = ctk.CTkLabel(cal_container, text="", font=("Segoe UI", 14, "bold"))
        self.appt_month_label.grid(row=0, column=1, sticky="w")

        self.appt_cal_next_btn = ctk.CTkButton(cal_container, text=">", width=32, command=self._appt_next_month)
        self.appt_cal_next_btn.grid(row=0, column=2, padx=(5, 0), pady=(0, 2))

        self.appt_calendar_frame = ctk.CTkFrame(form, corner_radius=10)
        self.appt_calendar_frame.grid(row=10, column=0, columnspan=2, padx=20, pady=(0, 6), sticky="nsew")
        for col in range(7):
            self.appt_calendar_frame.grid_columnconfigure(col, weight=1)

        ctk.CTkLabel(form, text="Time").grid(row=11, column=0, padx=20, pady=4, sticky="w")
        time_row = ctk.CTkFrame(form, fg_color="transparent")
        time_row.grid(row=11, column=1, padx=20, pady=4, sticky="w")

        hours = [f"{h:02d}" for h in range(1, 13)]
        minutes = ["00", "15", "30", "45"]
        periods = ["AM", "PM"]

        self.time_hour_combo = ctk.CTkComboBox(time_row, values=hours, width=70, state="readonly")
        self.time_hour_combo.set("09")
        self.time_minute_combo = ctk.CTkComboBox(time_row, values=minutes, width=70, state="readonly")
        self.time_minute_combo.set("00")
        self.time_period_combo = ctk.CTkComboBox(time_row, values=periods, width=70, state="readonly")
        self.time_period_combo.set("AM")

        duration_label = ctk.CTkLabel(
            time_row,
            text="Select an available time slot below (Duration: 2 hours)",
            font=("Segoe UI", 11),
        )
        duration_label.grid(row=0, column=0, padx=(0, 0), sticky="w")

        # Hide legacy time combo boxes and the old Check button from the modern UI,
        # but keep the widgets around so existing logic that references them
        # continues to work safely.
        self.time_hour_combo.grid_remove()
        self.time_minute_combo.grid_remove()
        self.time_period_combo.grid_remove()

        # Action buttons row (right-aligned), placed at the bottom of the form.
        actions_row = ctk.CTkFrame(form, fg_color="transparent")
        actions_row.grid(row=12, column=0, columnspan=2, padx=20, pady=(8, 16), sticky="e")
        actions_row.grid_columnconfigure(0, weight=0)
        actions_row.grid_columnconfigure(1, weight=0)

        clear_btn = ctk.CTkButton(
            actions_row,
            text="CLEAR",
            fg_color="#dc2626",  # red
            hover_color="#b91c1c",
            command=self._clear_form,
        )
        clear_btn.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="e")

        save_btn = ctk.CTkButton(
            actions_row,
            text="Save appointment",
            fg_color="#16a34a",  # green
            hover_color="#15803d",
            command=self.save_appointment,
        )
        save_btn.grid(row=0, column=1, padx=(0, 0), pady=0, sticky="e")

        # Time is auto-assigned; keep an invisible frame so other logic can safely clear it,
        # but place it below the action buttons so it doesn't create extra visual space.
        dummy_container = ctk.CTkFrame(form, corner_radius=8, fg_color="transparent")
        dummy_container.grid(row=11, column=0, columnspan=2, padx=20, pady=0, sticky="nsew")
        dummy_container.grid_columnconfigure(0, weight=1)

        self.slots_frame = ctk.CTkFrame(dummy_container, corner_radius=8, fg_color="transparent")
        self.slots_frame.grid(row=0, column=0, padx=0, pady=(0, 4), sticky="nsew")

        self.slot_summary_label = ctk.CTkLabel(
            dummy_container,
            text="No time selected.",
            anchor="w",
        )
        self.slot_summary_label.grid(row=1, column=0, padx=(0, 0), pady=(2, 0), sticky="w")

        self.selected_schedule = None
        self._selected_slot_btn = None
        self.available_dates = []
        self.current_date_index = None

        self._date_picker_win = None
        self._date_picker_year = None
        self._date_picker_month = None

        today = date.today()
        self.date_month_combo.set(f"{today.month:02d}")
        self.date_day_combo.set(f"{today.day:02d}")
        self.date_year_combo.set(str(today.year))
        self._sync_date_entry_from_combos()

        # Inline appointment calendar starts at the current month
        self.appt_cal_year = today.year
        self.appt_cal_month = today.month
        self._refresh_appt_calendar()

        self.date_month_combo.configure(command=lambda _v: self._sync_date_entry_from_combos())
        self.date_day_combo.configure(command=lambda _v: self._sync_date_entry_from_combos())
        self.date_year_combo.configure(command=lambda _v: self._sync_date_entry_from_combos())

        self._load_doctors()

    def _open_service_picker(self):
        """Popup window with a scrollable list of services for the About field."""
        services = getattr(self, "_about_services", [])
        if not services:
            return

        master = self.winfo_toplevel()
        win = ctk.CTkToplevel(master)
        win.title("Select service")
        win.geometry("420x360")
        win.resizable(False, False)
        win.transient(master)
        win.grab_set()

        win.grid_rowconfigure(1, weight=1)
        win.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(win, text="Choose appointment service", font=("Segoe UI", 15, "bold"))
        title.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="w")

        list_frame = ctk.CTkScrollableFrame(win, corner_radius=10)
        list_frame.grid(row=1, column=0, padx=16, pady=(0, 12), sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)

        def _choose(value: str):
            # Temporarily enable entry to change text, then restore readonly
            try:
                self.about_entry.configure(state="normal")
            except Exception:
                pass
            self.about_entry.delete(0, "end")
            self.about_entry.insert(0, value)
            try:
                self.about_entry.configure(state="readonly")
            except Exception:
                pass
            win.destroy()

        for idx, svc in enumerate(services):
            btn = ctk.CTkButton(
                list_frame,
                text=svc,
                width=360,
                command=lambda v=svc: _choose(v),
            )
            btn.grid(row=idx, column=0, padx=4, pady=2, sticky="ew")

        # Center popup relative to main window
        win.update_idletasks()
        master.update_idletasks()
        mx = master.winfo_rootx()
        my = master.winfo_rooty()
        mw = master.winfo_width()
        mh = master.winfo_height()
        ww = win.winfo_width()
        wh = win.winfo_height()
        x = mx + (mw - ww) // 2
        y = my + (mh - wh) // 2
        win.geometry(f"{ww}x{wh}+{x}+{y}")

    def _validate_contact_digits(self, new_value: str) -> bool:
        """Allow only digits (or empty) in the contact number field."""
        if new_value == "":
            return True
        return new_value.isdigit()

    def _connect(self):
        return sqlite3.connect(DB_NAME)

    def _clear_doctor(self):
        """Clear selected doctor and reset dates/slots."""
        try:
            self.doctor_combo.set("")
        except Exception:
            pass

        self.available_dates = []
        self.current_date_index = None
        self.date_entry.delete(0, "end")

        # Clear slots UI
        for child in self.slots_frame.winfo_children():
            child.destroy()
        self.selected_schedule = None
        self._selected_slot_btn = None

    def _clear_form(self):
        """Clear all fields on the appointment form."""
        # Patient info
        self.patient_entry.delete(0, "end")
        self.contact_entry.delete(0, "end")
        self.address_entry.delete(0, "end")
        self.about_entry.delete(0, "end")
        self.notes_entry.delete("1.0", "end")

        # Doctor + date + slots
        try:
            self.doctor_combo.set("")
        except Exception:
            pass

        self.available_dates = []
        self.current_date_index = None
        self.date_entry.delete(0, "end")

        for child in self.slots_frame.winfo_children():
            child.destroy()
        self.selected_schedule = None
        self._selected_slot_btn = None
        if hasattr(self, "slot_summary_label"):
            self.slot_summary_label.configure(text="No time selected.")

        # Reset date combos back to today
        today = date.today()
        try:
            self.date_month_combo.set(f"{today.month:02d}")
            self.date_day_combo.set(f"{today.day:02d}")
            self.date_year_combo.set(str(today.year))
            self._sync_date_entry_from_combos()
        except Exception:
            pass

        # Reset inline calendar to today after clearing
        today = date.today()
        self.appt_cal_year = today.year
        self.appt_cal_month = today.month
        self._refresh_appt_calendar()

    # ------------------------------------------------------------------
    # Inline appointment calendar (Schedule-style grid embedded in page)
    # ------------------------------------------------------------------

    def _appt_prev_month(self):
        if not hasattr(self, "appt_cal_year"):
            return
        if self.appt_cal_month == 1:
            self.appt_cal_month = 12
            self.appt_cal_year -= 1
        else:
            self.appt_cal_month -= 1
        self._refresh_appt_calendar()

    def _appt_next_month(self):
        if not hasattr(self, "appt_cal_year"):
            return
        if self.appt_cal_month == 12:
            self.appt_cal_month = 1
            self.appt_cal_year += 1
        else:
            self.appt_cal_month += 1
        self._refresh_appt_calendar()

    def _refresh_appt_calendar(self):
        """Rebuild the inline appointment calendar grid using doctor availability.

        Mirrors the visual style of the receptionist Schedule tab but is focused on
        selecting a single appointment date and driving the time-slot buttons.
        """

        if not hasattr(self, "appt_calendar_frame"):
            return

        for child in self.appt_calendar_frame.winfo_children():
            child.destroy()

        year = getattr(self, "appt_cal_year", date.today().year)
        month = getattr(self, "appt_cal_month", date.today().month)

        # Month label like "November 2025"
        try:
            self.appt_month_label.configure(text=f"{calendar.month_name[month]} {year}")
        except Exception:
            pass

        # Weekday headers
        for i, wd in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            lbl = ctk.CTkLabel(self.appt_calendar_frame, text=wd, font=("Segoe UI", 12, "bold"))
            lbl.grid(row=0, column=i, pady=(0, 5))

        today_str = date.today().strftime("%Y-%m-%d")

        # Determine per-day availability for the selected doctor in this month.
        # not_available_days -> explicitly marked "not available" (red)
        selected_doctor = self.doctor_combo.get().strip()
        not_available_days = set()

        if selected_doctor and selected_doctor != "Add doctor first":
            conn = self._connect()
            cur = conn.cursor()
            cur.execute("SELECT id FROM doctors WHERE name = ? AND status = 'active'", (selected_doctor,))
            row = cur.fetchone()
            if row is not None:
                doctor_id = row[0]
                month_start = f"{year:04d}-{month:02d}-01"
                month_end = f"{year:04d}-{month:02d}-31"

                # Days explicitly set to not available (day-level flag)
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
        row = 1
        for week in cal.monthdayscalendar(year, month):
            for col, day_num in enumerate(week):
                if day_num == 0:
                    continue
                d_str = f"{year:04d}-{month:02d}-{day_num:02d}"

                if d_str < today_str:
                    # Past dates: gray, disabled
                    fg = "#555555"
                    hover = fg
                    state = "disabled"
                elif d_str in not_available_days:
                    # Explicitly not available: red, disabled
                    fg = "#c0392b"
                    hover = fg
                    state = "disabled"
                else:
                    # Match receptionist Schedule tab: all future days are considered
                    # available (green) unless the doctor explicitly marked them
                    # not available.
                    fg = "#1c9b3b"
                    hover = "#17a349"
                    state = "normal"

                def _pick(ds=d_str):
                    self.date_entry.delete(0, "end")
                    self.date_entry.insert(0, ds)
                    self.current_date_index = None
                    self._sync_combos_from_date_entry()

                btn = ctk.CTkButton(
                    self.appt_calendar_frame,
                    text=str(day_num),
                    width=40,
                    height=32,
                    fg_color=fg,
                    hover_color=hover,
                    state=state,
                    command=(None if state == "disabled" else _pick),
                )
                btn.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
            row += 1

    def _sync_date_entry_from_combos(self) -> None:
        """Update internal date_entry from month/day/year combos and reload slots."""

        month_str = getattr(self, "date_month_combo", None).get().strip() if hasattr(self, "date_month_combo") else ""
        day_str = getattr(self, "date_day_combo", None).get().strip() if hasattr(self, "date_day_combo") else ""
        year_str = getattr(self, "date_year_combo", None).get().strip() if hasattr(self, "date_year_combo") else ""

        if not month_str or not day_str or not year_str:
            return

        try:
            y = int(year_str)
            m = int(month_str)
            d = int(day_str)
        except ValueError:
            return

        # Clamp day to valid range for the month/year
        try:
            max_day = calendar.monthrange(y, m)[1]
        except Exception:
            return

        if d > max_day:
            d = max_day
            try:
                self.date_day_combo.set(f"{d:02d}")
            except Exception:
                pass

        try:
            new_date = date(y, m, d)
        except ValueError:
            return

        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, new_date.strftime("%Y-%m-%d"))
        self.current_date_index = None
        self._load_slots()

    def _sync_combos_from_date_entry(self) -> None:
        """Update month/day/year combos from the internal date_entry and reload slots."""

        if not hasattr(self, "date_month_combo") or not hasattr(self, "date_day_combo") or not hasattr(self, "date_year_combo"):
            return

        date_str = self.date_entry.get().strip()
        if not date_str:
            return

        try:
            dt_val = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return

        month_str = f"{dt_val.month:02d}"
        day_str = f"{dt_val.day:02d}"
        year_str = str(dt_val.year)

        try:
            self.date_month_combo.set(month_str)
            self.date_day_combo.set(day_str)

            # Ensure year is present in year combo values
            values = list(self.date_year_combo.cget("values"))
            if year_str not in values:
                values.append(year_str)
                self.date_year_combo.configure(values=values)
            self.date_year_combo.set(year_str)
        except Exception:
            pass

        self._load_slots()

    def _load_doctors(self):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT name FROM doctors WHERE status = 'active' ORDER BY name")
        names = [row[0] for row in cur.fetchall()]
        conn.close()

        if names:
            # We have doctors: allow selection and load dates normally
            self.doctor_combo.configure(values=names, state="readonly")
            self.doctor_combo.set(names[0])
            self._load_dates()
        else:
            # No doctors yet: show message and disable selection
            self.doctor_combo.configure(values=["Add doctor first"], state="disabled")
            self.doctor_combo.set("Add doctor first")

            # Clear date and slots
            self.available_dates = []
            self.current_date_index = None
            self.date_entry.delete(0, "end")
            for child in self.slots_frame.winfo_children():
                child.destroy()
            if hasattr(self, "slot_summary_label"):
                self.slot_summary_label.configure(text="No time selected.")

    def _get_selected_doctor_id(self, cur):
        doctor = self.doctor_combo.get().strip()
        if not doctor or doctor == "Add doctor first":
            return None
        cur.execute("SELECT id FROM doctors WHERE name = ? AND status = 'active'", (doctor,))
        row = cur.fetchone()
        return row[0] if row else None

    def _load_dates(self):
        # Populate date combo with dates where the selected doctor has availability slots
        conn = self._connect()
        cur = conn.cursor()

        doctor_id = self._get_selected_doctor_id(cur)
        if doctor_id is None:
            conn.close()
            self.available_dates = []
            self.current_date_index = None
            self.date_entry.delete(0, "end")
            return

        today_str = date.today().strftime("%Y-%m-%d")
        cur.execute(
            """
            SELECT DISTINCT date FROM doctor_availability
            WHERE doctor_id = ?
              AND is_available = 1
              AND start_time IS NOT NULL
              AND date >= ?
            ORDER BY date
            """,
            (doctor_id, today_str),
        )
        dates = [row[0] for row in cur.fetchall()]
        conn.close()

        self.available_dates = dates
        if dates:
            self.current_date_index = 0
            self.date_entry.delete(0, "end")
            self.date_entry.insert(0, dates[0])
            self._sync_combos_from_date_entry()
        else:
            self.current_date_index = None
            self.date_entry.delete(0, "end")

        if not dates:
            self._load_slots()

        # Refresh the inline appointment calendar whenever the available
        # dates list changes (e.g., doctor selection or availability edits).
        try:
            self._refresh_appt_calendar()
        except Exception:
            pass

    def _open_date_picker(self):
        if self._date_picker_win is not None and self._date_picker_win.winfo_exists():
            return

        dates = self.available_dates or []
        if dates:
            first = datetime.strptime(dates[0], "%Y-%m-%d").date()
            year = first.year
            month = first.month
        else:
            today = datetime.today().date()
            year = today.year
            month = today.month

        self._date_picker_year = year
        self._date_picker_month = month

        win = ctk.CTkToplevel(self)
        self._date_picker_win = win
        win.title("Select date")
        win.geometry("320x340")
        win.resizable(False, False)

        # Match app icon (apply after CTk finishes its own setup)
        def _apply_icon():
            try:
                import os
                from tkinter import PhotoImage

                # images folder is at project root, one level above pages/
                project_root = os.path.dirname(os.path.dirname(__file__))
                ico_path = os.path.join(project_root, "images", "logo.ico")
                png_path = os.path.join(project_root, "images", "logo.png")
                if os.path.exists(ico_path):
                    win.iconbitmap(ico_path)
                elif os.path.exists(png_path):
                    win._icon_image = PhotoImage(file=png_path)
                    win.iconphoto(False, win._icon_image)
            except Exception:
                pass

        win.after(10, _apply_icon)
        win.transient(self)
        win.grab_set()

        win.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(win)
        header.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        prev_btn = ctk.CTkButton(header, text="<", width=28, command=self._picker_prev_month)
        prev_btn.grid(row=0, column=0, padx=(0, 4))

        self._picker_month_label = ctk.CTkLabel(header, text="")
        self._picker_month_label.grid(row=0, column=1, sticky="ew")

        next_btn = ctk.CTkButton(header, text=">", width=28, command=self._picker_next_month)
        next_btn.grid(row=0, column=2, padx=(4, 0))

        body = ctk.CTkFrame(win)
        body.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self._picker_body = body
        for col in range(7):
            body.grid_columnconfigure(col, weight=1)

        self._rebuild_date_picker()

        # Center popup inside the main window
        win.update_idletasks()
        master = self.winfo_toplevel()
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

    def _close_date_picker(self):
        if self._date_picker_win is not None and self._date_picker_win.winfo_exists():
            self._date_picker_win.destroy()
        self._date_picker_win = None

    def _picker_prev_month(self):
        if self._date_picker_year is None:
            return
        if self._date_picker_month == 1:
            self._date_picker_month = 12
            self._date_picker_year -= 1
        else:
            self._date_picker_month -= 1
        self._rebuild_date_picker()

    def _picker_next_month(self):
        if self._date_picker_year is None:
            return
        if self._date_picker_month == 12:
            self._date_picker_month = 1
            self._date_picker_year += 1
        else:
            self._date_picker_month += 1
        self._rebuild_date_picker()

    def _rebuild_date_picker(self):
        if self._picker_body is None or self._date_picker_year is None:
            return

        for child in self._picker_body.winfo_children():
            child.destroy()

        self._picker_month_label.configure(
            text=f"{calendar.month_name[self._date_picker_month]} {self._date_picker_year}"
        )

        today_str = date.today().strftime("%Y-%m-%d")

        # Normalized set of dates where this doctor actually has availability
        # (as pre-fetched by _load_dates) so only those are highlighted green.
        available_set = set(self.available_dates or [])

        for i, wd in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            lbl = ctk.CTkLabel(self._picker_body, text=wd)
            lbl.grid(row=0, column=i, pady=(0, 4))

        # Determine per-day availability for the selected doctor based on
        # doctor_availability day records (start_time IS NULL, is_available=0).
        selected_doctor = self.doctor_combo.get().strip()
        not_available_days = set()

        if selected_doctor:
            conn = self._connect()
            cur = conn.cursor()

            # Find doctor id
            cur.execute("SELECT id FROM doctors WHERE name = ? AND status = 'active'", (selected_doctor,))
            row = cur.fetchone()
            if row is not None:
                doctor_id = row[0]
                month_start = f"{self._date_picker_year:04d}-{self._date_picker_month:02d}-01"
                month_end = f"{self._date_picker_year:04d}-{self._date_picker_month:02d}-31"
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
        row = 1
        for week in cal.monthdayscalendar(self._date_picker_year, self._date_picker_month):
            for col, day_num in enumerate(week):
                if day_num == 0:
                    continue
                d_str = f"{self._date_picker_year:04d}-{self._date_picker_month:02d}-{day_num:02d}"

                if d_str < today_str:
                    # Past dates are gray and disabled
                    fg_color = "#555555"
                    hover_color = "#555555"
                    state = "disabled"
                elif d_str in not_available_days:
                    # Explicitly marked NOT AVAILABLE by the doctor -> red and disabled
                    fg_color = "#c0392b"
                    hover_color = "#c0392b"
                    state = "disabled"
                elif d_str in available_set:
                    # Doctor has defined availability on this date -> green and clickable
                    fg_color = "#1c9b3b"
                    hover_color = "#17a349"
                    state = "normal"
                else:
                    # Future day but no configured availability -> gray/disabled
                    fg_color = "#555555"
                    hover_color = "#555555"
                    state = "disabled"

                btn = ctk.CTkButton(
                    self._picker_body,
                    text=str(day_num),
                    width=34,
                    height=30,
                    fg_color=fg_color,
                    hover_color=hover_color,
                    state=state,
                    command=(None if state == "disabled" else lambda ds=d_str: self._on_date_picked(ds)),
                )
                btn.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
            row += 1

    def _on_date_picked(self, d_str: str):
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, d_str)
        self.current_date_index = None
        self._close_date_picker()
        self._sync_combos_from_date_entry()

    def _on_date_changed(self):
        # When the user edits the date manually, forget the index and reload slots.
        self.current_date_index = None
        self._sync_combos_from_date_entry()

    def _is_time_available_for_two_hours(self, doctor: str, date_str: str, time_24: str):
        """Check if a 2-hour appointment can be booked at the given time.

        Returns (True, "") if available; otherwise (False, reason_message).
        """

        if not doctor or not date_str or not time_24:
            return False, "Doctor, date, or time is missing."

        try:
            new_start_dt = datetime.strptime(f"{date_str} {time_24}", "%Y-%m-%d %H:%M")
        except ValueError:
            return False, "Selected date or time is invalid."

        # Fixed 2-hour duration
        new_end_dt = new_start_dt + timedelta(hours=2)

        # Do not allow booking in the past
        if new_start_dt < datetime.now():
            return False, "Cannot book an appointment in the past."

        conn = self._connect()
        cur = conn.cursor()

        # Confirm the doctor is active and get id
        cur.execute("SELECT id FROM doctors WHERE name = ? AND status = 'active'", (doctor,))
        row = cur.fetchone()
        if row is None:
            conn.close()
            return False, "Selected doctor is not active."
        doctor_id = row[0]

        # Ensure the day is not explicitly marked unavailable
        cur.execute(
            """
            SELECT is_available FROM doctor_availability
            WHERE doctor_id = ? AND date = ? AND start_time IS NULL
            ORDER BY id DESC LIMIT 1
            """,
            (doctor_id, date_str),
        )
        row = cur.fetchone()
        if row is not None and row[0] == 0:
            conn.close()
            return False, "Doctor is marked not available on this day."

        # Check the chosen start time fits completely inside at least one
        # availability range for that day.
        cur.execute(
            """
            SELECT start_time, end_time
            FROM doctor_availability
            WHERE doctor_id = ? AND date = ? AND is_available = 1 AND start_time IS NOT NULL
            ORDER BY start_time
            """,
            (doctor_id, date_str),
        )
        ranges = cur.fetchall()

        # If the doctor has no explicit availability ranges for this day but the
        # day is not marked unavailable, treat it as a default 09:0000 window
        # so that the receptionist can still honor the standard working hours.
        if not ranges:
            ranges = [("09:00", "17:00")]

        fits_in_range = False
        for start_t, end_t in ranges:
            try:
                range_start_dt = datetime.strptime(f"{date_str} {start_t}", "%Y-%m-%d %H:%M")
                range_end_dt = datetime.strptime(f"{date_str} {end_t}", "%Y-%m-%d %H:%M")
            except ValueError:
                continue

            # New appointment must start within the range and finish before it ends
            if new_start_dt >= range_start_dt and new_end_dt <= range_end_dt:
                fits_in_range = True
                break

        if not fits_in_range:
            conn.close()
            return False, "Doctor is not available for a full 2-hour slot at this time."

        # Check for overlapping appointments (also 2 hours each).
        cur.execute(
            "SELECT schedule FROM appointments WHERE doctor_name = ? AND schedule LIKE ?",
            (doctor, f"{date_str} %"),
        )
        rows = cur.fetchall()

        for (existing_schedule,) in rows:
            try:
                existing_start = datetime.strptime(existing_schedule, "%Y-%m-%d %H:%M")
            except ValueError:
                continue

            existing_end = existing_start + timedelta(hours=2)

            # Overlap condition: start < other_end and end > other_start
            if new_start_dt < existing_end and new_end_dt > existing_start:
                conn.close()
                return False, "This time overlaps with another appointment within its 1-hour window."

        conn.close()
        return True, ""

    def _set_date_from_index(self):
        if not self.available_dates or self.current_date_index is None:
            return
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, self.available_dates[self.current_date_index])
        self._sync_combos_from_date_entry()

    def _check_time_available(self):
        doctor = self.doctor_combo.get().strip()
        date_str = self.date_entry.get().strip()

        if not doctor or not date_str:
            messagebox.showwarning("Check time", "Select doctor and date first.")
            return

        hour_str = self.time_hour_combo.get().strip()
        minute_str = self.time_minute_combo.get().strip()
        period = self.time_period_combo.get().strip()

        try:
            h = int(hour_str)
            m = int(minute_str)
        except ValueError:
            messagebox.showwarning("Check time", "Selected time is invalid.")
            return

        if h < 1 or h > 12 or m < 0 or m > 59 or period not in ("AM", "PM"):
            messagebox.showwarning("Check time", "Selected time is invalid.")
            return

        if period == "AM":
            if h == 12:
                h_24 = 0
            else:
                h_24 = h
        else:
            if h == 12:
                h_24 = 12
            else:
                h_24 = h + 12

        time_24 = f"{h_24:02d}:{m:02d}"

        available, reason = self._is_time_available_for_two_hours(doctor, date_str, time_24)
        if available:
            messagebox.showinfo("Check time", "This time is available.")
        else:
            messagebox.showerror("Check time", reason or "This time is not available.")

    def _prev_date(self):
        if not self.available_dates:
            return
        if self.current_date_index is None:
            self.current_date_index = 0
        else:
            self.current_date_index = max(0, self.current_date_index - 1)
        self._set_date_from_index()

    def _next_date(self):
        if not self.available_dates:
            return
        if self.current_date_index is None:
            self.current_date_index = 0
        else:
            self.current_date_index = min(len(self.available_dates) - 1, self.current_date_index + 1)
        self._set_date_from_index()

    def _load_slots(self):
        # Rebuild the modern time-slot grid for the selected doctor and date.
        for child in self.slots_frame.winfo_children():
            child.destroy()
        self.selected_schedule = None
        self._selected_slot_btn = None
        if hasattr(self, "slot_summary_label"):
            self.slot_summary_label.configure(text="No time selected.")

        date_str = self.date_entry.get().strip()
        if not date_str:
            return

        # Do not show slots for past dates
        today_str = date.today().strftime("%Y-%m-%d")
        if date_str < today_str:
            return

        selected_doctor = self.doctor_combo.get().strip()
        if not selected_doctor:
            return

        conn = self._connect()
        cur = conn.cursor()

        # Fetch availability windows for this doctor and date
        cur.execute(
            """
            SELECT a.start_time, a.end_time, a.max_appointments, a.slot_length_minutes
            FROM doctor_availability a
            JOIN doctors d ON d.id = a.doctor_id
            WHERE a.date = ?
              AND d.name = ?
              AND a.is_available = 1
              AND a.start_time IS NOT NULL
              AND d.status = 'active'
            ORDER BY a.start_time
            """,
            (date_str, selected_doctor),
        )

        windows = cur.fetchall()

        # If the doctor has not configured explicit slots for this day, fall
        # back to a default 09:0000 duty window so receptionists can still
        # book standard 2-hour appointments.
        if not windows:
            windows = [("09:00", "17:00", 1, None)]

        from datetime import timedelta as _td

        # Layout config: up to 4 buttons per row
        self.slots_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        row_idx = 0
        col_idx = 0

        for start_t, end_t, max_appt, slot_len in windows:
            try:
                range_start = datetime.strptime(f"{date_str} {start_t}", "%Y-%m-%d %H:%M")
                range_end = datetime.strptime(f"{date_str} {end_t}", "%Y-%m-%d %H:%M")
            except ValueError:
                continue

            # Fixed 2-hour appointments, step forward by 2 hours for each option
            step = _td(hours=2)
            current = range_start
            while current + step <= range_end:
                end_dt = current + step

                # Skip times that fail the availability check (doctor rules + overlaps)
                time_24 = current.strftime("%H:%M")
                ok, _reason = self._is_time_available_for_two_hours(
                    selected_doctor, date_str, time_24
                )

                schedule_str = current.strftime("%Y-%m-%d %H:%M")

                # Capacity for each exact start time is 1 in this receptionist flow
                cur.execute(
                    "SELECT COUNT(*) FROM appointments WHERE doctor_name = ? AND schedule = ?",
                    (selected_doctor, schedule_str),
                )
                count = cur.fetchone()[0]
                remaining = max(0, 1 - int(count))

                pretty_start = current.strftime("%I:%M %p").lstrip("0")
                pretty_end = end_dt.strftime("%I:%M %p").lstrip("0")
                label_text = f"{pretty_start} - {pretty_end}"

                if not ok or remaining <= 0:
                    fg = "#4b5563"  # gray for full / not allowed
                    hover = fg
                    state = "disabled"
                else:
                    fg = "#16a34a"  # green for available
                    hover = "#15803d"
                    state = "normal"

                btn = ctk.CTkButton(
                    self.slots_frame,
                    text=label_text,
                    width=140,
                    height=28,
                    fg_color=fg,
                    hover_color=hover,
                    state=state,
                )

                if state == "normal":
                    btn._base_fg_color = fg
                    btn.configure(
                        command=lambda s=schedule_str, b=btn, rem=remaining, ma=1, doc=selected_doctor: self._select_slot(
                            s,
                            b,
                            rem,
                            ma,
                            doc,
                        )
                    )

                btn.grid(row=row_idx, column=col_idx, padx=4, pady=4, sticky="ew")
                col_idx += 1
                if col_idx >= 4:
                    col_idx = 0
                    row_idx += 1

                current += step

        conn.close()

    def _find_first_available_schedule(self, doctor: str, date_str: str):
        """Return the earliest free schedule for a doctor on a given date.

        Looks at doctor_availability for that doctor and day, then walks each
        configured time range in slot-length steps. The first time with no
        appointment in the appointments table is returned as (schedule_str, dt).
        If none are available, returns (None, None).
        """

        if not doctor or not date_str:
            return None, None

        # Do not allow booking in the past
        try:
            chosen_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None, None

        if chosen_date < date.today():
            return None, None

        conn = self._connect()
        cur = conn.cursor()

        # Confirm the doctor is active and get id
        cur.execute("SELECT id FROM doctors WHERE name = ? AND status = 'active'", (doctor,))
        row = cur.fetchone()
        if row is None:
            conn.close()
            return None, None
        doctor_id = row[0]

        # Ensure the day is not explicitly marked unavailable
        cur.execute(
            """
            SELECT is_available FROM doctor_availability
            WHERE doctor_id = ? AND date = ? AND start_time IS NULL
            ORDER BY id DESC LIMIT 1
            """,
            (doctor_id, date_str),
        )
        row = cur.fetchone()
        if row is not None and row[0] == 0:
            conn.close()
            return None, None

        # Fetch all configured availability ranges for that day
        cur.execute(
            """
            SELECT start_time, end_time, max_appointments, slot_length_minutes
            FROM doctor_availability
            WHERE doctor_id = ? AND date = ? AND is_available = 1 AND start_time IS NOT NULL
            ORDER BY start_time
            """,
            (doctor_id, date_str),
        )
        ranges = cur.fetchall()

        for start_t, end_t, max_appt, slot_len in ranges:
            try:
                start_dt = datetime.strptime(f"{date_str} {start_t}", "%Y-%m-%d %H:%M")
                end_dt = datetime.strptime(f"{date_str} {end_t}", "%Y-%m-%d %H:%M")
            except ValueError:
                continue

            # Step by configured slot length, defaulting to 30 minutes
            step_minutes = int(slot_len) if slot_len else 30
            if step_minutes <= 0:
                step_minutes = 30

            current = start_dt
            while current < end_dt:
                slot_end_dt = current + timedelta(minutes=step_minutes)
                if slot_end_dt > end_dt:
                    slot_end_dt = end_dt

                schedule_str = current.strftime("%Y-%m-%d %H:%M")

                # Each slot represents capacity 1 in this simplified model.
                cur.execute(
                    "SELECT COUNT(*) FROM appointments WHERE doctor_name = ? AND schedule = ?",
                    (doctor, schedule_str),
                )
                count = cur.fetchone()[0]

                if count < 1:
                    conn.close()
                    return schedule_str, current

                current += timedelta(minutes=step_minutes)

        conn.close()
        return None, None

    def _select_slot(self, schedule_str: str, btn, remaining, max_appt, doctor: str):
        # If clicking the same button again, unselect it
        if self._selected_slot_btn is btn:
            base_color = getattr(btn, "_base_fg_color", "#0d74d1")
            btn.configure(fg_color=base_color)
            self._selected_slot_btn = None
            self.selected_schedule = None
            if hasattr(self, "slot_summary_label"):
                self.slot_summary_label.configure(text="No time selected.")
            return

        # Reset previous selection styling
        if self._selected_slot_btn is not None:
            prev_base = getattr(self._selected_slot_btn, "_base_fg_color", "#0d74d1")
            self._selected_slot_btn.configure(fg_color=prev_base)

        self._selected_slot_btn = btn
        self._selected_slot_btn.configure(fg_color="#145ea8")
        self.selected_schedule = schedule_str
        # Ensure doctor combo reflects the chosen doctor
        if doctor:
            try:
                self.doctor_combo.set(doctor)
            except Exception:
                pass
        if hasattr(self, "slot_summary_label"):
            time_str = datetime.strptime(schedule_str, "%Y-%m-%d %H:%M").strftime("%I:%M %p")
            date_str = schedule_str.split()[0]
            if max_appt is not None and remaining is not None:
                # Use a simple middle-dot separator between time and remaining capacity
                self.slot_summary_label.configure(
                    text=f"Selected: {doctor} · {date_str} {time_str} · Remaining: {remaining} / {max_appt}"
                )
            else:
                self.slot_summary_label.configure(text=f"Selected: {doctor} · {date_str} {time_str}")

    def save_appointment(self):
        """Validate input and show a review window before saving using a chosen slot."""
        doctor = self.doctor_combo.get().strip()
        patient = self.patient_entry.get().strip()
        contact = self.contact_entry.get().strip()
        address = self.address_entry.get().strip()
        about = self.about_entry.get().strip()
        free_text = self.notes_entry.get("1.0", "end").strip()
        date_str = self.date_entry.get().strip()

        missing = []
        if not patient:
            missing.append("Full name")
        if not contact:
            missing.append("Contact no.")
        if not address:
            missing.append("Address")
        if not about:
            missing.append("Appointment about")
        if not free_text:
            missing.append("Reason / notes")
        if not doctor:
            missing.append("Doctor")
        if not date_str:
            missing.append("Date")

        schedule_str = self.selected_schedule
        if not schedule_str:
            missing.append("Time slot")

        if missing:
            messagebox.showwarning(
                "Validation",
                "Please fill in all required fields before saving:\n- " + "\n- ".join(missing),
            )
            return

        try:
            dt = datetime.strptime(schedule_str, "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showwarning("Validation", "Selected time is invalid.")
            return

        # Final safety check: ensure this 2-hour window is still valid
        time_24 = dt.strftime("%H:%M")
        available, reason = self._is_time_available_for_two_hours(doctor, date_str, time_24)
        if not available:
            messagebox.showerror("Appointment", reason or "This time is not available.")
            return

        # Generate a simple unique barcode for this pending appointment
        barcode = "APPT-" + uuid4().hex[:10].upper()

        data = {
            "doctor": doctor,
            "schedule_str": schedule_str,
            "patient": patient,
            "contact": contact,
            "address": address,
            "about": about,
            "free_text": free_text,
            "date_str": date_str,
            "datetime_obj": dt,
            "barcode": barcode,
        }

        self._open_review_window(data)

    def _open_review_window(self, data: dict):
        """Show a clean review/receipt window with appointment details and barcode."""
        master = self.winfo_toplevel()
        win = ctk.CTkToplevel(master)
        win.title("Review Appointment")
        # Slightly taller so barcode and buttons are fully visible
        win.geometry("520x480")
        win.resizable(False, False)
        win.transient(master)
        win.grab_set()

        win.grid_rowconfigure(1, weight=1)
        win.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            win,
            text="Appointment Review",
            font=("Segoe UI", 20, "bold"),
        )
        title.grid(row=0, column=0, padx=20, pady=(16, 4), sticky="w")

        body = ctk.CTkFrame(win, corner_radius=10)
        body.grid(row=1, column=0, padx=20, pady=(4, 16), sticky="nsew")
        body.grid_columnconfigure(1, weight=1)

        # Format date/time nicely (time is now based on user selection)
        pretty_date = data["datetime_obj"].strftime("%Y-%m-%d")
        pretty_time = data["datetime_obj"].strftime("%I:%M %p")

        rows = [
            ("Barcode", data["barcode"]),
            ("Patient", data["patient"]),
            ("Contact", data["contact"] or "-"),
            ("Address", data["address"] or "-"),
            ("About", data["about"] or "-"),
            ("Doctor", data["doctor"]),
            ("Date", pretty_date),
            ("Time", pretty_time),
        ]

        for idx, (label, value) in enumerate(rows):
            ctk.CTkLabel(body, text=f"{label}:", font=("Segoe UI", 12, "bold")).grid(
                row=idx, column=0, padx=12, pady=4, sticky="w"
            )
            ctk.CTkLabel(body, text=value, font=("Segoe UI", 12)).grid(
                row=idx, column=1, padx=12, pady=4, sticky="w"
            )

        # Simple barcode-style visualization (text code displayed in a box)
        barcode_frame = ctk.CTkFrame(body, corner_radius=6)
        barcode_frame.grid(row=len(rows), column=0, columnspan=2, padx=12, pady=(12, 8), sticky="ew")
        barcode_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            barcode_frame,
            text=data["barcode"],
            font=("Consolas", 16, "bold"),
            anchor="center",
        ).grid(row=0, column=0, padx=8, pady=6, sticky="ew")

        # Buttons row
        buttons = ctk.CTkFrame(win, fg_color="transparent")
        buttons.grid(row=2, column=0, padx=20, pady=(0, 16), sticky="e")

        cancel_btn = ctk.CTkButton(
            buttons,
            text="Cancel",
            fg_color="#4b5563",
            hover_color="#374151",
            command=win.destroy,
        )
        cancel_btn.grid(row=0, column=0, padx=(0, 8))

        proceed_btn = ctk.CTkButton(
            buttons,
            text="Proceed",
            fg_color="#16a34a",
            hover_color="#15803d",
            command=lambda w=win, d=data: self._finalize_appointment(w, d),
        )
        proceed_btn.grid(row=0, column=1)

        # Center popup relative to main window
        win.update_idletasks()
        master.update_idletasks()
        mx = master.winfo_rootx()
        my = master.winfo_rooty()
        mw = master.winfo_width()
        mh = master.winfo_height()
        ww = win.winfo_width()
        wh = win.winfo_height()
        x = mx + (mw - ww) // 2
        y = my + (mh - wh) // 2
        win.geometry(f"{ww}x{wh}+{x}+{y}")

    def _finalize_appointment(self, win: ctk.CTkToplevel, data: dict):
        """Actually insert the appointment after the user confirms in the review window."""
        doctor = data["doctor"]
        schedule_str = data["schedule_str"]
        patient = data["patient"]
        contact = data["contact"]
        address = data["address"]
        about = data["about"]
        free_text = data["free_text"]
        date_str = data["date_str"]

        conn = self._connect()
        cur = conn.cursor()

        # Find doctor id
        cur.execute("SELECT id FROM doctors WHERE name = ? AND status = 'active'", (doctor,))
        row = cur.fetchone()
        if row is None:
            conn.close()
            messagebox.showerror("Doctor", "Selected doctor is not active.")
            win.destroy()
            return
        doctor_id = row[0]

        cur.execute(
            """
            SELECT is_available FROM doctor_availability
            WHERE doctor_id = ? AND date = ? AND start_time IS NULL
            ORDER BY id DESC LIMIT 1
            """,
            (doctor_id, date_str),
        )
        row = cur.fetchone()
        if row is not None and row[0] == 0:
            conn.close()
            messagebox.showerror("Availability", "Doctor is marked not available on this day.")
            win.destroy()
            return

        # Build rich notes string with extra patient info without changing schema
        note_parts = []
        if contact:
            note_parts.append(f"Contact: {contact}")
        if address:
            note_parts.append(f"Address: {address}")
        if about:
            note_parts.append(f"About: {about}")
        if free_text:
            note_parts.append(f"Notes: {free_text}")
        notes_value = " | ".join(note_parts) if note_parts else None

        # Insert appointment
        cur.execute(
            """
            INSERT INTO appointments (patient_name, doctor_name, schedule, notes, barcode, is_rescheduled, is_paid)
            VALUES (?, ?, ?, ?, ?, 0, 0)
            """,
            (patient, doctor, schedule_str, notes_value, data["barcode"]),
        )
        conn.commit()
        conn.close()

        # After successful save, generate a receptionist receipt BMP (or .txt fallback)
        try:
            project_root = os.path.dirname(os.path.abspath(DB_NAME))
            receipts_dir = os.path.join(project_root, "RECEIPT_RECEPTIONIST")
            os.makedirs(receipts_dir, exist_ok=True)

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            barcode = data.get("barcode") or "NO_BARCODE"
            safe_barcode = barcode.replace(os.sep, "_")
            filename = f"appointment_{safe_barcode}_{ts}.bmp"
            filepath = os.path.join(receipts_dir, filename)

            sched_dt = data.get("datetime_obj")
            if isinstance(sched_dt, datetime):
                sched_text = sched_dt.strftime("%Y-%m-%d %I:%M %p")
            else:
                sched_text = schedule_str

            lines = [
                "MEDISKED: HOSPITAL SCHEDULING AND BILLING MANAGEMENT SYSTEM",
                "RECEPTIONIST APPOINTMENT RECEIPT",
                "",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}",
                "",
                f"Barcode: {barcode}",
                f"Patient: {patient}",
                f"Doctor: {doctor}",
                f"Schedule: {sched_text}",
                "",
                f"Contact: {contact or '-'}",
                f"Address: {address or '-'}",
                f"About: {about or '-'}",
                f"Notes: {free_text or '-'}",
            ]

            _write_receptionist_receipt_image(filepath, lines)
        except Exception:
            # If writing fails, ignore; appointment is already saved
            pass

        win.destroy()

        messagebox.showinfo("Appointment", "Appointment created successfully.")
        try:
            detail = f"Appointment for '{patient}' with Dr {doctor} at {schedule_str}"
            log_activity(None, "receptionist", "create_appointment", detail)
        except Exception:
            pass

        # Clear form after successful save and refresh slots
        self._clear_form()
        self._load_slots()


def _write_receptionist_receipt_image(filepath: str, lines: list[str]) -> None:
    """Render receptionist receipt as a BMP image if Pillow is installed.

    Falls back to a .txt file if Pillow is not available.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont  # type: ignore
    except Exception:
        fallback = filepath[:-4] + ".txt" if filepath.lower().endswith(".bmp") else filepath + ".txt"
        try:
            with open(fallback, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
        except Exception:
            pass
        return

    width = 800
    height = 1000
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("arial.ttf", 24)
        header_font = ImageFont.truetype("arial.ttf", 14)
        text_font = ImageFont.truetype("arial.ttf", 13)
    except Exception:
        title_font = header_font = text_font = ImageFont.load_default()

    x_margin = 60
    y = 40

    # Header: MEDISKED hospital info
    draw.text((x_margin, y), "MEDISKED HOSPITAL", fill="black", font=title_font)
    y += 36
    draw.text((x_margin, y), "ADDRESS: Sample Road, Sample City", fill="black", font=header_font)
    y += 22
    draw.text((x_margin, y), "CONTACT: 000-000-0000", fill="black", font=header_font)
    y += 34

    # Separator
    draw.line((x_margin, y, width - x_margin, y), fill="black", width=1)
    y += 20

    # Body lines (patient + appointment info from caller)
    for line in lines:
        draw.text((x_margin, y), line, fill="black", font=text_font)
        y += 20

    # Simple footer table for notes / signature
    table_top = height - 220
    table_left = x_margin
    table_right = width - x_margin
    table_bottom = height - 80

    draw.rectangle((table_left, table_top, table_right, table_bottom), outline="black", width=1)

    row_h = 28
    draw.line((table_left, table_top + row_h, table_right, table_top + row_h), fill="black", width=1)
    draw.text((table_left + 8, table_top + 6), "RECEPTIONIST SIGNATURE", fill="black", font=header_font)

    try:
        img.save(filepath, format="BMP")
    except Exception:
        fallback = filepath[:-4] + ".txt" if filepath.lower().endswith(".bmp") else filepath + ".txt"
        try:
            with open(fallback, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
        except Exception:
            pass
