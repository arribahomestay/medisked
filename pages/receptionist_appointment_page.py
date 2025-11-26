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
        form.grid_rowconfigure(5, weight=1)   # patient notes grows
        form.grid_rowconfigure(9, weight=1)   # slots area grows

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

        # Date (simple picker row: prev / entry / next instead of dropdown)
        ctk.CTkLabel(form, text="Date").grid(row=8, column=0, padx=20, pady=4, sticky="w")
        date_row = ctk.CTkFrame(form, fg_color="transparent")
        date_row.grid(row=8, column=1, padx=20, pady=4, sticky="ew")
        date_row.grid_columnconfigure(1, weight=1)

        self.prev_date_button = ctk.CTkButton(date_row, text="<", width=28, command=self._prev_date)
        self.prev_date_button.grid(row=0, column=0, padx=(0, 4))

        self.date_entry = ctk.CTkEntry(date_row)
        self.date_entry.grid(row=0, column=1, sticky="ew")
        self.date_entry.bind("<FocusOut>", lambda e: self._on_date_changed())
        self.date_entry.bind("<Button-1>", lambda e: self._open_date_picker())

        self.next_date_button = ctk.CTkButton(date_row, text=">", width=28, command=self._next_date)
        self.next_date_button.grid(row=0, column=2, padx=(4, 0))

        # Action buttons row (right-aligned), placed directly below the Date row.
        actions_row = ctk.CTkFrame(form, fg_color="transparent")
        actions_row.grid(row=9, column=0, columnspan=2, padx=20, pady=(8, 20), sticky="e")
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
        dummy_container.grid(row=10, column=0, columnspan=2, padx=20, pady=0, sticky="nsew")
        dummy_container.grid_columnconfigure(0, weight=1)

        self.slots_frame = ctk.CTkFrame(dummy_container, corner_radius=8, fg_color="transparent")
        self.slots_frame.grid(row=0, column=0, padx=0, pady=0, sticky="nsew")

        # Selected_schedule is no longer chosen by clicking a time slot; it will be
        # computed automatically when saving the appointment based on the first
        # available slot on the chosen day.
        self.selected_schedule = None
        self._selected_slot_btn = None
        self.available_dates = []
        self.current_date_index = None

        self._date_picker_win = None
        self._date_picker_year = None
        self._date_picker_month = None

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
        else:
            self.current_date_index = None
            self.date_entry.delete(0, "end")

        self._load_slots()

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

        for i, wd in enumerate(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]):
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
                else:
                    # By default days are available (green) and clickable
                    fg_color = "#1c9b3b"
                    hover_color = "#17a349"
                    state = "normal"

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
        self._load_slots()

    def _on_date_changed(self):
        # When the user edits the date manually, forget the index and reload slots.
        self.current_date_index = None
        self._load_slots()

    def _set_date_from_index(self):
        if not self.available_dates or self.current_date_index is None:
            return
        self.date_entry.delete(0, "end")
        self.date_entry.insert(0, self.available_dates[self.current_date_index])
        self._load_slots()

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
        # No longer showing individual time slots; just clear any previous content.
        for child in self.slots_frame.winfo_children():
            child.destroy()
        self.selected_schedule = None
        self._selected_slot_btn = None

        date_str = self.date_entry.get().strip()
        filter_by_date = bool(date_str)

        # Do not show slots for past dates
        if filter_by_date and date_str < date.today().strftime("%Y-%m-%d"):
            return

        # Respect selected doctor; if none, there is nothing to show
        selected_doctor = self.doctor_combo.get().strip()
        if not selected_doctor:
            return

        conn = self._connect()
        cur = conn.cursor()

        # Fetch availability slots for either a specific date or all dates,
        # but only for the currently selected doctor.
        if filter_by_date:
            cur.execute(
                """
                SELECT d.name, a.date, a.start_time, a.end_time,
                       a.max_appointments, a.slot_length_minutes
                FROM doctor_availability a
                JOIN doctors d ON d.id = a.doctor_id
                WHERE a.date = ?
                  AND d.name = ?
                  AND a.is_available = 1
                  AND a.start_time IS NOT NULL
                  AND d.status = 'active'
                ORDER BY a.date, d.name, a.start_time
                """,
                (date_str, selected_doctor),
            )
        else:
            cur.execute(
                """
                SELECT d.name, a.date, a.start_time, a.end_time,
                       a.max_appointments, a.slot_length_minutes
                FROM doctor_availability a
                JOIN doctors d ON d.id = a.doctor_id
                WHERE d.name = ?
                  AND a.is_available = 1
                  AND a.start_time IS NOT NULL
                  AND d.status = 'active'
                ORDER BY a.date, d.name, a.start_time
                """,
                (selected_doctor,),
            )

        slots = cur.fetchall()

        # We no longer render individual slot buttons here; this method is
        # retained only so that date navigation and availability queries keep
        # working. Actual selection of a concrete time happens inside
        # _find_first_available_schedule.

        conn.close()

        # We no longer render slots here; availability will be checked when saving.

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
        """Validate input and show a review/receipt window before saving.

        The receptionist selects only doctor + date; the system automatically
        chooses the first available time slot on that day for that doctor.
        """
        doctor = self.doctor_combo.get().strip()
        patient = self.patient_entry.get().strip()
        contact = self.contact_entry.get().strip()
        address = self.address_entry.get().strip()
        about = self.about_entry.get().strip()
        free_text = self.notes_entry.get("1.0", "end").strip()
        date_str = self.date_entry.get().strip()

        if not doctor or not date_str or not patient:
            messagebox.showwarning("Validation", "Doctor, date, and patient name are required.")
            return

        # Find the first available slot for this doctor and date.
        schedule_str, dt = self._find_first_available_schedule(doctor, date_str)
        if schedule_str is None or dt is None:
            messagebox.showerror(
                "Availability",
                "No available time slots remain for this doctor on the selected day.",
            )
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

        # Format date/time nicely (time is not shown to receptionist)
        pretty_date = data["datetime_obj"].strftime("%Y-%m-%d")
        pretty_time = "-"

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

        # Check day not explicitly marked unavailable
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

        # Check there is at least one availability slot containing this time
        cur.execute(
            """
            SELECT id, start_time, end_time, max_appointments
            FROM doctor_availability
            WHERE doctor_id = ? AND date = ? AND is_available = 1 AND start_time IS NOT NULL
            """,
            (doctor_id, date_str),
        )
        slots = cur.fetchall()

        def time_in_range(t, start, end):
            return start <= t < end

        dt = data["datetime_obj"]
        t_val = dt.strftime("%H:%M")

        matched_slot = None
        for sid, start_t, end_t, max_appt in slots:
            if time_in_range(t_val, start_t, end_t):
                matched_slot = (sid, max_appt)
                break

        if matched_slot is None:
            conn.close()
            messagebox.showerror("Availability", "No configured availability slot covers this time.")
            win.destroy()
            return

        slot_id, max_appt = matched_slot

        # Check existing appointments for this doctor and time
        cur.execute(
            "SELECT COUNT(*) FROM appointments WHERE doctor_name = ? AND schedule = ?",
            (doctor, schedule_str),
        )
        count = cur.fetchone()[0]

        # Each slot represents exactly one appointment; block if already booked
        if count >= 1:
            conn.close()
            messagebox.showerror("Availability", "This time slot is already full.")
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
            project_root = os.path.dirname(os.path.dirname(__file__))
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
