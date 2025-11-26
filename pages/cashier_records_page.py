import customtkinter as ctk
import sqlite3
from datetime import datetime

from tkinter import messagebox
from database import DB_NAME


class CashierRecordsPage(ctk.CTkFrame):
    """Cashier view of appointment/payment records (view-only)."""

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
            text="View previous appointment and payment records.",
            font=("Segoe UI", 14),
        )
        subtitle.grid(row=1, column=0, pady=(4, 0), sticky="w")

        controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=1, rowspan=2, padx=(20, 0), sticky="e")
        controls_frame.grid_columnconfigure(0, weight=0)
        controls_frame.grid_columnconfigure(1, weight=0)
        controls_frame.grid_columnconfigure(2, weight=0)
        controls_frame.grid_columnconfigure(3, weight=0)

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

        self.status_filter = "all"

        self.filter_all_button = ctk.CTkButton(
            controls_frame,
            text="All",
            width=50,
            command=lambda: self._set_status_filter("all"),
        )
        self.filter_all_button.grid(row=1, column=0, padx=(0, 4), pady=(6, 0))

        self.filter_unpaid_button = ctk.CTkButton(
            controls_frame,
            text="Unpaid",
            width=70,
            command=lambda: self._set_status_filter("unpaid"),
        )
        self.filter_unpaid_button.grid(row=1, column=1, padx=4, pady=(6, 0))

        self.filter_paid_button = ctk.CTkButton(
            controls_frame,
            text="Paid",
            width=60,
            command=lambda: self._set_status_filter("paid"),
        )
        self.filter_paid_button.grid(row=1, column=2, padx=(4, 0), pady=(6, 0))

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

        ctk.CTkLabel(header_row, text="ID", font=("Segoe UI", 13, "bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header_row, text="Patient", font=("Segoe UI", 13, "bold")).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(header_row, text="Doctor", font=("Segoe UI", 13, "bold")).grid(row=0, column=2, sticky="w")
        ctk.CTkLabel(header_row, text="Schedule", font=("Segoe UI", 13, "bold")).grid(row=0, column=3, sticky="w")
        ctk.CTkLabel(header_row, text="Total", font=("Segoe UI", 13, "bold")).grid(row=0, column=4, sticky="w")
        ctk.CTkLabel(header_row, text="Amount paid", font=("Segoe UI", 13, "bold")).grid(row=0, column=5, sticky="w")
        ctk.CTkLabel(header_row, text="Paid?", font=("Segoe UI", 13, "bold")).grid(row=0, column=6, sticky="w")
        ctk.CTkLabel(header_row, text="Actions", font=("Segoe UI", 13, "bold")).grid(row=0, column=7, sticky="w")

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

    def reload_records(self):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute(
            "SELECT id, patient_name, doctor_name, schedule, COALESCE(amount_paid, 0), COALESCE(is_paid, 0), barcode, notes FROM appointments ORDER BY id ASC"
        )
        self.records = cur.fetchall()
        conn.close()
        self.apply_filters()

    def clear_table(self):
        for child in self.table_frame.winfo_children():
            child.destroy()

    def get_filtered_records(self):
        query = self.search_entry.get().strip().lower()
        result = []
        for rec in self.records:
            rid, patient, doctor, schedule, amount_paid, is_paid, barcode, notes = rec
            haystack = f"{patient} {doctor}".lower()
            if query and query not in haystack:
                continue
            if self.status_filter == "paid" and not is_paid:
                continue
            if self.status_filter == "unpaid" and is_paid:
                continue
            result.append(rec)
        return result

    def apply_filters(self):
        self.clear_table()
        filtered = self.get_filtered_records()

        for row_index, rec in enumerate(filtered):
            rid, patient, doctor, schedule, amount_paid, is_paid, barcode, notes = rec

            ctk.CTkLabel(self.table_frame, text=str(rid), anchor="center").grid(
                row=row_index, column=0, sticky="nsew", padx=(0, 5), pady=2
            )
            ctk.CTkLabel(self.table_frame, text=patient, anchor="center").grid(
                row=row_index, column=1, sticky="nsew", padx=(0, 5), pady=2
            )
            ctk.CTkLabel(self.table_frame, text=doctor, anchor="center").grid(
                row=row_index, column=2, sticky="nsew", padx=(0, 5), pady=2
            )
            ctk.CTkLabel(self.table_frame, text=self._format_schedule_short(schedule), anchor="center").grid(
                row=row_index, column=3, sticky="nsew", padx=(0, 5), pady=2
            )

            total_value = self._extract_total_from_notes(notes)
            total_text = f"₱{total_value:,.2f}" if total_value is not None else "-"
            ctk.CTkLabel(self.table_frame, text=total_text, anchor="center").grid(
                row=row_index, column=4, sticky="nsew", padx=(0, 5), pady=2
            )

            amt_text = f"₱{amount_paid:,.2f}" if amount_paid else "-"
            ctk.CTkLabel(self.table_frame, text=amt_text, anchor="center").grid(
                row=row_index, column=5, sticky="nsew", padx=(0, 5), pady=2
            )

            paid_text = "Yes" if is_paid else "No"
            paid_color = "#16a34a" if is_paid else "#dc2626"
            ctk.CTkLabel(self.table_frame, text=paid_text, anchor="center", text_color=paid_color).grid(
                row=row_index, column=6, sticky="nsew", padx=(0, 5), pady=2
            )

            actions_frame = ctk.CTkFrame(self.table_frame, fg_color="transparent")
            actions_frame.grid(row=row_index, column=7, sticky="e", padx=(0, 5), pady=2)

            view_btn = ctk.CTkButton(
                actions_frame,
                text="VIEW",
                width=50,
                height=24,
                fg_color="#0d74d1",
                hover_color="#0b63b3",
                command=lambda r=rec: self._view_details(r),
            )
            view_btn.grid(row=0, column=0)

    def _view_details(self, record):
        rid, patient, doctor, schedule, amount_paid, is_paid, barcode, notes = record

        win = ctk.CTkToplevel(self)
        win.title(f"Appointment #{rid}")
        win.geometry("640x480")

        win.transient(self)
        win.grab_set()
        win.focus()

        self.update_idletasks()
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()
        win_w = 640
        win_h = 480
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

        total_value = self._extract_total_from_notes(notes)
        total_text = f"₱{total_value:,.2f}" if total_value is not None else "-"
        ctk.CTkLabel(win, text="Total:").grid(row=3, column=0, padx=20, pady=5, sticky="w")
        ctk.CTkLabel(win, text=total_text).grid(row=3, column=1, padx=20, pady=5, sticky="w")

        amt_text = f"₱{amount_paid:,.2f}" if amount_paid else "-"
        ctk.CTkLabel(win, text="Amount paid:").grid(row=4, column=0, padx=20, pady=5, sticky="w")
        ctk.CTkLabel(win, text=amt_text).grid(row=4, column=1, padx=20, pady=5, sticky="w")

        paid_text = "Yes" if is_paid else "No"
        ctk.CTkLabel(win, text="Paid:").grid(row=5, column=0, padx=20, pady=5, sticky="w")
        ctk.CTkLabel(win, text=paid_text).grid(row=5, column=1, padx=20, pady=5, sticky="w")

        ctk.CTkLabel(win, text="Barcode:").grid(row=6, column=0, padx=20, pady=5, sticky="w")
        barcode_row = ctk.CTkFrame(win, fg_color="transparent")
        barcode_row.grid(row=6, column=1, padx=20, pady=5, sticky="ew")
        barcode_row.grid_columnconfigure(0, weight=1)

        barcode_text = barcode or "(none)"
        barcode_entry = ctk.CTkEntry(barcode_row)
        barcode_entry.insert(0, barcode_text)
        barcode_entry.configure(state="readonly")
        barcode_entry.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        def _copy_barcode():
            value = barcode or ""
            win.clipboard_clear()
            win.clipboard_append(value)

        copy_btn = ctk.CTkButton(barcode_row, text="Copy", width=60, command=_copy_barcode)
        copy_btn.grid(row=0, column=1, sticky="e")

        raw = notes or ""
        parts = [p.strip() for p in raw.split("|") if p.strip()]
        values = {"Contact": "", "Address": "", "About": "", "Notes": ""}
        for p in parts:
            if ":" in p:
                key, val = p.split(":", 1)
                key = key.strip()
                val = val.strip()
                if key in values:
                    values[key] = val
                else:
                    if values["Notes"]:
                        values["Notes"] += " " + p
                    else:
                        values["Notes"] = p
            else:
                if values["Notes"]:
                    values["Notes"] += " " + p
                else:
                    values["Notes"] = p

        ctk.CTkLabel(win, text="Contact:").grid(row=7, column=0, padx=20, pady=5, sticky="w")
        ctk.CTkLabel(win, text=values["Contact"] or "-").grid(row=7, column=1, padx=20, pady=5, sticky="w")

        ctk.CTkLabel(win, text="Address:").grid(row=8, column=0, padx=20, pady=5, sticky="w")
        ctk.CTkLabel(win, text=values["Address"] or "-").grid(row=8, column=1, padx=20, pady=5, sticky="w")

        ctk.CTkLabel(win, text="About:").grid(row=9, column=0, padx=20, pady=5, sticky="w")
        ctk.CTkLabel(win, text=values["About"] or "-").grid(row=9, column=1, padx=20, pady=5, sticky="w")

        ctk.CTkLabel(win, text="Notes:").grid(row=10, column=0, padx=20, pady=5, sticky="nw")
        notes_text = values["Notes"] or ""
        notes_label = ctk.CTkLabel(win, text=notes_text, justify="left")
        notes_label.grid(row=10, column=1, padx=20, pady=5, sticky="w")

        close_btn = ctk.CTkButton(win, text="Close", width=80, command=win.destroy)
        close_btn.grid(row=11, column=0, columnspan=2, pady=(20, 20))

    def _extract_total_from_notes(self, notes: str | None) -> float | None:
        if not notes:
            return None
        raw = notes
        if "About:" in raw:
            after = raw.split("About:", 1)[1]
        else:
            after = raw
        digits = []
        token = ""
        for ch in after:
            if ch.isdigit() or ch in ",.":
                token += ch
            else:
                if token:
                    digits.append(token)
                    token = ""
        if token:
            digits.append(token)
        if not digits:
            return None
        candidate = digits[-1].replace(",", "")
        try:
            value = float(candidate)
        except ValueError:
            return None
        return value

    def _set_status_filter(self, value: str):
        self.status_filter = value
        self.apply_filters()

    def _format_schedule(self, schedule_str: str) -> str:
        try:
            dt = datetime.strptime(schedule_str, "%Y-%m-%d %H:%M")
            return dt.strftime("%b %d, %Y %I:%M %p")
        except Exception:
            return schedule_str

    def _format_schedule_short(self, schedule_str: str) -> str:
        try:
            dt = datetime.strptime(schedule_str, "%Y-%m-%d %H:%M")
            return dt.strftime("%m/%d/%y")
        except Exception:
            parts = schedule_str.split()
            if parts:
                try:
                    dt = datetime.strptime(parts[0], "%Y-%m-%d")
                    return dt.strftime("%m/%d/%y")
                except Exception:
                    return parts[0]
            return schedule_str

    def _show_error(self, title: str, message: str) -> None:
        messagebox.showerror(title, message)
