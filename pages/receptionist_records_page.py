import customtkinter as ctk
import sqlite3
import csv
import calendar
from datetime import datetime, date

from tkinter import filedialog, messagebox, Menu
from database import DB_NAME


class ReceptionistRecordsPage(ctk.CTkFrame):
    """Receptionist view of all appointment records, with full rescheduling access.

    UI is similar to the Admin records page: search, refresh, clear, optional CSV export,
    and a table with VIEW / EDIT actions.
    """

    def __init__(self, master):
        super().__init__(master, corner_radius=0)

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=30, pady=(30, 10), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)

        title = ctk.CTkLabel(
            header_frame,
            text="Records",
            font=("Segoe UI", 24, "bold"),
        )
        title.grid(row=0, column=0, sticky="w")

        subtitle = ctk.CTkLabel(
            header_frame,
            text="Search, view, and reschedule patient appointments.",
            font=("Segoe UI", 14),
        )
        subtitle.grid(row=1, column=0, pady=(4, 0), sticky="w")

        controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=1, rowspan=2, padx=(20, 0), sticky="e")
        controls_frame.grid_columnconfigure(0, weight=0)
        controls_frame.grid_columnconfigure(1, weight=0)
        controls_frame.grid_columnconfigure(2, weight=0)

        self.search_entry = ctk.CTkEntry(
            controls_frame,
            placeholder_text="Search patient or doctor...",
            width=160,
        )
        self.search_entry.grid(row=0, column=0, padx=(0, 10))

        self.refresh_button = ctk.CTkButton(
            controls_frame,
            text="Refresh",
            width=80,
            fg_color="#16a34a",
            hover_color="#15803d",
            command=self.reload_records,
        )
        self.refresh_button.grid(row=0, column=1)

        self.clear_button = ctk.CTkButton(
            controls_frame,
            text="Clear",
            width=70,
            fg_color="#4b5563",
            hover_color="#374151",
            command=self.clear_filters,
        )
        self.clear_button.grid(row=0, column=2, padx=(10, 0))

        self.export_button = ctk.CTkButton(
            controls_frame,
            text="Export CSV",
            width=90,
            command=self.export_csv,
        )
        self.export_button.grid(row=0, column=3, padx=(10, 0))

        table_container = ctk.CTkFrame(self, corner_radius=10)
        table_container.grid(row=1, column=0, padx=30, pady=(0, 30), sticky="nsew")
        table_container.grid_rowconfigure(1, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        header_row = ctk.CTkFrame(table_container, fg_color="transparent")
        header_row.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        header_row.grid_columnconfigure(0, weight=1)
        header_row.grid_columnconfigure(1, weight=1)
        header_row.grid_columnconfigure(2, weight=1)
        header_row.grid_columnconfigure(3, weight=1)
        header_row.grid_columnconfigure(4, weight=2)
        header_row.grid_columnconfigure(5, weight=1)

        id_header = ctk.CTkLabel(header_row, text="ID", font=("Segoe UI", 13, "bold"))
        id_header.grid(row=0, column=0, sticky="w")

        patient_header = ctk.CTkLabel(
            header_row,
            text="Patient",
            font=("Segoe UI", 13, "bold"),
        )
        patient_header.grid(row=0, column=1, sticky="w")

        doctor_header = ctk.CTkLabel(
            header_row,
            text="Doctor",
            font=("Segoe UI", 13, "bold"),
        )
        doctor_header.grid(row=0, column=2, sticky="w")

        schedule_header = ctk.CTkLabel(
            header_row,
            text="Schedule",
            font=("Segoe UI", 13, "bold"),
        )
        schedule_header.grid(row=0, column=3, sticky="w")

        notes_header = ctk.CTkLabel(
            header_row,
            text="Notes",
            font=("Segoe UI", 13, "bold"),
        )
        notes_header.grid(row=0, column=4, sticky="w", padx=(0, 5))

        actions_header = ctk.CTkLabel(
            header_row,
            text="Actions",
            font=("Segoe UI", 13, "bold"),
        )
        actions_header.grid(row=0, column=5, sticky="w")

        self.table_frame = ctk.CTkScrollableFrame(table_container, corner_radius=10)
        self.table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        self.table_frame.grid_columnconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(1, weight=1)
        self.table_frame.grid_columnconfigure(2, weight=1)
        self.table_frame.grid_columnconfigure(3, weight=1)
        self.table_frame.grid_columnconfigure(4, weight=2)
        self.table_frame.grid_columnconfigure(5, weight=1)

        self.records = []
        self.reload_records()

        self.search_entry.bind("<Return>", lambda event: self.apply_filters())

    def clear_filters(self):
        self.search_entry.delete(0, "end")
        self.apply_filters()

    def reload_records(self):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Include barcode so we can show/copy it in the details dialog
        cur.execute(
            "SELECT id, patient_name, doctor_name, schedule, notes, barcode FROM appointments ORDER BY id ASC"
        )
        self.records = cur.fetchall()

        conn.close()
        self.apply_filters()

    def get_filtered_records(self):
        query = self.search_entry.get().strip().lower()

        filtered = []
        for rec in self.records:
            rid, patient, doctor, schedule, notes, barcode = rec
            haystack = f"{patient} {doctor}".lower()
            if query and query not in haystack:
                continue
            filtered.append(rec)
        return filtered

    def apply_filters(self):
        for child in self.table_frame.winfo_children():
            child.destroy()

        filtered = self.get_filtered_records()

        for row_index, rec in enumerate(filtered):
            rid, patient, doctor, schedule, notes, barcode = rec

            row_widgets = []

            id_label = ctk.CTkLabel(self.table_frame, text=str(rid), anchor="w")
            id_label.grid(row=row_index, column=0, sticky="ew", padx=(0, 5), pady=2)
            row_widgets.append(id_label)

            patient_label = ctk.CTkLabel(
                self.table_frame,
                text=patient,
                anchor="w",
            )
            patient_label.grid(row=row_index, column=1, sticky="ew", padx=(0, 5), pady=2)
            row_widgets.append(patient_label)

            doctor_label = ctk.CTkLabel(
                self.table_frame,
                text=doctor,
                anchor="w",
            )
            doctor_label.grid(row=row_index, column=2, sticky="ew", padx=(0, 5), pady=2)
            row_widgets.append(doctor_label)

            # Format schedule to 12-hour human readable form
            pretty_schedule = self._format_schedule(schedule)

            schedule_label = ctk.CTkLabel(
                self.table_frame,
                text=pretty_schedule,
                anchor="w",
            )
            schedule_label.grid(row=row_index, column=3, sticky="ew", padx=(0, 5), pady=2)
            row_widgets.append(schedule_label)

            notes_text = (notes or "").replace("\n", " ")
            if len(notes_text) > 80:
                notes_text = notes_text[:77] + "..."
            notes_label = ctk.CTkLabel(
                self.table_frame,
                text=notes_text,
                anchor="w",
            )
            notes_label.grid(row=row_index, column=4, sticky="ew", padx=(0, 5), pady=2)
            row_widgets.append(notes_label)

            # Actions column with VIEW (blue) and EDIT (green)
            actions_frame = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            actions_frame.grid(row=row_index, column=5, sticky="e", padx=(0, 5), pady=2)

            view_btn = ctk.CTkButton(
                actions_frame,
                text="VIEW",
                width=40,
                height=24,
                fg_color="#0d74d1",
                hover_color="#0b63b3",
                command=lambda r=rec: self._view_details(r),
            )
            view_btn.grid(row=0, column=0, padx=(0, 4))

            edit_btn = ctk.CTkButton(
                actions_frame,
                text="EDIT",
                width=40,
                height=24,
                fg_color="#1c9b3b",
                hover_color="#178533",
                command=lambda r=rec: self._edit_record(r),
            )
            edit_btn.grid(row=0, column=1, padx=(0, 0))

            row_widgets.extend([actions_frame, view_btn, edit_btn])

            for widget in row_widgets:
                widget.bind(
                    "<Button-3>",
                    lambda event, record=rec: self._show_row_menu(event, record),
                )

    def _show_row_menu(self, event, record):
        menu = Menu(self, tearoff=0)
        menu.add_command(
            label="View details",
            command=lambda r=record: self._view_details(r),
        )
        menu.add_command(
            label="Edit",
            command=lambda r=record: self._edit_record(r),
        )

        menu.tk_popup(event.x_root, event.y_root)

    def _format_schedule(self, schedule_str: str) -> str:
        """Return schedule string in a friendly 12-hour format if possible.

        Expects something like "YYYY-MM-DD HH:MM". Falls back to original if parsing fails.
        """
        try:
            dt = datetime.strptime(schedule_str, "%Y-%m-%d %H:%M")
            return dt.strftime("%b %d, %Y %I:%M %p")
        except Exception:
            return schedule_str

    def _view_details(self, record):
        rid, patient, doctor, schedule, notes, barcode = record

        win = ctk.CTkToplevel(self)
        win.title(f"Appointment #{rid}")
        win.geometry("420x320")

        # Make sure window is on top and modal-like
        win.transient(self)
        win.grab_set()
        win.focus()

        # Center over parent
        self.update_idletasks()
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()
        win_w = 400
        win_h = 260
        x = parent_x + (parent_w - win_w) // 2
        y = parent_y + (parent_h - win_h) // 2
        win.geometry(f"{win_w}x{win_h}+{x}+{y}")

        win.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(win, text="Patient:").grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        ctk.CTkLabel(win, text=patient).grid(row=0, column=1, padx=20, pady=(20, 5), sticky="w")

        ctk.CTkLabel(win, text="Doctor:").grid(row=1, column=0, padx=20, pady=5, sticky="w")
        ctk.CTkLabel(win, text=doctor).grid(row=1, column=1, padx=20, pady=5, sticky="w")

        ctk.CTkLabel(win, text="Schedule:").grid(row=2, column=0, padx=20, pady=5, sticky="w")
        ctk.CTkLabel(win, text=self._format_schedule(schedule)).grid(
            row=2,
            column=1,
            padx=20,
            pady=5,
            sticky="w",
        )

        # Barcode row with copy button
        ctk.CTkLabel(win, text="Barcode:").grid(row=3, column=0, padx=20, pady=5, sticky="w")
        barcode_row = ctk.CTkFrame(win, fg_color="transparent")
        barcode_row.grid(row=3, column=1, padx=20, pady=5, sticky="ew")
        barcode_row.grid_columnconfigure(0, weight=1)

        barcode_text = barcode or "(none)"
        barcode_entry = ctk.CTkEntry(barcode_row)
        barcode_entry.insert(0, barcode_text)
        barcode_entry.configure(state="readonly")
        barcode_entry.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        def _copy_barcode():
            # Copy raw barcode value (empty string if None)
            value = barcode or ""
            win.clipboard_clear()
            win.clipboard_append(value)

        copy_btn = ctk.CTkButton(barcode_row, text="Copy", width=60, command=_copy_barcode)
        copy_btn.grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(win, text="Notes:").grid(row=4, column=0, padx=20, pady=5, sticky="nw")
        notes_text = notes or ""
        notes_label = ctk.CTkLabel(win, text=notes_text, justify="left")
        notes_label.grid(row=4, column=1, padx=20, pady=5, sticky="w")

        close_btn = ctk.CTkButton(win, text="Close", command=win.destroy)
        close_btn.grid(row=5, column=0, columnspan=2, pady=(20, 20))

    def _edit_record(self, record):
        """Edit an appointment, including rescheduling via doctor/date/slot selection."""
        rid, patient, doctor, schedule, notes = record

        win = ctk.CTkToplevel(self)
        win.title(f"Edit Appointment #{rid}")
        win.geometry("520x420")

        # Make sure window is on top and modal-like
        win.transient(self)
        win.grab_set()
        win.focus()

        # Center over parent
        self.update_idletasks()
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()
        win_w = 520
        win_h = 420
        x = parent_x + (parent_w - win_w) // 2
        y = parent_y + (parent_h - win_h) // 2
        win.geometry(f"{win_w}x{win_h}+{x}+{y}")

        win.grid_columnconfigure(1, weight=1)

        # Parse existing schedule into date/time
        try:
            current_dt = datetime.strptime(schedule, "%Y-%m-%d %H:%M")
            current_date_str = current_dt.strftime("%Y-%m-%d")
        except Exception:
            parts = schedule.split()
            current_date_str = parts[0] if parts else ""

        ctk.CTkLabel(win, text="Patient").grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        patient_entry = ctk.CTkEntry(win)
        patient_entry.insert(0, patient)
        patient_entry.grid(row=0, column=1, padx=20, pady=(20, 5), sticky="ew")

        # Doctor selection
        ctk.CTkLabel(win, text="Doctor").grid(row=1, column=0, padx=20, pady=5, sticky="w")
        doctor_combo = ctk.CTkComboBox(win, state="readonly")
        # Load doctors list
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT name FROM doctors WHERE status = 'active' ORDER BY name")
        doctor_names = [row[0] for row in cur.fetchall()]
        conn.close()
        if doctor_names:
            doctor_combo.configure(values=doctor_names)
            if doctor in doctor_names:
                doctor_combo.set(doctor)
            else:
                doctor_combo.set(doctor_names[0])
        else:
            doctor_combo.configure(values=["No doctors"], state="disabled")
            doctor_combo.set("No doctors")
        doctor_combo.grid(row=1, column=1, padx=20, pady=5, sticky="ew")

        # Date entry + calendar picker button
        ctk.CTkLabel(win, text="Date").grid(row=2, column=0, padx=20, pady=5, sticky="w")
        date_row = ctk.CTkFrame(win, fg_color="transparent")
        date_row.grid(row=2, column=1, padx=20, pady=5, sticky="ew")
        date_row.grid_columnconfigure(0, weight=1)

        date_entry = ctk.CTkEntry(date_row)
        if current_date_str:
            date_entry.insert(0, current_date_str)
        date_entry.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        def _open_date_picker():
            """Small calendar popup to pick a date for rescheduling."""
            # Determine initial year/month
            try:
                base_date = datetime.strptime(date_entry.get().strip(), "%Y-%m-%d").date()
            except Exception:
                base_date = date.today()

            year = base_date.year
            month = base_date.month

            dp = ctk.CTkToplevel(win)
            dp.title("Select date")
            dp.geometry("260x280")
            dp.resizable(False, False)
            dp.transient(win)
            dp.grab_set()

            dp.grid_columnconfigure(0, weight=1)

            header = ctk.CTkFrame(dp)
            header.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")
            header.grid_columnconfigure(1, weight=1)

            month_label = ctk.CTkLabel(header, text="")
            month_label.grid(row=0, column=1, sticky="ew")

            def rebuild():
                for child in body.winfo_children():
                    child.destroy()
                month_label.configure(text=f"{calendar.month_name[month]} {year}")

                # Weekday headers
                for i, wd in enumerate(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]):
                    lbl = ctk.CTkLabel(body, text=wd)
                    lbl.grid(row=0, column=i, pady=(0, 4))

                cal = calendar.Calendar(firstweekday=0)
                today_str = date.today().strftime("%Y-%m-%d")
                row_idx = 1
                for week in cal.monthdayscalendar(year, month):
                    for col_idx, day_num in enumerate(week):
                        if day_num == 0:
                            continue
                        d_str = f"{year:04d}-{month:02d}-{day_num:02d}"

                        # Disable past dates
                        is_past = d_str < today_str
                        fg = "#555555" if is_past else "#1c9b3b"
                        hover = fg if is_past else "#17a349"
                        state = "disabled" if is_past else "normal"

                        def _pick(ds=d_str):
                            date_entry.delete(0, "end")
                            date_entry.insert(0, ds)
                            load_slots_for_selection()
                            dp.destroy()

                        btn = ctk.CTkButton(
                            body,
                            text=str(day_num),
                            width=26,
                            height=24,
                            fg_color=fg,
                            hover_color=hover,
                            state=state,
                            command=(None if is_past else _pick),
                        )
                        btn.grid(row=row_idx, column=col_idx, padx=2, pady=2, sticky="nsew")
                    row_idx += 1

            def prev_month():
                nonlocal year, month
                if month == 1:
                    month = 12
                    year -= 1
                else:
                    month -= 1
                rebuild()

            def next_month():
                nonlocal year, month
                if month == 12:
                    month = 1
                    year += 1
                else:
                    month += 1
                rebuild()

            prev_btn = ctk.CTkButton(header, text="<", width=24, command=prev_month)
            prev_btn.grid(row=0, column=0, padx=(0, 4))
            next_btn = ctk.CTkButton(header, text=">", width=24, command=next_month)
            next_btn.grid(row=0, column=2, padx=(4, 0))

            body = ctk.CTkFrame(dp)
            body.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
            for c in range(7):
                body.grid_columnconfigure(c, weight=1)

            rebuild()

            # Center over the edit window
            dp.update_idletasks()
            win.update_idletasks()
            wx = win.winfo_rootx()
            wy = win.winfo_rooty()
            ww = win.winfo_width()
            wh = win.winfo_height()
            dw = dp.winfo_width()
            dh = dp.winfo_height()
            x = wx + (ww - dw) // 2
            y = wy + (wh - dh) // 2
            dp.geometry(f"{dw}x{dh}+{x}+{y}")

        date_picker_btn = ctk.CTkButton(date_row, text="📅", width=32, command=_open_date_picker)
        date_picker_btn.grid(row=0, column=1, sticky="e")

        # Available slots area
        ctk.CTkLabel(win, text="Available time slots").grid(row=3, column=0, padx=20, pady=(10, 2), sticky="w")
        slots_frame = ctk.CTkFrame(win, corner_radius=8)
        slots_frame.grid(row=3, column=1, padx=20, pady=(4, 8), sticky="nsew")
        slots_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        win.grid_rowconfigure(3, weight=1)

        selected_schedule = {"value": schedule}

        def load_slots_for_selection():
            # Clear previous
            for child in slots_frame.winfo_children():
                child.destroy()

            doc_name = doctor_combo.get().strip()
            date_str = date_entry.get().strip()
            if not doc_name or not date_str:
                return

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # Find doctor id
            cur.execute("SELECT id FROM doctors WHERE name = ? AND status = 'active'", (doc_name,))
            row = cur.fetchone()
            if not row:
                conn.close()
                return
            doctor_id = row[0]

            # Fetch availability for that day
            cur.execute(
                """
                SELECT start_time, end_time, max_appointments, slot_length_minutes
                FROM doctor_availability
                WHERE doctor_id = ? AND date = ? AND is_available = 1 AND start_time IS NOT NULL
                ORDER BY start_time
                """,
                (doctor_id, date_str),
            )
            slots = cur.fetchall()

            from datetime import timedelta as _td

            row_idx = 0
            col_idx = 0
            for start_t, end_t, max_appt, slot_len in slots:
                try:
                    start_dt = datetime.strptime(f"{date_str} {start_t}", "%Y-%m-%d %H:%M")
                    end_dt = datetime.strptime(f"{date_str} {end_t}", "%Y-%m-%d %H:%M")
                except ValueError:
                    continue

                step = int(slot_len) if slot_len else 30
                current_dt = start_dt
                while current_dt < end_dt:
                    slot_end_dt = current_dt + _td(minutes=step)
                    if slot_end_dt > end_dt:
                        slot_end_dt = end_dt

                    schedule_str = current_dt.strftime("%Y-%m-%d %H:%M")

                    # Check if this time already has another appointment (ignore this same record)
                    cur.execute(
                        "SELECT COUNT(*) FROM appointments WHERE doctor_name = ? AND schedule = ? AND id != ?",
                        (doc_name, schedule_str, rid),
                    )
                    count = cur.fetchone()[0]

                    full = count >= 1
                    pretty_start = current_dt.strftime("%I:%M %p")
                    pretty_end = slot_end_dt.strftime("%I:%M %p")
                    label_text = f"{pretty_start} - {pretty_end}"

                    fg = "#555555" if full else "#0d74d1"
                    hover = fg
                    if not full:
                        hover = "#0b63b3"

                    btn = ctk.CTkButton(
                        slots_frame,
                        text=label_text,
                        width=120,
                        height=26,
                        state="disabled" if full else "normal",
                        fg_color=fg,
                        hover_color=hover,
                    )

                    if not full:
                        def _select(sched=schedule_str, button=btn):
                            # reset others
                            for child in slots_frame.winfo_children():
                                base = getattr(child, "_base_fg", None)
                                if base is not None:
                                    child.configure(fg_color=base)
                            button.configure(fg_color="#145ea8")
                            selected_schedule["value"] = sched

                        btn._base_fg = fg
                        btn.configure(command=_select)

                    btn.grid(row=row_idx, column=col_idx, padx=4, pady=4, sticky="ew")
                    col_idx += 1
                    if col_idx >= 4:
                        col_idx = 0
                        row_idx += 1

                    current_dt += _td(minutes=step)

            conn.close()

        # Initial load of slots based on existing doctor/date
        load_slots_for_selection()

        # Notes editing
        ctk.CTkLabel(win, text="Notes").grid(row=4, column=0, padx=20, pady=5, sticky="nw")
        notes_entry = ctk.CTkTextbox(win, height=80)
        if notes:
            notes_entry.insert("1.0", notes)
        notes_entry.grid(row=4, column=1, padx=20, pady=5, sticky="nsew")

        # Reload slots when doctor or date changes
        doctor_combo.configure(command=lambda _value: load_slots_for_selection())
        date_entry.bind("<FocusOut>", lambda _e: load_slots_for_selection())

        def save_changes():
            new_patient = patient_entry.get().strip()
            new_doctor = doctor_combo.get().strip()
            new_schedule = selected_schedule["value"]
            new_notes = notes_entry.get("1.0", "end").strip()

            if not new_patient or not new_doctor or not new_schedule:
                messagebox.showwarning("Validation", "Patient, doctor, and time slot are required.")
                return

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            # Mark this appointment as rescheduled when changing via receptionist records
            cur.execute(
                "UPDATE appointments SET patient_name = ?, doctor_name = ?, schedule = ?, notes = ?, is_rescheduled = 1 WHERE id = ?",
                (new_patient, new_doctor, new_schedule, new_notes, rid),
            )
            conn.commit()
            conn.close()

            win.destroy()
            self.reload_records()

        save_btn = ctk.CTkButton(win, text="Save", command=save_changes)
        save_btn.grid(row=5, column=0, columnspan=2, pady=(16, 20))

    def export_csv(self):
        filtered = self.get_filtered_records()
        if not filtered:
            messagebox.showinfo("Export", "No records to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export appointments to CSV",
        )
        if not file_path:
            return

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Patient", "Doctor", "Schedule", "Notes"])
            for rid, patient, doctor, schedule, notes in filtered:
                writer.writerow(
                    [
                        rid,
                        patient,
                        doctor,
                        self._format_schedule(schedule),
                        notes or "",
                    ]
                )

        messagebox.showinfo("Export", "Appointments exported successfully.")
