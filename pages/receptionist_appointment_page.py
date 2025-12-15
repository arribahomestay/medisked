import customtkinter as ctk
import sqlite3
import calendar
from datetime import datetime, timedelta, date
from uuid import uuid4
import os

from tkinter import messagebox, filedialog
from database import DB_NAME, log_activity

class ReceptionistAppointmentPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header Card
        header_card = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=16)
        header_card.grid(row=0, column=0, padx=0, pady=(0, 20), sticky="ew")
        header_card.grid_columnconfigure(0, weight=1)

        title_frame = ctk.CTkFrame(header_card, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=24, pady=24, sticky="ew")
        
        ctk.CTkLabel(
            title_frame, 
            text="Book Appointment", 
            font=("Inter", 24, "bold"), 
            text_color="white"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame, 
            text="Schedule a new consultation for a patient.", 
            font=("Inter", 13), 
            text_color="#94a3b8"
        ).pack(anchor="w", pady=(2, 0))

        # 2. Main Content Card (Scrollable Form)
        form = ctk.CTkScrollableFrame(self, corner_radius=16, fg_color="#1e293b")
        form.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        form.grid_columnconfigure(0, weight=1, uniform="top_cols")
        form.grid_columnconfigure(1, weight=1, uniform="top_cols")
        
        # --- LEFT COLUMN: PATIENT DETAILS ---
        left_frame = ctk.CTkFrame(form, fg_color="transparent")
        left_frame.grid(row=0, column=0, padx=(20, 10), pady=0, sticky="nsew")
        left_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(left_frame, text="PATIENT DETAILS", font=("Inter", 12, "bold"), text_color="#64748b").grid(
            row=0, column=0, columnspan=2, pady=(24, 16), sticky="w"
        )

        def _left_entry(label, r, height=38):
            ctk.CTkLabel(left_frame, text=label, font=("Inter", 13), text_color="#94a3b8").grid(row=r, column=0, padx=(0, 10), pady=6, sticky="nw")
            e = ctk.CTkEntry(
                left_frame, height=height, corner_radius=8, fg_color="#334155", border_color="#475569", text_color="white", font=("Inter", 13)
            )
            e.grid(row=r, column=1, pady=6, sticky="ew")
            return e

        self.patient_entry = _left_entry("Full Name", 1)
        self.contact_entry = _left_entry("Contact No.", 2)
        vcmd = self.register(self._validate_contact_digits)
        try: self.contact_entry.configure(validate="key", validatecommand=(vcmd, "%P"))
        except: pass
        self.address_entry = _left_entry("Address", 3)

        # --- RIGHT COLUMN: APPOINTMENT DETAILS ---
        right_frame = ctk.CTkFrame(form, fg_color="transparent")
        right_frame.grid(row=0, column=1, padx=(10, 20), pady=0, sticky="nsew")
        right_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(right_frame, text="APPOINTMENT", font=("Inter", 12, "bold"), text_color="#64748b").grid(
            row=0, column=0, columnspan=2, pady=(24, 16), sticky="w"
        )

        # Doctor
        ctk.CTkLabel(right_frame, text="Doctor", font=("Inter", 13), text_color="#94a3b8").grid(row=1, column=0, padx=(0, 10), pady=6, sticky="nw")
        doc_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        doc_frame.grid(row=1, column=1, pady=6, sticky="ew")
        doc_frame.grid_columnconfigure(0, weight=1)
        
        self.doctor_combo = ctk.CTkComboBox(
            doc_frame, values=[], state="readonly", height=38, corner_radius=8, fg_color="#334155", border_color="#475569", text_color="white", font=("Inter", 13), dropdown_fg_color="#334155",
            command=lambda _value: self._load_dates()
        )
        self.doctor_combo.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkButton(doc_frame, text="✕", width=38, height=38, fg_color="#ef4444", hover_color="#dc2626", command=self._clear_doctor).grid(row=0, column=1)

        # Date (Hidden, logic uses calendar)
        self.date_entry = ctk.CTkEntry(right_frame, height=38, fg_color="#334155", border_color="#475569", text_color="white", font=("Inter", 13))

        # Hidden logic combos
        self.date_month_combo = ctk.CTkComboBox(right_frame, width=0)
        self.date_day_combo = ctk.CTkComboBox(right_frame, width=0)
        self.date_year_combo = ctk.CTkComboBox(right_frame, width=0)

        # Service / About
        ctk.CTkLabel(right_frame, text="Service", font=("Inter", 13), text_color="#94a3b8").grid(row=3, column=0, padx=(0, 10), pady=6, sticky="nw")
        svc_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        svc_frame.grid(row=3, column=1, pady=6, sticky="ew")
        svc_frame.grid_columnconfigure(0, weight=1)
        
        self.about_entry = ctk.CTkEntry(svc_frame, state="readonly", height=38, corner_radius=8, fg_color="#334155", border_color="#475569", text_color="white", font=("Inter", 13))
        self.about_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        
        ctk.CTkButton(svc_frame, text="Select", width=70, height=38, font=("Inter", 12, "bold"), fg_color="#3b82f6", hover_color="#2563eb", command=self._open_service_picker).grid(row=0, column=1)

        # Notes
        ctk.CTkLabel(right_frame, text="Notes", font=("Inter", 13), text_color="#94a3b8").grid(row=4, column=0, padx=(0, 10), pady=6, sticky="nw")
        self.notes_entry = ctk.CTkTextbox(right_frame, height=80, corner_radius=8, fg_color="#334155", border_color="#475569", text_color="white", font=("Inter", 13))
        self.notes_entry.grid(row=4, column=1, pady=6, sticky="ew")
        
        # --- BOTTOM SECTION: CALENDAR ---
        cal_container = ctk.CTkFrame(form, fg_color="transparent")
        cal_container.grid(row=1, column=0, columnspan=2, padx=20, pady=(20, 4), sticky="ew")
        cal_container.grid_columnconfigure(1, weight=1)

        self.appt_cal_prev_btn = ctk.CTkButton(cal_container, text="<", width=32, height=32, command=self._appt_prev_month, fg_color="#334155", hover_color="#475569")
        self.appt_cal_prev_btn.grid(row=0, column=0, padx=(0, 5))

        self.appt_month_label = ctk.CTkLabel(cal_container, text="", font=("Inter", 14, "bold"), text_color="white")
        self.appt_month_label.grid(row=0, column=1)

        self.appt_cal_next_btn = ctk.CTkButton(cal_container, text=">", width=32, height=32, command=self._appt_next_month, fg_color="#334155", hover_color="#475569")
        self.appt_cal_next_btn.grid(row=0, column=2, padx=(5, 0))

        # Inline Calendar Grid
        self.appt_calendar_frame = ctk.CTkFrame(form, corner_radius=12, fg_color="#0f172a", border_width=1, border_color="#334155")
        self.appt_calendar_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=8, sticky="nsew")
        for col in range(7):
            self.appt_calendar_frame.grid_columnconfigure(col, weight=1)

        # Time Slots
        self.slots_section_wrapper = ctk.CTkFrame(form, fg_color="transparent")
        self.slots_section_wrapper.grid(row=3, column=0, columnspan=2, padx=20, pady=(16, 8), sticky="nsew")
        self.slots_section_wrapper.grid_columnconfigure(0, weight=1)
        self.slots_section_wrapper.grid_remove() 

        ctk.CTkLabel(self.slots_section_wrapper, text="AVAILABLE SLOTS", font=("Inter", 12, "bold"), text_color="#64748b").pack(anchor="w", pady=(0, 8))
        
        self.slots_frame = ctk.CTkFrame(self.slots_section_wrapper, corner_radius=10, fg_color="transparent")
        self.slots_frame.pack(fill="x", expand=True)

        self.slot_summary_label = ctk.CTkLabel(self.slots_section_wrapper, text="No time selected.", font=("Inter", 13), text_color="#fbbf24")
        self.slot_summary_label.pack(anchor="w", pady=(10, 0))

        # Action Buttons
        actions_row = ctk.CTkFrame(form, fg_color="transparent")
        actions_row.grid(row=4, column=0, columnspan=2, padx=20, pady=32, sticky="e")

        ctk.CTkButton(
            actions_row,
            text="Clear Form",
            font=("Inter", 13),
            fg_color="transparent",
            border_width=1,
            border_color="#ef4444", 
            text_color="#ef4444",
            hover_color="#1e293b",
            width=100,
            command=self._clear_form
        ).pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            actions_row,
            text="Save Appointment",
            font=("Inter", 13, "bold"),
            fg_color="#10b981", 
            hover_color="#059669",
            width=160,
            height=40,
            command=self.save_appointment,
        ).pack(side="left")

        # Init state
        self.selected_schedule = None
        self._selected_slot_btn = None
        self.available_dates = []
        self.current_date_index = None

        services = [
            "General Consultation - 400 PHP", "Pediatrics Consultation - 450 PHP", "Internal Medicine - 500 PHP",
            "Cardiology Consultation - 800 PHP", "OB-GYN Consultation - 700 PHP", "Dermatology Consultation - 600 PHP",
            "ENT Consultation - 550 PHP", "Orthopedic Consultation - 750 PHP", "Ophthalmology Consultation - 500 PHP",
            "Dental Consultation - 350 PHP", "CBC (Complete Blood Count) - 250 PHP", "Urinalysis - 150 PHP",
            "Stool Examination - 150 PHP", "Fasting Blood Sugar (FBS) - 200 PHP", "HbA1c - 800 PHP",
            "Lipid Profile - 700 PHP", "Creatinine Test - 300 PHP", "BUN (Blood Urea Nitrogen) - 250 PHP",
            "Liver Function Test (LFT) - 500 PHP", "TSH / Thyroid Test - 700 PHP", "Chest X-Ray (PA View) - 650 PHP",
            "Lumbar X-Ray - 800 PHP", "Ultrasound – Whole Abdomen - 1000 PHP", "Ultrasound – Pelvic / OB - 900 PHP",
            "Ultrasound – Thyroid - 800 PHP", "2D Echo - 2500 PHP", "ECG - 600 PHP", "CT Scan (Plain) - 6000 PHP",
            "MRI (Plain) - 10000 PHP", "Mammogram - 2000 PHP", "Wound Dressing - 300 PHP", "Nebulization - 200 PHP",
            "Injection Service - 200 PHP", "Suturing (small wound) - 1000 PHP", "Ear Cleaning - 400 PHP",
            "Incision and Drainage - 800 PHP", "ECG with Interpretation - 800 PHP", "Cast / Splint Application - 1000 PHP",
            "Pap Smear - 500 PHP", "Pregnancy Test (Urine) - 200 PHP", "Medical Certificate - 250 PHP",
            "Vital Signs Check - 100 PHP", "ECG Print Request - 150 PHP", "X-Ray CD Copy - 150 PHP",
            "Laboratory Results Printing - 100 PHP", "Doctor Follow-Up Consultation - 300 PHP",
            "Teleconsultation - 400 PHP", "Nutritional Counseling - 500 PHP", "Family Planning Consultation - 400 PHP",
            "Vaccination Service (Service Fee) - 400 PHP",
        ]
        self._about_services = services
        
        today = date.today()
        self.date_month_combo.set(f"{today.month:02d}")
        self.date_day_combo.set(f"{today.day:02d}")
        self.date_year_combo.set(str(today.year))
        
        self.appt_cal_year = today.year
        self.appt_cal_month = today.month
        self._refresh_appt_calendar()

        self.date_month_combo.configure(command=lambda _v: self._sync_date_entry_from_combos())
        self.date_day_combo.configure(command=lambda _v: self._sync_date_entry_from_combos())
        self.date_year_combo.configure(command=lambda _v: self._sync_date_entry_from_combos())
        
        self._load_doctors()

    def _open_service_picker(self):
        services = getattr(self, "_about_services", [])
        if not services: return

        master = self.winfo_toplevel()
        win = ctk.CTkToplevel(master)
        win.title("Select service")
        win.geometry("420x400")
        win.resizable(False, False)
        win.transient(master)
        win.grab_set()
        win.configure(fg_color="#0f172a")

        win.grid_rowconfigure(1, weight=1)
        win.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(win, text="Choose Service", font=("Inter", 16, "bold"), text_color="white")
        title.grid(row=0, column=0, padx=16, pady=(16, 12), sticky="w")

        list_frame = ctk.CTkScrollableFrame(win, corner_radius=10, fg_color="#1e293b")
        list_frame.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)

        def _choose(value: str):
            try: self.about_entry.configure(state="normal")
            except: pass
            self.about_entry.delete(0, "end")
            self.about_entry.insert(0, value)
            try: self.about_entry.configure(state="readonly")
            except: pass
            win.destroy()

        for idx, svc in enumerate(services):
            btn = ctk.CTkButton(
                list_frame,
                text=svc,
                font=("Inter", 13),
                fg_color="#334155",
                hover_color="#475569",
                height=32,
                anchor="w",
                command=lambda v=svc: _choose(v),
            )
            btn.grid(row=idx, column=0, padx=4, pady=2, sticky="ew")

        win.update_idletasks()
        master.update_idletasks()
        try:
             mx = master.winfo_rootx() + (master.winfo_width() - 420)//2
             my = master.winfo_rooty() + (master.winfo_height() - 400)//2
             win.geometry(f"420x400+{mx}+{my}")
        except: pass

    def _validate_contact_digits(self, new_value: str) -> bool:
        return new_value == "" or new_value.isdigit()

    def _connect(self):
        return sqlite3.connect(DB_NAME)

    def _clear_doctor(self):
        try: self.doctor_combo.set("")
        except: pass
        self.available_dates = []
        self.current_date_index = None
        self.date_entry.delete(0, "end")
        for c in self.slots_frame.winfo_children(): c.destroy()
        self.selected_schedule = None
        self._selected_slot_btn = None
        if hasattr(self, "slot_summary_label"):
            self.slot_summary_label.configure(text="No time selected.")
        if hasattr(self, "slots_section_wrapper"):
            self.slots_section_wrapper.grid_remove()

    def _clear_form(self):
        self.patient_entry.delete(0, "end")
        self.contact_entry.delete(0, "end")
        self.address_entry.delete(0, "end")
        self.about_entry.configure(state="normal")
        self.about_entry.delete(0, "end")
        self.about_entry.configure(state="readonly")
        self.notes_entry.delete("1.0", "end")
        self._clear_doctor()
        
        today = date.today()
        try:
            self.date_month_combo.set(f"{today.month:02d}")
            self.date_day_combo.set(f"{today.day:02d}")
            self.date_year_combo.set(str(today.year))
        except: pass
        
        self.appt_cal_year = today.year
        self.appt_cal_month = today.month
        self._refresh_appt_calendar()

    def _appt_prev_month(self):
        if self.appt_cal_month == 1:
            self.appt_cal_month = 12
            self.appt_cal_year -= 1
        else:
            self.appt_cal_month -= 1
        self._refresh_appt_calendar()

    def _appt_next_month(self):
        if self.appt_cal_month == 12:
            self.appt_cal_month = 1
            self.appt_cal_year += 1
        else:
            self.appt_cal_month += 1
        self._refresh_appt_calendar()

    def _refresh_appt_calendar(self):
        if not hasattr(self, "appt_calendar_frame"): return
        for c in self.appt_calendar_frame.winfo_children(): c.destroy()

        year = getattr(self, "appt_cal_year", date.today().year)
        month = getattr(self, "appt_cal_month", date.today().month)
        try: self.appt_month_label.configure(text=f"{calendar.month_name[month]} {year}")
        except: pass
        
        for i, wd in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            ctk.CTkLabel(self.appt_calendar_frame, text=wd, font=("Inter", 12, "bold"), text_color="#cbd5e1").grid(row=0, column=i, pady=6)

        today_str = date.today().strftime("%Y-%m-%d")
        
        selected_doctor = self.doctor_combo.get().strip()
        not_available_days = set()

        if selected_doctor and selected_doctor != "Add doctor first":
            conn = self._connect()
            cur = conn.cursor()
            cur.execute("SELECT id FROM doctors WHERE name = ? AND status = 'active'", (selected_doctor,))
            row = cur.fetchone()
            if row:
                doc_id = row[0]
                ms = f"{year:04d}-{month:02d}-01"
                me = f"{year:04d}-{month:02d}-31"
                cur.execute("SELECT date FROM doctor_availability WHERE doctor_id=? AND date BETWEEN ? AND ? AND start_time IS NULL AND is_available=0", (doc_id, ms, me))
                not_available_days = {d for (d,) in cur.fetchall()}
            conn.close()

        cal = calendar.Calendar(firstweekday=0)
        row_idx = 1
        for week in cal.monthdayscalendar(year, month):
            for col, day_num in enumerate(week):
                if day_num == 0: continue
                d_str = f"{year:04d}-{month:02d}-{day_num:02d}"

                if d_str < today_str:
                    fg, hover, state = "#334155", "#334155", "disabled"
                elif d_str in not_available_days:
                    fg, hover, state = "#ef4444", "#ef4444", "disabled"
                else:
                    fg, hover, state = "#10b981", "#059669", "normal"

                def _pick(ds=d_str):
                    self.date_entry.delete(0, "end")
                    self.date_entry.insert(0, ds)
                    self.current_date_index = None
                    self._sync_combos_from_date_entry()

                ctk.CTkButton(
                    self.appt_calendar_frame,
                    text=str(day_num), width=32, height=32,
                    fg_color=fg, hover_color=hover, state=state,
                    command=(None if state=="disabled" else _pick),
                    font=("Inter", 12)
                ).grid(row=row_idx, column=col, padx=3, pady=3, sticky="nsew")
            row_idx += 1

    def _sync_date_entry_from_combos(self):
        m = self.date_month_combo.get().strip()
        d = self.date_day_combo.get().strip()
        y = self.date_year_combo.get().strip()
        if not (m and d and y): return
        try:
             # Basic limit logic
             mx = calendar.monthrange(int(y), int(m))[1]
             dd = min(int(d), mx)
             new_date = date(int(y), int(m), dd)
             self.date_entry.delete(0, "end")
             self.date_entry.insert(0, new_date.strftime("%Y-%m-%d"))
             self.current_date_index = None
             self._load_slots()
        except: pass

    def _sync_combos_from_date_entry(self):
        ds = self.date_entry.get().strip()
        if not ds: return
        try:
            dt = datetime.strptime(ds, "%Y-%m-%d")
            self.date_month_combo.set(f"{dt.month:02d}")
            self.date_day_combo.set(f"{dt.day:02d}")
            vals = list(self.date_year_combo.cget("values") or [])
            if str(dt.year) not in vals:
                vals.append(str(dt.year))
                self.date_year_combo.configure(values=vals)
            self.date_year_combo.set(str(dt.year))
        except: pass
        self._load_slots()

    def _load_doctors(self):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT name FROM doctors WHERE status='active' ORDER BY name")
        names = [r[0] for r in cur.fetchall()]
        conn.close()
        if names:
            self.doctor_combo.configure(values=names, state="readonly")
            self.doctor_combo.set(names[0])
            self._load_dates()
        else:
            self.doctor_combo.configure(values=["Add doctor first"], state="disabled")
            self.doctor_combo.set("Add doctor first")
            self._clear_doctor()

    def _load_dates(self):
        # Just triggers calendar refresh now basically, plus auto-selection of first avail if we wanted
        # For this modern flow, we let user pick from calendar
        self._refresh_appt_calendar()

    def _load_slots(self):
        for c in self.slots_frame.winfo_children(): c.destroy()
        self.selected_schedule = None
        self._selected_slot_btn = None
        if hasattr(self, "slot_summary_label"): self.slot_summary_label.configure(text="No time selected.")
        
        date_str = self.date_entry.get().strip()
        if not date_str:
             if hasattr(self, "slots_section_wrapper"): self.slots_section_wrapper.grid_remove()
             return

        if hasattr(self, "slots_section_wrapper"): self.slots_section_wrapper.grid()
        if date_str < date.today().strftime("%Y-%m-%d"): return

        doc = self.doctor_combo.get().strip()
        if not doc: return

        conn = self._connect()
        cur = conn.cursor()
        cur.execute("""
            SELECT a.start_time, a.end_time 
            FROM doctor_availability a 
            JOIN doctors d ON d.id=a.doctor_id 
            WHERE a.date=? AND d.name=? AND a.is_available=1 AND a.start_time IS NOT NULL AND d.status='active'
            ORDER BY a.start_time
        """, (date_str, doc))
        windows = cur.fetchall()
        if not windows: windows = [("09:00", "17:00")]

        self.slots_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        r, c = 0, 0
        
        for start_t, end_t in windows:
            try:
                rs = datetime.strptime(f"{date_str} {start_t}", "%Y-%m-%d %H:%M")
                re = datetime.strptime(f"{date_str} {end_t}", "%Y-%m-%d %H:%M")
            except: continue
            
            curr = rs
            step = timedelta(hours=2)
            while curr + step <= re:
                 time_24 = curr.strftime("%H:%M")
                 ok, _ = self._is_time_available_for_two_hours(doc, date_str, time_24)
                 sch_str = curr.strftime("%Y-%m-%d %H:%M")
                 
                 cur.execute("SELECT COUNT(*) FROM appointments WHERE doctor_name=? AND schedule=?", (doc, sch_str))
                 cnt = cur.fetchone()[0]
                 rem = max(0, 1 - int(cnt))
                 
                 label = f"{curr.strftime('%I:%M %p').lstrip('0')} - {(curr+step).strftime('%I:%M %p').lstrip('0')}"
                 
                 if not ok or rem <= 0:
                     fg, hover, state = "#334155", "#334155", "disabled"
                 else:
                     fg, hover, state = "#1e293b", "#334155", "normal"
                 
                 btn = ctk.CTkButton(
                     self.slots_frame, text=label, font=("Inter", 12),
                     fg_color=fg, hover_color=hover, state=state,
                     border_width=1, border_color="#475569", height=32
                 )
                 if state == "normal":
                     btn._base_fg_color = fg
                     btn.configure(command=lambda s=sch_str, b=btn, d=doc: self._select_slot(s, b, d))
                 
                 btn.grid(row=r, column=c, padx=4, pady=4, sticky="ew")
                 c += 1
                 if c >= 4:
                     c = 0; r += 1
                 curr += step
        conn.close()

    def _select_slot(self, sch_str, btn, doctor):
        if self._selected_slot_btn is btn:
            btn.configure(fg_color=getattr(btn, "_base_fg_color", "#1e293b"), border_color="#475569")
            self._selected_slot_btn = None
            self.selected_schedule = None
            self.slot_summary_label.configure(text="No time selected.", text_color="#fbbf24")
            return
            
        if self._selected_slot_btn:
            self._selected_slot_btn.configure(fg_color=getattr(self._selected_slot_btn, "_base_fg_color", "#1e293b"), border_color="#475569")
        
        self._selected_slot_btn = btn
        btn.configure(fg_color="#3b82f6", border_color="#3b82f6")
        self.selected_schedule = sch_str
        
        ts = datetime.strptime(sch_str, "%Y-%m-%d %H:%M").strftime("%I:%M %p")
        self.slot_summary_label.configure(text=f"Selected: {doctor} · {sch_str.split()[0]} {ts}", text_color="#10b981")

    def _is_time_available_for_two_hours(self, doctor, date_str, time_24):
         # Simplified re-check
         conn = self._connect()
         cur = conn.cursor()
         try:
             start = datetime.strptime(f"{date_str} {time_24}", "%Y-%m-%d %H:%M")
             end = start + timedelta(hours=2)
             if start < datetime.now(): return False, "Past"
             
             # Overlap check
             cur.execute("SELECT schedule FROM appointments WHERE doctor_name=? AND schedule LIKE ?", (doctor, f"{date_str} %"))
             for (ex,) in cur.fetchall():
                 est = datetime.strptime(ex, "%Y-%m-%d %H:%M")
                 een = est + timedelta(hours=2)
                 if start < een and end > est: return False, "Overlap"
             return True, ""
         except: return False, "Error"
         finally: conn.close()

    def save_appointment(self):
        doc = self.doctor_combo.get().strip()
        pat = self.patient_entry.get().strip()
        con = self.contact_entry.get().strip()
        add = self.address_entry.get().strip()
        svc = self.about_entry.get().strip()
        sch = self.selected_schedule
        note = self.notes_entry.get("1.0", "end").strip()
        
        if not (doc and pat and con and add and svc and sch):
            messagebox.showwarning("Incomplete", "Please fill all fields and select a slot.")
            return
            
        bc = "APPT-" + uuid4().hex[:10].upper()
        data = {
            "doctor": doc, "patient": pat, "contact": con, "address": add,
            "about": svc, "schedule_str": sch, "free_text": note, "barcode": bc,
            "datetime_obj": datetime.strptime(sch, "%Y-%m-%d %H:%M")
        }
        self._open_review_window(data)

    def _open_review_window(self, data):
        master = self.winfo_toplevel()
        win = ctk.CTkToplevel(master)
        win.title("Review Appointment")
        win.geometry("500x520")
        win.configure(fg_color="#0f172a")
        win.transient(master)
        win.grab_set()
        
        try:
             mx = master.winfo_rootx() + (master.winfo_width() - 500)//2
             my = master.winfo_rooty() + (master.winfo_height() - 520)//2
             win.geometry(f"+{mx}+{my}")
        except: pass

        ctk.CTkLabel(win, text="Review Details", font=("Inter", 18, "bold"), text_color="white").grid(row=0, column=0, padx=20, pady=20)
        
        card = ctk.CTkFrame(win, fg_color="#1e293b", corner_radius=12)
        card.grid(row=1, column=0, padx=40, pady=(0, 20), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=1)
        
        rows = [
            ("Patient", data["patient"]), ("Contact", data["contact"]), ("Address", data["address"]),
            ("Doctor", data["doctor"]), ("Service", data["about"]),
            ("Date", data["datetime_obj"].strftime("%b %d, %Y")), ("Time", data["datetime_obj"].strftime("%I:%M %p"))
        ]
        
        for i, (l, v) in enumerate(rows):
            ctk.CTkLabel(card, text=l, font=("Inter", 12, "bold"), text_color="#94a3b8").grid(row=i, column=0, padx=(20, 10), pady=6, sticky="e")
            ctk.CTkLabel(card, text=v, font=("Inter", 12), text_color="white").grid(row=i, column=1, padx=(10, 20), pady=6, sticky="w")
            
        b_frame = ctk.CTkFrame(card, fg_color="#0f172a", corner_radius=8)
        b_frame.grid(row=8, column=0, columnspan=2, padx=40, pady=20, sticky="ew")
        ctk.CTkLabel(b_frame, text=data["barcode"], font=("Consolas", 16, "bold"), text_color="#facc15").pack(pady=10)
        
        actions = ctk.CTkFrame(win, fg_color="transparent")
        actions.grid(row=2, column=0, padx=20, pady=20)
        
        ctk.CTkButton(actions, text="Cancel", fg_color="transparent", border_width=1, border_color="#64748b", text_color="#cbd5e1", width=100, command=win.destroy).pack(side="left", padx=10)
        ctk.CTkButton(actions, text="Confirm Booking", fg_color="#10b981", hover_color="#059669", font=("Inter", 13, "bold"), width=160, command=lambda: self._finalize(win, data)).pack(side="left")

    def _finalize(self, win, data):
        conn = self._connect()
        cur = conn.cursor()
        notes = f"Contact: {data['contact']} | Address: {data['address']} | About: {data['about']}"
        if data['free_text']: notes += f" | Notes: {data['free_text']}"
        
        try:
            cur.execute("INSERT INTO appointments (patient_name, doctor_name, schedule, notes, barcode) VALUES (?, ?, ?, ?, ?)",
                        (data['patient'], data['doctor'], data['schedule_str'], notes, data['barcode']))
            conn.commit()
            log_activity("receptionist", "receptionist", "book_appointment", f"Booked for {data['patient']}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {e}")
            return
        finally: conn.close()
        
        win.destroy()
        self._show_receipt(data)
        self._clear_form()

    def _show_receipt(self, data):
        win = ctk.CTkToplevel(self)
        win.title("Booking Confirmed")
        win.geometry("400x500")
        win.configure(fg_color="#0f172a")
        win.transient(self)
        
        try:
             mx = self.winfo_rootx() + (self.winfo_width() - 400)//2
             my = self.winfo_rooty() + (self.winfo_height() - 500)//2
             win.geometry(f"+{mx}+{my}")
        except: pass
        
        ctk.CTkLabel(win, text="✅ Booking Confirmed", font=("Inter", 18, "bold"), text_color="#10b981").pack(pady=(30, 10))
        
        info = ctk.CTkFrame(win, fg_color="#1e293b", corner_radius=10)
        info.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(info, text=f"Patient: {data['patient']}", font=("Inter", 14), text_color="white").pack(pady=5)
        ctk.CTkLabel(info, text=f"Doctor: {data['doctor']}", font=("Inter", 13), text_color="#cbd5e1").pack(pady=2)
        ctk.CTkLabel(info, text=f"Schedule: {data['schedule_str']}", font=("Inter", 13, "bold"), text_color="#3b82f6").pack(pady=10)
        ctk.CTkLabel(info, text=f"Barcode: {data['barcode']}", font=("Consolas", 14), text_color="#facc15").pack(pady=10)
        
        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        def _save_receipt():
            project_root = os.path.dirname(os.path.abspath(DB_NAME))
            receipts_dir = os.path.join(project_root, "RECEIPT_RECEPTIONIST")
            os.makedirs(receipts_dir, exist_ok=True)
            
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_bc = data['barcode'].replace(os.sep, "_")
            filename = f"booking_{safe_bc}_{ts}.bmp"
            filepath = os.path.join(receipts_dir, filename)
            
            lines = [
                "MEDISKED HOSPITAL",
                f"Date: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}",
                "---",
                "APPOINTMENT SLIP",
                "---",
                f"Booking Ref: {data['barcode']}",
                f"Patient:     {data['patient']}",
                f"Doctor:      {data['doctor']}",
                f"Schedule:    {data['schedule_str']}",
                f"Service:     {data['about']}",
                "---",
                "Please present this slip at cashier",
                "for payment processing.",
                "---",
                "Thank you!"
            ]
            
            _write_receipt_image(filepath, lines)
            messagebox.showinfo("Saved", f"Receipt saved to:\n{filepath}")
            win.destroy()

        ctk.CTkButton(btn_frame, text="Save Receipt", command=_save_receipt, width=120, fg_color="#334155").pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Close", command=win.destroy, width=80, fg_color="#ef4444").pack(side="left", padx=5)


def _write_receipt_image(filepath: str, lines: list[str]) -> None:
    """Render a receipt as a BMP image (reused logic)."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except: return

    width = 500
    height = 600
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("arial.ttf", 20)
        text_font = ImageFont.truetype("arial.ttf", 14)
        bold_font = ImageFont.truetype("arialbd.ttf", 14)
    except:
        title_font = text_font = bold_font = ImageFont.load_default()

    x = 40
    y = 40
    
    for line in lines:
        if line == "---":
            draw.line((x, y, width-x, y), fill="black")
            y += 20
        elif line == "MEDISKED HOSPITAL":
             draw.text((x, y), line, fill="black", font=title_font)
             y += 40
        elif ":" in line:
             k, v = line.split(":", 1)
             draw.text((x, y), k+":", fill="black", font=bold_font)
             bbox = draw.textbbox((0,0), k+":", font=bold_font)
             draw.text((x + (bbox[2]-bbox[0]) + 10, y), v.strip(), fill="black", font=text_font)
             y += 30
        else:
             draw.text((x, y), line, fill="black", font=text_font)
             y += 25
             
    try: img.save(filepath)
    except: pass
