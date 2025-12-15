import customtkinter as ctk
import sqlite3
import csv
import calendar
from datetime import datetime, date

from tkinter import filedialog, messagebox, Menu
from database import DB_NAME


class ReceptionistRecordsPage(ctk.CTkFrame):
    """Receptionist view of all appointment records, with rescheduling access."""

    def __init__(self, master):
        super().__init__(master, corner_radius=0, fg_color="transparent")

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header & Controls Card
        controls_card = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=16)
        controls_card.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        controls_card.grid_columnconfigure(0, weight=1)
        controls_card.grid_columnconfigure(1, weight=0)

        # Title Group
        title_frame = ctk.CTkFrame(controls_card, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=24, pady=24, sticky="ew")
        
        ctk.CTkLabel(
            title_frame, 
            text="Records", 
            font=("Inter", 20, "bold"), 
            text_color="white"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame, 
            text="Search, view, and reschedule patient appointments.", 
            font=("Inter", 13), 
            text_color="#94a3b8"
        ).pack(anchor="w", pady=(2, 0))

        # Action Buttons
        actions_frame = ctk.CTkFrame(controls_card, fg_color="transparent")
        actions_frame.grid(row=0, column=1, padx=24, pady=24, sticky="e")

        self.search_entry = ctk.CTkEntry(
            actions_frame,
            placeholder_text="Search patient or doctor...",
            width=200,
            height=36,
            corner_radius=8,
            border_width=0,
            fg_color="#334155",
            text_color="white",
            placeholder_text_color="#94a3b8"
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<Return>", lambda event: self.apply_filters())

        self.refresh_button = ctk.CTkButton(
            actions_frame,
            text="Refresh",
            width=80,
            height=36,
            corner_radius=8,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            font=("Inter", 13, "bold"),
            command=self.reload_records,
        )
        self.refresh_button.pack(side="left", padx=(0, 10))

        self.export_button = ctk.CTkButton(
            actions_frame,
            text="Export CSV",
            width=100,
            height=36,
            corner_radius=8,
            fg_color="#10b981", # Green
            hover_color="#059669",
            font=("Inter", 13, "bold"),
            command=self.export_csv,
        )
        self.export_button.pack(side="left")

        # 2. Results List Container
        list_container = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=16)
        list_container.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")
        list_container.grid_rowconfigure(1, weight=1)
        list_container.grid_columnconfigure(0, weight=1)

        # Header Row
        header_row = ctk.CTkFrame(list_container, fg_color="transparent", height=40)
        header_row.grid(row=0, column=0, sticky="ew", padx=(5, 20), pady=(10, 0))
        
        header_row.grid_columnconfigure(0, weight=0, minsize=60)  # ID
        header_row.grid_columnconfigure((1, 2, 3), weight=1, uniform="data_cols") # Patient, Doctor, Schedule
        header_row.grid_columnconfigure(4, weight=0, minsize=100) # Status
        header_row.grid_columnconfigure(5, weight=0, minsize=100) # Actions

        def _hlabel(col, text, align="w", px=10):
            ctk.CTkLabel(
                header_row, 
                text=text.upper(), 
                font=("Inter", 11, "bold"), 
                text_color="#64748b", 
                anchor=align
            ).grid(row=0, column=col, sticky="ew", padx=px)
        
        _hlabel(0, "#ID")
        _hlabel(1, "PATIENT")
        _hlabel(2, "DOCTOR")
        _hlabel(3, "SCHEDULE")
        _hlabel(4, "STATUS")
        _hlabel(5, "ACTIONS", "e")

        self.table_frame = ctk.CTkScrollableFrame(list_container, corner_radius=0, fg_color="transparent")
        self.table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(10, 10))
        self.table_frame.grid_columnconfigure(0, weight=1)

        self.records = []
        self.reload_records()

    def clear_filters(self):
        self.search_entry.delete(0, "end")
        self.apply_filters()

    def reload_records(self):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        # Fetch fields needed for display + editing: id, patient, doctor, schedule, notes, barcode, is_paid, amount_paid
        cur.execute(
            """
            SELECT id, patient_name, doctor_name, schedule, notes, barcode, COALESCE(is_paid, 0), COALESCE(amount_paid, 0) 
            FROM appointments ORDER BY id DESC
            """
        )
        self.records = cur.fetchall()
        conn.close()
        self.apply_filters()

    def get_filtered_records(self):
        query = self.search_entry.get().strip().lower()
        filtered = []
        for rec in self.records:
            rid, patient, doctor, schedule, notes, barcode, is_paid, amount = rec
            haystack = f"{patient} {doctor} {barcode or ''}".lower()
            if query and query not in haystack:
                continue
            filtered.append(rec)
        return filtered

    def apply_filters(self):
        for child in self.table_frame.winfo_children():
            child.destroy()

        filtered = self.get_filtered_records()

        for row_index, rec in enumerate(filtered):
            rid, patient, doctor, schedule, notes, barcode, is_paid, amount = rec
            
            row_frame = ctk.CTkFrame(
                self.table_frame, 
                corner_radius=8,
                fg_color="#334155", 
                border_width=1,
                border_color="#475569",
                height=50
            ) 
            row_frame.grid(row=row_index, column=0, sticky="ew", pady=5, padx=5)
            
            row_frame.grid_columnconfigure(0, weight=0, minsize=60)
            row_frame.grid_columnconfigure((1, 2, 3), weight=1, uniform="data_cols")
            row_frame.grid_columnconfigure(4, weight=0, minsize=100)
            row_frame.grid_columnconfigure(5, weight=0, minsize=100)

            # ID
            ctk.CTkLabel(row_frame, text=str(rid), font=("Inter", 12), text_color="#cbd5e1", anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=10)
            
            # Patient
            ctk.CTkLabel(row_frame, text=patient, font=("Inter", 13, "bold"), text_color="white", anchor="w").grid(row=0, column=1, sticky="ew", padx=10)
            
            # Doctor
            ctk.CTkLabel(row_frame, text=f"Dr. {doctor}", font=("Inter", 13), text_color="#94a3b8", anchor="w").grid(row=0, column=2, sticky="ew", padx=10)
            
            # Schedule
            pretty_schedule = self._format_schedule(schedule)
            ctk.CTkLabel(row_frame, text=pretty_schedule, font=("Inter", 12), text_color="#cbd5e1", anchor="w").grid(row=0, column=3, sticky="ew", padx=10)
            
            # Status
            status_text = "PAID" if is_paid else "UNPAID"
            status_color = "#10b981" if is_paid else "#ef4444" 
            ctk.CTkLabel(row_frame, text=status_text, font=("Inter", 11, "bold"), text_color=status_color, anchor="w").grid(row=0, column=4, sticky="ew", padx=10)

            # Actions
            actions_panel = ctk.CTkFrame(row_frame, fg_color="transparent")
            actions_panel.grid(row=0, column=5, sticky="e", padx=10)

            def _action_btn(txt, color, cmd):
                return ctk.CTkButton(
                    actions_panel,
                    text=txt,
                    width=40,
                    height=24,
                    font=("Inter", 11),
                    fg_color="transparent",
                    border_width=1,
                    border_color=color,
                    text_color=color,
                    hover_color=("#1e293b", "#0f172a"),
                    command=cmd
                )

            view_btn = _action_btn("View", "#3b82f6", lambda r=rec: self._view_details(r))
            view_btn.pack(side="left", padx=2)

            edit_btn = _action_btn("Edit", "#10b981", lambda r=rec: self._edit_record(r))
            edit_btn.pack(side="left", padx=2)

            # Separator inside
            ctk.CTkFrame(row_frame, height=1, fg_color="#334155").place(relx=0, rely=0.98, relwidth=1.0)


    def _format_schedule(self, schedule_str: str) -> str:
        try:
            dt = datetime.strptime(schedule_str, "%Y-%m-%d %H:%M")
            return dt.strftime("%b %d, %I:%M %p")
        except Exception:
            return schedule_str

    def _view_details(self, record):
        rid, patient, doctor, schedule, notes, barcode, is_paid, amount = record

        win = ctk.CTkToplevel(self)
        win.title("Appointment Details")
        win.geometry("500x600")
        win.transient(self)
        win.grab_set()
        
        win.update_idletasks()
        try:
            x = self.winfo_rootx() + (self.winfo_width() - 500) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 600) // 2
            win.geometry(f"+{x}+{y}")
        except: pass
        
        win.configure(fg_color="#0f172a")

        ctk.CTkLabel(win, text="Appointment Details", font=("Inter", 20, "bold"), text_color="white").pack(padx=24, pady=(24, 4), anchor="w")
        ctk.CTkLabel(win, text=f"ID: #{rid}", font=("Inter", 13), text_color="#64748b").pack(padx=24, pady=(0, 24), anchor="w")

        content = ctk.CTkFrame(win, fg_color="#1e293b", corner_radius=12)
        content.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        def _row(label, val, col=None):
            f = ctk.CTkFrame(content, fg_color="transparent")
            f.pack(fill="x", padx=16, pady=8)
            ctk.CTkLabel(f, text=label, font=("Inter", 13, "bold"), text_color="#94a3b8", width=100, anchor="w").pack(side="left")
            ctk.CTkLabel(f, text=val, font=("Inter", 13), text_color=col if col else "white", wraplength=300, justify="left", anchor="w").pack(side="left", fill="x", expand=True)

        _row("Patient", patient)
        _row("Doctor", doctor)
        _row("Schedule", self._format_schedule(schedule))
        
        status_txt = "PAID" if is_paid else "UNPAID"
        status_c = "#10b981" if is_paid else "#ef4444"
        _row("Status", status_txt, status_c)
        _row("Amount", f"₱{amount:,.2f}" if amount else "-")

        # Parsing Notes
        raw = notes or ""
        parsed_notes = ""
        meta = {}
        for p in [x.strip() for x in raw.split("|") if x.strip()]:
            if ":" in p:
                k, v = p.split(":", 1)
                meta[k.strip()] = v.strip()
            else:
                parsed_notes += p + " "
        
        if "Contact" in meta: _row("Contact", meta["Contact"])
        if "Address" in meta: _row("Address", meta["Address"])
        if "About" in meta: _row("About", meta["About"])
        if "Notes" in meta: parsed_notes += meta["Notes"]
        
        _row("Notes", parsed_notes.strip() or "-")

        # Barcode
        b_frame = ctk.CTkFrame(content, fg_color="#0f172a", corner_radius=8)
        b_frame.pack(fill="x", padx=16, pady=20)
        ctk.CTkLabel(b_frame, text=barcode or "(no barcode)", font=("Consolas", 14, "bold"), text_color="#facc15" if barcode else "gray").pack(pady=10)

        ctk.CTkButton(win, text="Close", font=("Inter", 13), fg_color="#334155", hover_color="#475569", command=win.destroy).pack(pady=(0, 24))


    def _edit_record(self, record):
        """Rescheduling implementation."""
        rid, patient, doctor, schedule, notes, barcode, is_paid, amount = record

        win = ctk.CTkToplevel(self)
        win.title(f"Edit Appointment #{rid}")
        win.geometry("700x800")
        win.transient(self)
        win.grab_set()
        win.configure(fg_color="#0f172a")

        win.update_idletasks()
        try:
            x = self.winfo_rootx() + (self.winfo_width() - 700) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 800) // 2
            win.geometry(f"+{x}+{y}")
        except: pass

        win.grid_columnconfigure(1, weight=1)
        win.grid_rowconfigure(9, weight=1) # Spacer row

        # Parse schedule
        try:
            current_dt = datetime.strptime(schedule, "%Y-%m-%d %H:%M")
            current_date_str = current_dt.strftime("%Y-%m-%d")
        except:
            current_date_str = schedule.split()[0] if schedule else ""

        # Styles
        lbl_font = ("Inter", 13)
        input_bg = "#1e293b"
        input_border = "#334155"

        ctk.CTkLabel(win, text="Reschedule / Edit", font=("Inter", 20, "bold"), text_color="white").grid(row=0, column=0, columnspan=2, padx=24, pady=24, sticky="w")

        # Patient
        ctk.CTkLabel(win, text="Patient", font=lbl_font, text_color="#94a3b8").grid(row=1, column=0, padx=24, pady=8, sticky="w")
        patient_entry = ctk.CTkEntry(win, fg_color=input_bg, border_color=input_border, text_color="white")
        patient_entry.insert(0, patient)
        patient_entry.grid(row=1, column=1, padx=24, pady=8, sticky="ew")

        # Doctor
        ctk.CTkLabel(win, text="Doctor", font=lbl_font, text_color="#94a3b8").grid(row=2, column=0, padx=24, pady=8, sticky="w")
        doctor_combo = ctk.CTkComboBox(win, state="readonly", fg_color=input_bg, border_color=input_border, text_color="white", dropdown_fg_color=input_bg)
        
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT name FROM doctors WHERE status = 'active' ORDER BY name")
        doctor_names = [row[0] for row in cur.fetchall()]
        conn.close()
        
        if doctor_names:
            doctor_combo.configure(values=doctor_names)
            doctor_combo.set(doctor if doctor in doctor_names else doctor_names[0])
        else:
            doctor_combo.set("No doctors")

        doctor_combo.grid(row=2, column=1, padx=24, pady=8, sticky="ew")

        # Date
        ctk.CTkLabel(win, text="Date", font=lbl_font, text_color="#94a3b8").grid(row=3, column=0, padx=24, pady=8, sticky="w")
        date_row = ctk.CTkFrame(win, fg_color="transparent")
        date_row.grid(row=3, column=1, padx=24, pady=8, sticky="ew")
        date_row.grid_columnconfigure(0, weight=1)
        
        date_entry = ctk.CTkEntry(date_row, fg_color=input_bg, border_color=input_border, text_color="white")
        if current_date_str: date_entry.insert(0, current_date_str)
        date_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        def _open_calendar():
            # (Simplified calendar popup integration)
            top = ctk.CTkToplevel(win)
            top.title("Pick Date")
            top.geometry("300x320")
            top.configure(fg_color="#1e293b")
            top.transient(win)
            
            cal_frame = ctk.CTkFrame(top, fg_color="transparent")
            cal_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            cal = calendar.Calendar()
            today = date.today()
            yr, mo = today.year, today.month
            
            def _draw(y, m):
                for w in cal_frame.winfo_children(): w.destroy()
                ctk.CTkLabel(cal_frame, text=f"{calendar.month_name[m]} {y}", font=("Inter", 14, "bold"), text_color="white").pack(pady=5)
                
                days = ctk.CTkFrame(cal_frame, fg_color="transparent")
                days.pack()
                # Headers
                for col, dname in enumerate(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]):
                    ctk.CTkLabel(days, text=dname, width=30, text_color="#94a3b8").grid(row=0, column=col)
                
                for r, week in enumerate(cal.monthdayscalendar(y, m)):
                    for c, d in enumerate(week):
                        if d == 0: continue
                        btn = ctk.CTkButton(days, text=str(d), width=30, height=30, fg_color="#334155", hover_color="#3b82f6", command=lambda d=d: _set(y, m, d))
                        btn.grid(row=r+1, column=c, padx=2, pady=2)
            
            def _set(y, m, d):
                date_entry.delete(0, "end")
                date_entry.insert(0, f"{y:04d}-{m:02d}-{d:02d}")
                top.destroy()
                load_slots()

            _draw(yr, mo)

        ctk.CTkButton(date_row, text="📅", width=40, fg_color="#334155", command=_open_calendar).grid(row=0, column=1)

        # Slots
        ctk.CTkLabel(win, text="Available Slots", font=lbl_font, text_color="#94a3b8").grid(row=4, column=0, padx=24, pady=8, sticky="nw")
        slots_frame = ctk.CTkScrollableFrame(win, height=120, fg_color="#1e293b", corner_radius=8)
        slots_frame.grid(row=4, column=1, padx=24, pady=8, sticky="ew")

        selected_schedule = {"value": schedule}

        def load_slots():
            for c in slots_frame.winfo_children(): c.destroy()
            
            doc = doctor_combo.get()
            d_str = date_entry.get()
            if not doc or not d_str: return

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("SELECT id FROM doctors WHERE name=? AND status='active'", (doc,))
            row = cur.fetchone()
            if not row: conn.close(); return
            did = row[0]

            cur.execute("SELECT start_time, end_time, slot_length_minutes FROM doctor_availability WHERE doctor_id=? AND date=? AND is_available=1 AND start_time IS NOT NULL ORDER BY start_time", (did, d_str))
            avails = cur.fetchall()
            
            from datetime import timedelta
            row_idx, col_idx = 0, 0
            
            for s, e, slen in avails:
                try:
                    s_dt = datetime.strptime(f"{d_str} {s}", "%Y-%m-%d %H:%M")
                    e_dt = datetime.strptime(f"{d_str} {e}", "%Y-%m-%d %H:%M")
                except: continue
                
                curr = s_dt
                step = slen if slen else 30 
                
                while curr < e_dt:
                    slot_str = curr.strftime("%Y-%m-%d %H:%M")
                    # Check overlap (excluding self)
                    cur.execute("SELECT COUNT(*) FROM appointments WHERE doctor_name=? AND schedule=? AND id!=?", (doc, slot_str, rid))
                    busy = cur.fetchone()[0] > 0
                    
                    btn_txt = curr.strftime("%H:%M")
                    
                    if not busy:
                        def _pick(ss=slot_str, b=None):
                            selected_schedule["value"] = ss
                            # Visual update
                            for child in slots_frame.winfo_children():
                                if getattr(child, "_is_slot", False):
                                   child.configure(fg_color="#10b981")
                            if b: b.configure(fg_color="#3b82f6")

                        btn = ctk.CTkButton(slots_frame, text=btn_txt, width=80, height=30, fg_color="#10b981", hover_color="#059669")
                        btn.configure(command=lambda s=slot_str, b=btn: _pick(s, b))
                        btn._is_slot = True
                    else:
                        btn = ctk.CTkButton(slots_frame, text=btn_txt, width=80, height=30, fg_color="#334155", state="disabled")
                    
                    btn.grid(row=row_idx, column=col_idx, padx=4, pady=4)
                    col_idx += 1
                    if col_idx > 3: 
                        col_idx=0; row_idx+=1
                    
                    curr += timedelta(minutes=step)

            conn.close()

        doctor_combo.configure(command=lambda x: load_slots())
        # Manual trigger
        load_slots()

        # Parse meta notes again
        raw_meta = notes or ""
        meta = {}
        curr_notes = ""
        for p in raw_meta.split("|"):
            if ":" in p:
                k, v = p.split(":", 1)
                meta[k.strip()] = v.strip()
            else:
                curr_notes += p + " "

        ctk.CTkLabel(win, text="Contact", font=lbl_font, text_color="#94a3b8").grid(row=5, column=0, padx=24, pady=8, sticky="w")
        contact_entry = ctk.CTkEntry(win, fg_color=input_bg, border_color=input_border, text_color="white")
        contact_entry.insert(0, meta.get("Contact", ""))
        contact_entry.grid(row=5, column=1, padx=24, pady=8, sticky="ew")

        ctk.CTkLabel(win, text="Address", font=lbl_font, text_color="#94a3b8").grid(row=6, column=0, padx=24, pady=8, sticky="w")
        addr_entry = ctk.CTkEntry(win, fg_color=input_bg, border_color=input_border, text_color="white")
        addr_entry.insert(0, meta.get("Address", ""))
        addr_entry.grid(row=6, column=1, padx=24, pady=8, sticky="ew")
        
        ctk.CTkLabel(win, text="About", font=lbl_font, text_color="#94a3b8").grid(row=7, column=0, padx=24, pady=8, sticky="w")
        about_entry = ctk.CTkEntry(win, fg_color=input_bg, border_color=input_border, text_color="white")
        about_entry.insert(0, meta.get("About", ""))
        about_entry.grid(row=7, column=1, padx=24, pady=8, sticky="ew")

        ctk.CTkLabel(win, text="Notes", font=lbl_font, text_color="#94a3b8").grid(row=8, column=0, padx=24, pady=8, sticky="nw")
        notes_entry = ctk.CTkTextbox(win, height=80, fg_color=input_bg, border_color=input_border, text_color="white")
        notes_entry.insert("1.0", (meta.get("Notes", "") + curr_notes).strip())
        notes_entry.grid(row=8, column=1, padx=24, pady=8, sticky="ew")

        def save():
            p = patient_entry.get().strip()
            d = doctor_combo.get()
            s = selected_schedule["value"]
            if not p or not d or not s:
                messagebox.showerror("Error", "Missing fields")
                return

            # Rebuild notes
            parts = []
            c = contact_entry.get().strip()
            a = addr_entry.get().strip()
            ab = about_entry.get().strip()
            n = notes_entry.get("1.0", "end").strip()
            if c: parts.append(f"Contact: {c}")
            if a: parts.append(f"Address: {a}")
            if ab: parts.append(f"About: {ab}")
            if n: parts.append(f"Notes: {n}")
            final_notes = " | ".join(parts)

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("UPDATE appointments SET patient_name=?, doctor_name=?, schedule=?, notes=?, is_rescheduled=1 WHERE id=?", (p, d, s, final_notes, rid))
            conn.commit()
            conn.close()
            win.destroy()
            self.reload_records()

        ctk.CTkButton(win, text="Save Changes", fg_color="#10b981", hover_color="#059669", font=("Inter", 13, "bold"), command=save).grid(row=10, column=0, columnspan=2, pady=24)

    def export_csv(self):
        filtered = self.get_filtered_records()
        if not filtered:
            messagebox.showinfo("Export", "No records.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not file_path: return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Patient", "Doctor", "Schedule", "Status", "Amount", "Barcode", "Notes"])
                for r in filtered:
                     writer.writerow([r[0], r[1], r[2], r[3], "PAID" if r[6] else "UNPAID", r[7], r[5], r[4]])
            messagebox.showinfo("Success", "Export successful.")
        except Exception as e:
            messagebox.showerror("Error", str(e))
