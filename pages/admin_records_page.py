import customtkinter as ctk
import sqlite3
import csv
from datetime import datetime

from tkinter import filedialog, messagebox, Menu
from database import DB_NAME, log_activity


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

        header_label = ctk.CTkLabel(
            header_row,
            text="Appointments",
            font=("Segoe UI", 13, "bold"),
        )
        header_label.grid(row=0, column=0, sticky="w")

        self.table_frame = ctk.CTkScrollableFrame(table_container, corner_radius=10)
        self.table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))
        self.table_frame.grid_columnconfigure(0, weight=1)

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

            # Outlined Row Item
            row_frame = ctk.CTkFrame(
                self.table_frame, 
                corner_radius=6, 
                fg_color="transparent", 
                border_width=1, 
                border_color="#3d3d3d"
            )
            row_frame.grid(row=row_index, column=0, sticky="ew", padx=10, pady=4)
            row_frame.grid_columnconfigure(1, weight=1)

            pretty_schedule = self._format_schedule(schedule)
            paid_text = "PAID" if is_paid else "UNPAID"
            amount_text = f"₱{amount_paid:,.2f}" if amount_paid else "-"
            
            # Using a combined label for uniformity with the requested style, 
            # or we can split it. The user asked for "outline very items".
            # Let's keep the textual summary but ensure the container is outlined.
            summary_text = (
                 f"#{rid}  ·  {patient}  ·  {doctor}  ·  {pretty_schedule}  ·  {paid_text}  ·  {amount_text}"
            )

            summary_label = ctk.CTkLabel(
                row_frame,
                text=summary_text,
                anchor="w",
                justify="left",
                font=("Segoe UI", 13)
            )
            summary_label.grid(row=0, column=0, padx=15, pady=12, sticky="w")
            # We assign column 1 to a spacer if needed, but here label is col 0, actions col 2.
            # Let's push actions to the right using weight on a middle column.
            row_frame.grid_columnconfigure(0, weight=0)
            row_frame.grid_columnconfigure(1, weight=1)

            actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            actions_frame.grid(row=0, column=2, padx=15, pady=10, sticky="e")

            view_btn = ctk.CTkButton(
                actions_frame,
                text="View",
                width=60,
                height=26,
                font=("Segoe UI", 11),
                fg_color="transparent",
                border_width=1,
                border_color="#0d74d1",
                text_color="#0d74d1",
                hover_color=("#d0e1f5", "#1a2c42"),
                command=lambda r=rec: self._view_details(r),
            )
            view_btn.grid(row=0, column=0, padx=(0, 6))

            edit_btn = ctk.CTkButton(
                actions_frame,
                text="Edit",
                width=60,
                height=26,
                font=("Segoe UI", 11),
                fg_color="transparent",
                border_width=1,
                border_color="#1c9b3b",
                text_color="#1c9b3b",
                hover_color=("#d1f0d9", "#1e3324"),
                command=lambda r=rec: self._edit_record(r),
            )
            edit_btn.grid(row=0, column=1, padx=(0, 6))

            delete_btn = ctk.CTkButton(
                actions_frame,
                text="Delete",
                width=60,
                height=26,
                font=("Segoe UI", 11),
                fg_color="transparent",
                border_width=1,
                border_color="#dc2626",
                text_color="#dc2626",
                hover_color=("#fee2e2", "#450a0a"),
                command=lambda r=rec: self._delete_record(r),
            )
            delete_btn.grid(row=0, column=2, padx=(0, 0))

            # Clicking anywhere on the row or summary opens the details view
            def _open_details(_event=None, r=rec):
                self._view_details(r)

            row_frame.bind("<Button-1>", _open_details)
            summary_label.bind("<Button-1>", _open_details)

            # Right-click context menu
            def _on_right_click(event, r=rec):
                self._show_row_menu(event, r)

            row_frame.bind("<Button-3>", _on_right_click)
            summary_label.bind("<Button-3>", _on_right_click)

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
        menu.add_command(
            label="Delete",
            command=lambda r=record: self._delete_record(r),
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
        win.title("")
        win.geometry("550x550")

        win.transient(self)
        win.grab_set()
        win.focus()

        # Center over parent
        self.update_idletasks()
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()
        win.update_idletasks()
        win_w = 550
        win_h = 550
        x = parent_x + (parent_w - win_w) // 2
        y = parent_y + (parent_h - win_h) // 2
        win.geometry(f"{win_w}x{win_h}+{x}+{y}")

        # Header
        ctk.CTkLabel(
            win, 
            text="Details", 
            font=("Segoe UI", 22, "bold")
        ).pack(anchor="w", padx=30, pady=(25, 5))

        ctk.CTkLabel(
            win,
            text=f"Appointment #{rid}",
            font=("Segoe UI", 14),
            text_color="gray70"
        ).pack(anchor="w", padx=30, pady=(0, 15))

        container = ctk.CTkScrollableFrame(win, corner_radius=0, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=0, pady=(0, 60))
        container.grid_columnconfigure(0, weight=1)

        def _add_row(label_text, value_text, r_idx, is_multi=False):
            frame = ctk.CTkFrame(
                container, 
                corner_radius=6, 
                fg_color="transparent", 
                border_width=1, 
                border_color="#3d3d3d"
            )
            frame.grid(row=r_idx, column=0, sticky="ew", padx=30, pady=6)
            frame.grid_columnconfigure(1, weight=1)
            
            lbl = ctk.CTkLabel(
                frame, 
                text=label_text, 
                width=100, 
                anchor="w", 
                font=("Segoe UI", 12, "bold"), 
                text_color="gray70"
            )
            lbl.grid(row=0, column=0, padx=(15, 5), pady=12, sticky="nw" if is_multi else "w")
            
            val = ctk.CTkLabel(
                frame, 
                text=value_text, 
                font=("Segoe UI", 12), 
                justify="left", 
                anchor="w",
                wraplength=340 if is_multi else 0
            )
            val.grid(row=0, column=1, padx=(5, 15), pady=12, sticky="w")
            return frame

        _add_row("Patient:", patient, 0)
        _add_row("Doctor:", doctor, 1)
        _add_row("Schedule:", self._format_schedule(schedule), 2)
        _add_row("Notes:", notes or "", 3, is_multi=True)
        _add_row("Paid:", "Yes" if is_paid else "No", 4)
        _add_row("Amount paid:", f"₱{amount_paid:,.2f}" if amount_paid else "-", 5)

        close_btn = ctk.CTkButton(win, text="Close", command=win.destroy, width=120)
        close_btn.place(relx=0.5, rely=0.94, anchor="center")

    def _edit_record(self, record):
        rid, patient, doctor, schedule, notes, _is_paid, _amount_paid = record

        win = ctk.CTkToplevel(self)
        win.title(f"Edit Appointment #{rid}")
        # Larger window to comfortably show all fields
        win.geometry("520x420")

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
        win.grid_rowconfigure(6, weight=1)

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

        # Parse meta information from combined notes (same format used elsewhere)
        raw_meta = notes or ""
        meta_parts = [p.strip() for p in raw_meta.split("|") if p.strip()]
        meta_values = {"Contact": "", "Address": "", "About": "", "Notes": ""}
        for p in meta_parts:
            if ":" in p:
                key, val = p.split(":", 1)
                key = key.strip()
                val = val.strip()
                if key in meta_values:
                    meta_values[key] = val
                else:
                    if meta_values["Notes"]:
                        meta_values["Notes"] += " " + p
                    else:
                        meta_values["Notes"] = p
            else:
                if meta_values["Notes"]:
                    meta_values["Notes"] += " " + p
                else:
                    meta_values["Notes"] = p

        ctk.CTkLabel(win, text="Contact").grid(row=3, column=0, padx=20, pady=5, sticky="w")
        contact_entry = ctk.CTkEntry(win)
        if meta_values["Contact"]:
            contact_entry.insert(0, meta_values["Contact"])
        contact_entry.grid(row=3, column=1, padx=20, pady=5, sticky="ew")

        ctk.CTkLabel(win, text="Address").grid(row=4, column=0, padx=20, pady=5, sticky="w")
        address_entry = ctk.CTkEntry(win)
        if meta_values["Address"]:
            address_entry.insert(0, meta_values["Address"])
        address_entry.grid(row=4, column=1, padx=20, pady=5, sticky="ew")

        ctk.CTkLabel(win, text="About").grid(row=5, column=0, padx=20, pady=5, sticky="w")
        about_entry = ctk.CTkEntry(win)
        if meta_values["About"]:
            about_entry.insert(0, meta_values["About"])
        about_entry.grid(row=5, column=1, padx=20, pady=5, sticky="ew")

        ctk.CTkLabel(win, text="Notes").grid(row=6, column=0, padx=20, pady=5, sticky="nw")
        notes_entry = ctk.CTkTextbox(win, height=80)
        if meta_values["Notes"]:
            notes_entry.insert("1.0", meta_values["Notes"])
        notes_entry.grid(row=6, column=1, padx=20, pady=5, sticky="nsew")

        def save_changes():
            new_patient = patient_entry.get().strip()
            new_doctor = doctor_entry.get().strip()
            new_schedule = schedule_entry.get().strip()
            new_contact = contact_entry.get().strip()
            new_address = address_entry.get().strip()
            new_about = about_entry.get().strip()
            new_notes_text = notes_entry.get("1.0", "end").strip()

            if not new_patient or not new_doctor or not new_schedule:
                messagebox.showwarning("Validation", "Patient, doctor, and schedule are required.")
                return

            combined_parts = []
            if new_contact:
                combined_parts.append(f"Contact: {new_contact}")
            if new_address:
                combined_parts.append(f"Address: {new_address}")
            if new_about:
                combined_parts.append(f"About: {new_about}")
            if new_notes_text:
                combined_parts.append(f"Notes: {new_notes_text}")
            new_notes = " | ".join(combined_parts) if combined_parts else None

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute(
                "UPDATE appointments SET patient_name = ?, doctor_name = ?, schedule = ?, notes = ? WHERE id = ?",
                (new_patient, new_doctor, new_schedule, new_notes, rid),
            )
            conn.commit()
            conn.close()

            # Log admin editing this appointment
            try:
                top = self.winfo_toplevel()
                username = getattr(top, "username", "admin")
                detail = f"Edited appointment #{rid} for {new_patient} with {new_doctor} at {new_schedule}"
                log_activity(username, "admin", "edit_appointment", detail)
            except Exception:
                pass

            win.destroy()
            self.reload_records()

        save_btn = ctk.CTkButton(win, text="Save", command=save_changes)
        save_btn.grid(row=7, column=0, columnspan=2, pady=(20, 20))

    def _delete_record(self, record):
        rid, patient, doctor, schedule, _notes, _is_paid, _amount_paid = record
        confirm = messagebox.askyesno(
            "Delete appointment",
            f"Are you sure you want to delete appointment #{rid} for {patient} with {doctor}?",
        )
        if not confirm:
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("DELETE FROM appointments WHERE id = ?", (rid,))
        conn.commit()
        conn.close()

        self.reload_records()

        # Log admin deleting this appointment
        try:
            top = self.winfo_toplevel()
            username = getattr(top, "username", "admin")
            detail = f"Deleted appointment #{rid} for {patient} with {doctor} at {schedule}"
            log_activity(username, "admin", "delete_appointment", detail)
        except Exception:
            pass


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

        # Log export action
        try:
            top = self.winfo_toplevel()
            username = getattr(top, "username", "admin")
            detail = f"Exported {len(filtered)} appointments to CSV at '{file_path}'"
            log_activity(username, "admin", "export_appointments_csv", detail)
        except Exception:
            pass

