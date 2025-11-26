import customtkinter as ctk
import sqlite3
import csv
from datetime import datetime

from tkinter import filedialog, messagebox, Menu
from database import DB_NAME


class AdminRecordsPage(ctk.CTkFrame):
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
            text="View and manage appointment records.",
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
            command=self.reload_records,
        )
        self.refresh_button.grid(row=0, column=1)

        self.clear_button = ctk.CTkButton(
            controls_frame,
            text="Clear",
            width=70,
            command=self.clear_filters,
        )
        self.clear_button.grid(row=0, column=2, padx=(10, 0))

        self.export_button = ctk.CTkButton(
            controls_frame,
            text="Export CSV",
            width=80,
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
        header_row.grid_columnconfigure(4, weight=1)
        header_row.grid_columnconfigure(5, weight=1)
        header_row.grid_columnconfigure(6, weight=1)
        header_row.grid_columnconfigure(7, weight=1)

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

        paid_header = ctk.CTkLabel(
            header_row,
            text="Paid",
            font=("Segoe UI", 13, "bold"),
        )
        paid_header.grid(row=0, column=5, sticky="w")

        amount_header = ctk.CTkLabel(
            header_row,
            text="Amount paid",
            font=("Segoe UI", 13, "bold"),
        )
        amount_header.grid(row=0, column=6, sticky="w")

        actions_header = ctk.CTkLabel(
            header_row,
            text="Actions",
            font=("Segoe UI", 13, "bold"),
        )
        actions_header.grid(row=0, column=7, sticky="w")

        self.table_frame = ctk.CTkScrollableFrame(table_container, corner_radius=10)
        self.table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        self.table_frame.grid_columnconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(1, weight=1)
        self.table_frame.grid_columnconfigure(2, weight=1)
        self.table_frame.grid_columnconfigure(3, weight=1)
        self.table_frame.grid_columnconfigure(4, weight=1)
        self.table_frame.grid_columnconfigure(5, weight=1)
        self.table_frame.grid_columnconfigure(6, weight=1)
        self.table_frame.grid_columnconfigure(7, weight=1)

        self.records = []
        self.reload_records()

        self.search_entry.bind("<Return>", lambda event: self.apply_filters())

    def clear_filters(self):
        self.search_entry.delete(0, "end")
        self.apply_filters()

    def reload_records(self):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute(
            "SELECT id, patient_name, doctor_name, schedule, notes, COALESCE(is_paid, 0), COALESCE(amount_paid, 0) FROM appointments ORDER BY id ASC"
        )
        self.records = cur.fetchall()

        conn.close()
        self.apply_filters()

    def get_filtered_records(self):
        query = self.search_entry.get().strip().lower()

        filtered = []
        for rec in self.records:
            rid, patient, doctor, schedule, notes, is_paid, amount_paid = rec
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
            rid, patient, doctor, schedule, notes, is_paid, amount_paid = rec

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

            pretty_schedule = self._format_schedule(schedule)

            schedule_label = ctk.CTkLabel(
                self.table_frame,
                text=pretty_schedule,
                anchor="w",
            )
            schedule_label.grid(row=row_index, column=3, sticky="ew", padx=(0, 5), pady=2)
            row_widgets.append(schedule_label)

            notes_text = notes or ""
            notes_label = ctk.CTkLabel(
                self.table_frame,
                text=notes_text,
                anchor="w",
            )
            notes_label.grid(row=row_index, column=4, sticky="ew", padx=(0, 5), pady=2)
            row_widgets.append(notes_label)

            paid_label = ctk.CTkLabel(
                self.table_frame,
                text=("Yes" if is_paid else "No"),
                anchor="w",
            )
            paid_label.grid(row=row_index, column=5, sticky="ew", padx=(0, 5), pady=2)
            row_widgets.append(paid_label)

            amount_label = ctk.CTkLabel(
                self.table_frame,
                text=(f"₱{amount_paid:,.2f}" if amount_paid else "-"),
                anchor="w",
            )
            amount_label.grid(row=row_index, column=6, sticky="ew", padx=(0, 5), pady=2)
            row_widgets.append(amount_label)

            actions_frame = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            actions_frame.grid(row=row_index, column=7, sticky="e", padx=(0, 5), pady=2)

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
        rid, patient, doctor, schedule, notes, is_paid, amount_paid = record

        win = ctk.CTkToplevel(self)
        win.title(f"Appointment #{rid}")
        win.geometry("400x260")

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

        ctk.CTkLabel(win, text="Notes:").grid(row=3, column=0, padx=20, pady=5, sticky="nw")
        notes_text = notes or ""
        notes_label = ctk.CTkLabel(win, text=notes_text, justify="left")
        notes_label.grid(row=3, column=1, padx=20, pady=5, sticky="w")

        ctk.CTkLabel(win, text="Paid:").grid(row=4, column=0, padx=20, pady=5, sticky="w")
        ctk.CTkLabel(win, text=("Yes" if is_paid else "No")).grid(row=4, column=1, padx=20, pady=5, sticky="w")

        ctk.CTkLabel(win, text="Amount paid:").grid(row=5, column=0, padx=20, pady=5, sticky="w")
        ctk.CTkLabel(win, text=(f"₱{amount_paid:,.2f}" if amount_paid else "-")).grid(
            row=5, column=1, padx=20, pady=5, sticky="w"
        )

        close_btn = ctk.CTkButton(win, text="Close", command=win.destroy)
        close_btn.grid(row=6, column=0, columnspan=2, pady=(20, 20))

    def _edit_record(self, record):
        rid, patient, doctor, schedule, notes, _is_paid, _amount_paid = record

        win = ctk.CTkToplevel(self)
        win.title(f"Edit Appointment #{rid}")
        win.geometry("420x320")

        win.transient(self)
        win.grab_set()
        win.focus()

        # Center over parent
        self.update_idletasks()
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()
        win_w = 420
        win_h = 320
        x = parent_x + (parent_w - win_w) // 2
        y = parent_y + (parent_h - win_h) // 2
        win.geometry(f"{win_w}x{win_h}+{x}+{y}")

        win.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(win, text="Patient").grid(row=0, column=0, padx=20, pady=(20, 5), sticky="w")
        patient_entry = ctk.CTkEntry(win)
        patient_entry.insert(0, patient)
        patient_entry.grid(row=0, column=1, padx=20, pady=(20, 5), sticky="ew")

        ctk.CTkLabel(win, text="Doctor").grid(row=1, column=0, padx=20, pady=5, sticky="w")
        doctor_entry = ctk.CTkEntry(win)
        doctor_entry.insert(0, doctor)
        doctor_entry.grid(row=1, column=1, padx=20, pady=5, sticky="ew")

        ctk.CTkLabel(win, text="Schedule").grid(row=2, column=0, padx=20, pady=5, sticky="w")
        schedule_entry = ctk.CTkEntry(win)
        schedule_entry.insert(0, schedule)
        schedule_entry.grid(row=2, column=1, padx=20, pady=5, sticky="ew")

        ctk.CTkLabel(win, text="Notes").grid(row=3, column=0, padx=20, pady=5, sticky="nw")
        notes_entry = ctk.CTkTextbox(win, height=80)
        if notes:
            notes_entry.insert("1.0", notes)
        notes_entry.grid(row=3, column=1, padx=20, pady=5, sticky="nsew")

        def save_changes():
            new_patient = patient_entry.get().strip()
            new_doctor = doctor_entry.get().strip()
            new_schedule = schedule_entry.get().strip()
            new_notes = notes_entry.get("1.0", "end").strip()

            if not new_patient or not new_doctor or not new_schedule:
                messagebox.showwarning("Validation", "Patient, doctor, and schedule are required.")
                return

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute(
                "UPDATE appointments SET patient_name = ?, doctor_name = ?, schedule = ?, notes = ? WHERE id = ?",
                (new_patient, new_doctor, new_schedule, new_notes, rid),
            )
            conn.commit()
            conn.close()

            win.destroy()
            self.reload_records()

        save_btn = ctk.CTkButton(win, text="Save", command=save_changes)
        save_btn.grid(row=4, column=0, columnspan=2, pady=(20, 20))


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
            for rid, patient, doctor, schedule, notes, _is_paid, _amount_paid in filtered:
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

