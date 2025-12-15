import customtkinter as ctk
import sqlite3
from datetime import datetime

from tkinter import messagebox
from database import DB_NAME


class CashierRecordsPage(ctk.CTkFrame):
    """Cashier view of appointment/payment records (view-only)."""

    def __init__(self, master):
        super().__init__(master, corner_radius=0, fg_color="transparent")

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header & Controls
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)

        # Title
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="ew")
        
        ctk.CTkLabel(
            title_box,
            text="Records",
            font=("Inter", 20, "bold"),
            text_color="white"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="View previous appointment and payment records.",
            font=("Inter", 13),
            text_color="#94a3b8"
        ).pack(anchor="w", pady=(2, 0))

        # Controls
        controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=1, sticky="e")
        controls_frame.grid_columnconfigure(1, weight=1)

        self.search_entry = ctk.CTkEntry(
            controls_frame,
            placeholder_text="Search patient or doctor...",
            width=200,
            height=36,
            font=("Inter", 13),
            fg_color="#1e293b",
            border_width=1,
            border_color="#334155",
            text_color="white",
            placeholder_text_color="#94a3b8"
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<Return>", lambda event: self.apply_filters())

        # Filters and Refresh
        self.status_filter = "all"
        
        # Filter Buttons Container
        filter_box = ctk.CTkFrame(controls_frame, fg_color="#1e293b", corner_radius=8)
        filter_box.pack(side="left", padx=(0, 10))

        self.btn_all = self._make_filter_btn(filter_box, "All", "all")
        self.btn_all.pack(side="left", padx=2, pady=2)
        
        self.btn_unpaid = self._make_filter_btn(filter_box, "Unpaid", "unpaid") 
        self.btn_unpaid.pack(side="left", padx=2, pady=2)
        
        self.btn_paid = self._make_filter_btn(filter_box, "Paid", "paid")
        self.btn_paid.pack(side="left", padx=2, pady=2)

        self.refresh_button = ctk.CTkButton(
            controls_frame,
            text="Refresh",
            width=80,
            height=36,
            fg_color="#334155",
            hover_color="#475569",
            font=("Inter", 13),
            command=self.reload_records,
        )
        self.refresh_button.pack(side="left")

        # 2. Records List Container
        # Transparent background so list items float using their own card bg
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Table Header
        header_row = ctk.CTkFrame(container, fg_color="transparent", height=40)
        header_row.grid(row=0, column=0, sticky="ew", padx=(15, 20), pady=(0, 5))
        # Cols: ID(0.5), Details(3), Amount(1), Status(1), Actions(0)
        header_row.grid_columnconfigure(0, weight=1) # ID + Patient/Doctor
        header_row.grid_columnconfigure(1, weight=1) # Schedule/Total
        header_row.grid_columnconfigure(2, weight=0, minsize=100) # Status
        header_row.grid_columnconfigure(3, weight=0, minsize=100) # Actions

        def _hlabel(col, text, align="w", px=5):
            ctk.CTkLabel(
                header_row, 
                text=text.upper(), 
                font=("Inter", 11, "bold"), 
                text_color="#64748b",
                anchor=align
            ).grid(row=0, column=col, sticky="ew", padx=px)

        _hlabel(0, "TRANSACTION INFO")
        _hlabel(1, "SCHEDULE / TOTAL")
        _hlabel(2, "STATUS")
        _hlabel(3, "ACTIONS", "e")

        self.table_frame = ctk.CTkScrollableFrame(container, corner_radius=0, fg_color="transparent")
        self.table_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=5)
        self.table_frame.grid_columnconfigure(0, weight=1)

        self.records = []
        self.reload_records()

    def _make_filter_btn(self, parent, text, mode):
        return ctk.CTkButton(
            parent,
            text=text,
            width=60,
            height=28,
            corner_radius=6,
            font=("Inter", 12, "bold"),
            fg_color="transparent",
            text_color="#94a3b8",
            hover_color="#334155",
            command=lambda: self._set_status_filter(mode)
        )

    def _update_filter_visuals(self):
        # Update button styles based on current filter
        active_fg = "#3b82f6"
        active_text = "white"
        inactive_fg = "transparent"
        inactive_text = "#94a3b8"

        for btn, mode in [(self.btn_all, "all"), (self.btn_unpaid, "unpaid"), (self.btn_paid, "paid")]:
            if self.status_filter == mode:
                btn.configure(fg_color=active_fg, text_color=active_text)
            else:
                btn.configure(fg_color=inactive_fg, text_color=inactive_text)

    def reload_records(self):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute(
            "SELECT id, patient_name, doctor_name, schedule, COALESCE(amount_paid, 0), COALESCE(is_paid, 0), barcode, notes FROM appointments ORDER BY id DESC LIMIT 50"
        )
        self.records = cur.fetchall()
        conn.close()
        self.apply_filters()
        self._update_filter_visuals()

    def clear_table(self):
        for child in self.table_frame.winfo_children():
            child.destroy()

    def get_filtered_records(self):
        query = self.search_entry.get().strip().lower()
        result = []
        for rec in self.records:
            rid, patient, doctor, schedule, amount_paid, is_paid, barcode, notes = rec
            haystack = f"{patient} {doctor} {barcode or ''}".lower()
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
            ctk.CTkLabel(
                self.table_frame,
                text="No records found.",
                font=("Inter", 14),
                text_color="#64748b"
            ).pack(pady=40)
            return

        for row_index, rec in enumerate(filtered):
            rid, patient, doctor, schedule, amount_paid, is_paid, barcode, notes = rec

            # Card Row
            row = ctk.CTkFrame(self.table_frame, corner_radius=10, fg_color="#1e293b", height=60)
            row.pack(fill="x", pady=5)
            
            row.grid_columnconfigure(0, weight=1)
            row.grid_columnconfigure(1, weight=1)
            row.grid_columnconfigure(2, weight=0, minsize=100)
            row.grid_columnconfigure(3, weight=0, minsize=100)

            pretty_schedule = self._format_schedule(schedule)
            total_value = self._extract_total_from_notes(notes)
            total_text = f"₱{total_value:,.2f}" if total_value is not None else "-"
            amt_text = f"₱{amount_paid:,.2f}" if amount_paid else "-"
            paid_text = "PAID" if is_paid else "UNPAID"
            paid_color = "#10b981" if is_paid else "#ef4444"

            # 1. Transaction Info (Patient / Doctor)
            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=10)
            
            ctk.CTkLabel(
                info_frame, 
                text=patient or "Unknown Patient", 
                font=("Inter", 14, "bold"), 
                text_color="white",
                anchor="w"
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                info_frame, 
                text=f"Dr. {doctor or 'Unknown'}", 
                font=("Inter", 12), 
                text_color="#94a3b8",
                anchor="w"
            ).pack(anchor="w")

            # 2. Schedule / Amount
            sched_frame = ctk.CTkFrame(row, fg_color="transparent")
            sched_frame.grid(row=0, column=1, sticky="ew", padx=10, pady=10)
            
            ctk.CTkLabel(
                sched_frame, 
                text=pretty_schedule, 
                font=("Inter", 13), 
                text_color="white",
                anchor="w"
            ).pack(anchor="w")
            
            detail_sub = f"Total: {total_text}"
            if is_paid: detail_sub += f" • Paid: {amt_text}"
            
            ctk.CTkLabel(
                sched_frame, 
                text=detail_sub, 
                font=("Inter", 12), 
                text_color="#94a3b8",
                anchor="w"
            ).pack(anchor="w")

            # 3. Status Badge
            status_Badge = ctk.CTkFrame(row, fg_color=paid_color, corner_radius=6, height=24)
            status_Badge.grid(row=0, column=2, padx=10)
            ctk.CTkLabel(status_Badge, text=paid_text, font=("Inter", 11, "bold"), text_color="white").pack(padx=8, pady=2)

            # 4. Action
            ctk.CTkButton(
                row,
                text="Details",
                width=70,
                height=30,
                font=("Inter", 12, "bold"),
                fg_color="transparent",
                border_width=1,
                border_color="#3b82f6",
                text_color="#3b82f6",
                hover_color="#1e293b", # slightly darker or transparent hover
                command=lambda r=rec: self._view_details(r)
            ).grid(row=0, column=3, padx=15)

    def _view_details(self, record):
        rid, patient, doctor, schedule, amount_paid, is_paid, barcode, notes = record

        win = ctk.CTkToplevel(self)
        win.title("Transaction Details")
        win.geometry("500x600")
        win.configure(fg_color="#0f172a")
        win.transient(self)
        win.grab_set()

        # Center
        win.update_idletasks()
        try:
            mx = self.winfo_rootx() + (self.winfo_width() - 500) // 2
            my = self.winfo_rooty() + (self.winfo_height() - 600) // 2
            win.geometry(f"+{mx}+{my}")
        except: pass

        ctk.CTkLabel(win, text="Transaction Details", font=("Inter", 20, "bold"), text_color="white").pack(anchor="w", padx=30, pady=(25, 5))
        ctk.CTkLabel(win, text=f"Record ID #{rid}", font=("Inter", 13), text_color="#94a3b8").pack(anchor="w", padx=30, pady=(0, 20))

        content = ctk.CTkScrollableFrame(win, fg_color="#1e293b", corner_radius=16)
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        content.grid_columnconfigure(0, weight=1)

        def _row(idx, k, v, big=False, multi=False):
            f = ctk.CTkFrame(content, fg_color="transparent")
            f.grid(row=idx, column=0, sticky="ew", padx=15, pady=8)
            ctk.CTkLabel(f, text=k, font=("Inter", 12, "bold"), text_color="#94a3b8", width=100, anchor="w").pack(side="left", anchor="nw" if multi else "center")
            
            c = "white"
            ft = ("Inter", 13)
            if big: 
                c = "#4ade80"
                ft = ("Inter", 14, "bold")
            
            ctk.CTkLabel(f, text=v, font=ft, text_color=c, justify="left", wraplength=280).pack(side="left", anchor="w")

        _row(0, "Barcode:", barcode or "-")
        _row(1, "Patient:", patient or "-")
        _row(2, "Doctor:", doctor or "-")
        _row(3, "Schedule:", self._format_schedule(schedule))
        
        div = ctk.CTkFrame(content, height=1, fg_color="#334155")
        div.grid(row=4, column=0, sticky="ew", padx=15, pady=10)

        total_val = self._extract_total_from_notes(notes)
        total_str = f"₱{total_val:,.2f}" if total_val else "-"
        paid_str = f"₱{amount_paid:,.2f}" if amount_paid else "-"

        _row(5, "Total Due:", total_str)
        _row(6, "Paid Amount:", paid_str, big=True)
        _row(7, "Status:", "PAID" if is_paid else "UNPAID", big=True)

        div2 = ctk.CTkFrame(content, height=1, fg_color="#334155")
        div2.grid(row=8, column=0, sticky="ew", padx=15, pady=10)

        # Parse Notes
        raw = notes or ""
        parts = [p.strip() for p in raw.split("|") if p.strip()]
        vals = {"Contact": "", "Address": "", "About": "", "Notes": ""}
        for p in parts:
            if ":" in p:
                key, val = p.split(":", 1)
                k = key.strip()
                if k in vals: vals[k] = val.strip()
                else: vals["Notes"] += f" {p}"
            else: vals["Notes"] += f" {p}"

        _row(9, "Contact:", vals["Contact"] or "-")
        _row(10, "Address:", vals["Address"] or "-")
        _row(11, "Service:", vals["About"] or "-")
        _row(12, "Notes:", vals["Notes"], multi=True)

        # Copy Barcode Button in Modal
        if barcode:
            def _copy():
                win.clipboard_clear()
                win.clipboard_append(barcode)
                ctk.CTkLabel(content, text="Copied!", text_color="#10b981", font=("Inter", 10)).grid(row=14, column=0)
                
            ctk.CTkButton(content, text="Copy Barcode", font=("Inter", 12), height=24, fg_color="#334155", command=_copy).grid(row=13, column=0, pady=10)

        ctk.CTkButton(win, text="Close", width=100, fg_color="transparent", border_width=1, border_color="#64748b", text_color="#cbd5e1", hover_color="#334155", command=win.destroy).pack(pady=(0, 20))

    def _extract_total_from_notes(self, notes: str | None) -> float | None:
        if not notes: return None
        raw = notes.split("About:", 1)[1] if "About:" in notes else notes
        digits = []
        token = ""
        for ch in raw:
            if ch.isdigit() or ch in ",.": token += ch
            else:
                if token: digits.append(token); token = ""
        if token: digits.append(token)
        if not digits: return None
        try: return float(digits[-1].replace(",", ""))
        except: return None

    def _set_status_filter(self, value: str):
        self.status_filter = value
        self.apply_filters()
        self._update_filter_visuals()

    def _format_schedule(self, schedule_str: str) -> str:
        try:
            return datetime.strptime(schedule_str, "%Y-%m-%d %H:%M").strftime("%b %d, %Y %I:%M %p")
        except: return schedule_str
