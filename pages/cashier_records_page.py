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
        controls_frame.grid_columnconfigure(4, weight=0)

        self.search_entry = ctk.CTkEntry(
            controls_frame,
            placeholder_text="Search patient or doctor...",
            width=160,
        )
        self.search_entry.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="w")

        self.refresh_button = ctk.CTkButton(
            controls_frame,
            text="Refresh",
            width=80,
            command=self.reload_records,
        )
        self.refresh_button.grid(row=0, column=1, padx=(0, 8), pady=0)

        self.status_filter = "all"

        self.filter_all_button = ctk.CTkButton(
            controls_frame,
            text="All",
            width=50,
            command=lambda: self._set_status_filter("all"),
        )
        self.filter_all_button.grid(row=0, column=2, padx=(0, 4), pady=0)

        self.filter_unpaid_button = ctk.CTkButton(
            controls_frame,
            text="Unpaid",
            width=70,
            command=lambda: self._set_status_filter("unpaid"),
        )
        self.filter_unpaid_button.grid(row=0, column=3, padx=4, pady=0)

        self.filter_paid_button = ctk.CTkButton(
            controls_frame,
            text="Paid",
            width=60,
            command=lambda: self._set_status_filter("paid"),
        )
        self.filter_paid_button.grid(row=0, column=4, padx=(4, 0), pady=0)

        table_container = ctk.CTkFrame(self, corner_radius=10)
        table_container.grid(row=1, column=0, padx=30, pady=(0, 30), sticky="nsew")
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        # Scrollable list of "folder" style records instead of a column table.
        self.table_frame = ctk.CTkScrollableFrame(table_container, corner_radius=10)
        self.table_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 10))
        self.table_frame.grid_columnconfigure(0, weight=1)

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

        if not filtered:
            empty = ctk.CTkLabel(
                self.table_frame,
                text="No records found.",
                font=("Segoe UI", 13),
                anchor="w",
            )
            empty.grid(row=0, column=0, padx=12, pady=10, sticky="w")
            return

        for row_index, rec in enumerate(filtered):
            rid, patient, doctor, schedule, amount_paid, is_paid, barcode, notes = rec

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
            total_value = self._extract_total_from_notes(notes)
            total_text = f"₱{total_value:,.2f}" if total_value is not None else "-"
            amt_text = f"₱{amount_paid:,.2f}" if amount_paid else "-"
            paid_text = "PAID" if is_paid else "UNPAID"
            paid_color = "#16a34a" if is_paid else "#dc2626"

            # 1) ID Column
            id_lbl = ctk.CTkLabel(
                row_frame, 
                text=f"#{rid}", 
                font=("Segoe UI", 16, "bold"),
                text_color=("gray60", "gray70")
            )
            id_lbl.grid(row=0, column=0, padx=(15, 10), pady=15, sticky="w")

            # 2) Info Column
            info_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            info_frame.grid(row=0, column=1, sticky="ew", padx=5)

            main_text = f"{patient or 'Unknown'} with {doctor or 'Unknown'}"
            sub_text = f"{pretty_schedule}  •  Total: {total_text}  •  Paid: {amt_text}"

            main_lbl = ctk.CTkLabel(info_frame, text=main_text, font=("Segoe UI", 14, "bold"), anchor="w")
            main_lbl.pack(side="top", anchor="w")

            sub_lbl = ctk.CTkLabel(info_frame, text=sub_text, font=("Segoe UI", 12), text_color=("gray50", "gray60"), anchor="w")
            sub_lbl.pack(side="top", anchor="w")

            # 3) Actions Column (Status + View)
            actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            actions_frame.grid(row=0, column=2, padx=15, pady=10, sticky="e")

            # Status Chip
            status_chip = ctk.CTkLabel(
                actions_frame,
                text=paid_text,
                font=("Segoe UI", 11, "bold"),
                fg_color=paid_color,
                corner_radius=6,
                width=72,
                anchor="center"
            )
            status_chip.grid(row=0, column=0, padx=(0, 10))

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
            view_btn.grid(row=0, column=1)

    def _view_details(self, record):
        rid, patient, doctor, schedule, amount_paid, is_paid, barcode, notes = record

        win = ctk.CTkToplevel(self)
        win.title("")
        win.geometry("550x650")

        win.transient(self)
        win.grab_set()
        win.focus()

        self.update_idletasks()
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()
        win.update_idletasks()
        win_w = 550
        win_h = 650
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

        total_value = self._extract_total_from_notes(notes)
        total_text = f"₱{total_value:,.2f}" if total_value is not None else "-"
        _add_row("Total:", total_text, 3)

        amt_text = f"₱{amount_paid:,.2f}" if amount_paid else "-"
        _add_row("Amount paid:", amt_text, 4)

        paid_text = "Yes" if is_paid else "No"
        _add_row("Paid:", paid_text, 5)

        # Barcode Row (Custom)
        bc_frame = ctk.CTkFrame(
            container, 
            corner_radius=6, 
            fg_color="transparent", 
            border_width=1, 
            border_color="#3d3d3d"
        )
        bc_frame.grid(row=6, column=0, sticky="ew", padx=30, pady=6)
        bc_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(
            bc_frame, 
            text="Barcode:", 
            width=100, 
            anchor="w", 
            font=("Segoe UI", 12, "bold"), 
            text_color="gray70"
        ).grid(row=0, column=0, padx=(15, 5), pady=12, sticky="w")
        
        bc_val = barcode or "(none)"
        ctk.CTkLabel(
            bc_frame, 
            text=bc_val, 
            font=("Segoe UI", 12, "bold"),
            text_color="#1c9b3b"
        ).grid(row=0, column=1, padx=5, sticky="w")

        def _copy():
             win.clipboard_clear()
             win.clipboard_append(bc_val)
        
        ctk.CTkButton(
            bc_frame, 
            text="Copy", 
            width=50, 
            height=24,
            fg_color="#333",
            hover_color="#444", 
            command=_copy
        ).grid(row=0, column=2, padx=15, pady=8)

        # Additional parsed info
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

        _add_row("Contact:", values["Contact"] or "-", 7)
        _add_row("Address:", values["Address"] or "-", 8)
        _add_row("About:", values["About"] or "-", 9)
        _add_row("Notes:", values["Notes"] or "", 10, is_multi=True)

        close_btn = ctk.CTkButton(win, text="Close", command=win.destroy, width=120)
        close_btn.place(relx=0.5, rely=0.94, anchor="center")

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
