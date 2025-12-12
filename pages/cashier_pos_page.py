import customtkinter as ctk
import sqlite3
from datetime import datetime
import os

from tkinter import messagebox

from database import DB_NAME, log_activity


class CashierPOSPage(ctk.CTkFrame):
    """Simple POS interface for cashiers: verify APPT barcode and mark as paid."""

    def __init__(self, master):
        super().__init__(master, corner_radius=0)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Main container with 2 columns
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_container.grid_rowconfigure(0, weight=1)
        main_container.grid_columnconfigure(0, weight=3) # Left: Details (60%)
        main_container.grid_columnconfigure(1, weight=2) # Right: Actions (40%)

        # --- LEFT PANEL: Transaction Details ---
        left_panel = ctk.CTkFrame(main_container, corner_radius=10, fg_color=("gray95", "#2b2b2b"))
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_panel.grid_rowconfigure(2, weight=1) # Details expand
        left_panel.grid_columnconfigure(0, weight=1)

        # 1. Header
        ctk.CTkLabel(
            left_panel, 
            text="Transaction Details", 
            font=("Segoe UI", 20, "bold")
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        # 2. Search Bar
        search_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        search_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        search_frame.grid_columnconfigure(0, weight=1)
        
        self.barcode_entry = ctk.CTkEntry(
            search_frame, 
            placeholder_text="Scan Appointment ID / Barcode...",
            height=35,
            font=("Segoe UI", 13)
        )
        self.barcode_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.barcode_entry.bind("<Return>", lambda _e: self._lookup())

        verify_btn = ctk.CTkButton(
            search_frame,
            text="Verify",
            width=100,
            height=35,
            fg_color="#0d74d1",
            hover_color="#0b63b3",
            font=("Segoe UI", 12, "bold"),
            command=self._lookup
        )
        verify_btn.grid(row=0, column=1)

        # 3. Details List (Scrollable)
        self.details_scroll = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        self.details_scroll.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 20))
        self.details_scroll.grid_columnconfigure(0, weight=1)

        self.detail_labels = {}
        # We will dynamically populate this in `_lookup`, but let's create the slots
        fields = ["Barcode", "Patient", "Doctor", "Date", "Time", "Notes", "Paid"]
        for idx, label in enumerate(fields):
            row_f = ctk.CTkFrame(self.details_scroll, corner_radius=6, border_width=1, border_color="#3d3d3d", fg_color="transparent")
            row_f.grid(row=idx, column=0, sticky="ew", pady=4, padx=5)
            row_f.grid_columnconfigure(1, weight=1)
            
            ctk.CTkLabel(row_f, text=f"{label}:", font=("Segoe UI", 12, "bold"), text_color="gray70", width=80, anchor="w").grid(row=0, column=0, padx=10, pady=10)
            
            val_lbl = ctk.CTkLabel(row_f, text="-", font=("Segoe UI", 13), anchor="w", justify="left")
            val_lbl.grid(row=0, column=1, padx=10, pady=10, sticky="w")
            
            self.detail_labels[label.lower()] = val_lbl

        # --- RIGHT PANEL: Actions ---
        right_panel = ctk.CTkFrame(main_container, corner_radius=10, fg_color=("gray95", "#1e1e1e"))
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        # 1. Totals Section
        totals_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        totals_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=30)
        totals_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(totals_frame, text="Total Due", font=("Segoe UI", 14)).grid(row=0, column=0, sticky="w", pady=5)
        self.amount_entry = ctk.CTkEntry(
            totals_frame, 
            height=40, 
            font=("Segoe UI", 20, "bold"),
            justify="right",
            border_color="#3d3d3d"
        )
        self.amount_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 15))

        ctk.CTkLabel(totals_frame, text="Amount Tendered", font=("Segoe UI", 14)).grid(row=2, column=0, sticky="w", pady=5)
        self.paid_entry = ctk.CTkEntry(
            totals_frame, 
            height=40, 
            font=("Segoe UI", 20, "bold"),
            justify="right",
            border_color="#3d3d3d"
        )
        self.paid_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        self.change_label = ctk.CTkLabel(
            totals_frame, 
            text="Change: ₱0.00", 
            font=("Segoe UI", 24, "bold"),
            text_color="#16a34a"
        )
        self.change_label.grid(row=4, column=0, columnspan=2, sticky="e", pady=10)

        # Realtime change computation
        self.amount_entry.bind("<KeyRelease>", lambda _e: self._update_change())
        self.paid_entry.bind("<KeyRelease>", lambda _e: self._update_change())

        # 2. Action Buttons Grid
        actions_grid = ctk.CTkFrame(right_panel, fg_color="transparent")
        actions_grid.grid(row=1, column=0, sticky="s ew", padx=20, pady=(20, 30))
        actions_grid.grid_columnconfigure((0, 1), weight=1)

        # Row 0: Helper actions (Drawer, Cancel)
        # OPEN DRAWER
        self.btn_drawer = ctk.CTkButton(
            actions_grid,
            text="OPEN DRAWER",
            font=("Segoe UI", 12, "bold"),
            fg_color="#2563eb", # Blue
            hover_color="#1d4ed8",
            height=50,
            command=lambda: messagebox.showinfo("POS", "Cash drawer opened.")
        )
        self.btn_drawer.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=5)

        # CANCEL (Clear)
        self.btn_cancel = ctk.CTkButton(
            actions_grid,
            text="CANCEL",
            font=("Segoe UI", 12, "bold"),
            fg_color="#d97706", # Amber/Orange
            hover_color="#b45309",
            height=50,
            command=self._clear
        )
        self.btn_cancel.grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=5)

        # Row 1: Primary action (Proceed)
        # PROCEED (Confirm Payment)
        self.btn_proceed = ctk.CTkButton(
            actions_grid,
            text="PROCEED",
            font=("Segoe UI", 14, "bold"),
            fg_color="#16a34a",
            hover_color="#15803d",
            height=60,
            command=self._confirm_payment
        )
        self.btn_proceed.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=(5, 0))

        self.current_record = None

        # Fixed price list for services (must match receptionist "About" dropdown text)
        self.service_prices = {
            "General Consultation - 400 PHP": 400.0,
            "Pediatrics Consultation - 450 PHP": 450.0,
            "Internal Medicine - 500 PHP": 500.0,
            "Cardiology Consultation - 800 PHP": 800.0,
            "OB-GYN Consultation - 700 PHP": 700.0,
            "Dermatology Consultation - 600 PHP": 600.0,
            "ENT Consultation - 550 PHP": 550.0,
            "Orthopedic Consultation - 750 PHP": 750.0,
            "Ophthalmology Consultation - 500 PHP": 500.0,
            "Dental Consultation - 350 PHP": 350.0,
            "CBC (Complete Blood Count) - 250 PHP": 250.0,
            "Urinalysis - 150 PHP": 150.0,
            "Stool Examination - 150 PHP": 150.0,
            "Fasting Blood Sugar (FBS) - 200 PHP": 200.0,
            "HbA1c - 800 PHP": 800.0,
            "Lipid Profile - 700 PHP": 700.0,
            "Creatinine Test - 300 PHP": 300.0,
            "BUN (Blood Urea Nitrogen) - 250 PHP": 250.0,
            "Liver Function Test (LFT) - 500 PHP": 500.0,
            "TSH / Thyroid Test - 700 PHP": 700.0,
            "Chest X-Ray (PA View) - 650 PHP": 650.0,
            "Lumbar X-Ray - 800 PHP": 800.0,
            "Ultrasound   Whole Abdomen - 1000 PHP": 1000.0,
            "Ultrasound   Pelvic / OB - 900 PHP": 900.0,
            "Ultrasound   Thyroid - 800 PHP": 800.0,
            "2D Echo - 2500 PHP": 2500.0,
            "ECG - 600 PHP": 600.0,
            "CT Scan (Plain) - 6000 PHP": 6000.0,
            "MRI (Plain) - 10000 PHP": 10000.0,
            "Mammogram - 2000 PHP": 2000.0,
            "Wound Dressing - 300 PHP": 300.0,
            "Nebulization - 200 PHP": 200.0,
            "Injection Service - 200 PHP": 200.0,
            "Suturing (small wound) - 1000 PHP": 1000.0,
            "Ear Cleaning - 400 PHP": 400.0,
            "Incision and Drainage - 800 PHP": 800.0,
            "ECG with Interpretation - 800 PHP": 800.0,
            "Cast / Splint Application - 1000 PHP": 1000.0,
            "Pap Smear - 500 PHP": 500.0,
            "Pregnancy Test (Urine) - 200 PHP": 200.0,
            "Medical Certificate - 250 PHP": 250.0,
            "Vital Signs Check - 100 PHP": 100.0,
            "ECG Print Request - 150 PHP": 150.0,
            "X-Ray CD Copy - 150 PHP": 150.0,
            "Laboratory Results Printing - 100 PHP": 100.0,
            "Doctor Follow-Up Consultation - 300 PHP": 300.0,
            "Teleconsultation - 400 PHP": 400.0,
            "Nutritional Counseling - 500 PHP": 500.0,
            "Family Planning Consultation - 400 PHP": 400.0,
            "Vaccination Service (Service Fee) - 400 PHP": 400.0,
        }  # (id, patient, doctor, schedule, notes, barcode, is_paid)

    def _connect(self):
        return sqlite3.connect(DB_NAME)

    def _clear(self):
        self.barcode_entry.delete(0, "end")
        for lbl in self.detail_labels.values():
            lbl.configure(text="-")
        self.amount_entry.delete(0, "end")
        self.paid_entry.delete(0, "end")
        self.change_label.configure(text="Change: -")
        self.current_record = None

    def _lookup(self):
        code = self.barcode_entry.get().strip()
        if not code:
            messagebox.showwarning("POS", "Please enter or scan a barcode.")
            return

        conn = self._connect()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT id, patient_name, doctor_name, schedule, COALESCE(notes, ''), barcode, COALESCE(is_paid, 0)
                FROM appointments
                WHERE barcode = ?
                """,
                (code,),
            )
            row = cur.fetchone()
        finally:
            conn.close()

        if row is None:
            messagebox.showerror("POS", "No appointment found for that barcode.")
            self._clear()
            self.barcode_entry.insert(0, code)
            return

        rid, patient, doctor, schedule, notes, barcode, is_paid = row
        self.current_record = row

        # Fill detail labels
        self.detail_labels["barcode"].configure(text=barcode or code)
        self.detail_labels["patient"].configure(text=patient)
        self.detail_labels["doctor"].configure(text=doctor)
        try:
            dt = datetime.strptime(schedule, "%Y-%m-%d %H:%M")
            self.detail_labels["date"].configure(text=dt.strftime("%Y-%m-%d"))
            self.detail_labels["time"].configure(text=dt.strftime("%I:%M %p"))
        except Exception:
            self.detail_labels["date"].configure(text=schedule.split()[0] if " " in schedule else schedule)
            self.detail_labels["time"].configure(text=schedule.split()[1] if " " in schedule else "-")
        self.detail_labels["notes"].configure(text=notes or "-")
        self.detail_labels["paid"].configure(text="Yes" if is_paid else "No")

        # Auto-compute total amount based on the service encoded in notes
        price = self._extract_price_from_notes(notes)
        self.amount_entry.delete(0, "end")
        if price is not None:
            self.amount_entry.insert(0, f"{price:.2f}")

        if is_paid:
            messagebox.showinfo("POS", "This appointment is already marked as paid.")

    def _update_change(self):
        """Update the change label in realtime based on total and amount paid."""
        total_str = self.amount_entry.get().strip()
        paid_str = self.paid_entry.get().strip()

        try:
            total = float(total_str) if total_str else 0.0
            paid = float(paid_str) if paid_str else 0.0
        except ValueError:
            self.change_label.configure(text="Change: -")
            return

        if paid >= total and total > 0:
            change = paid - total
            self.change_label.configure(text=f"Change: {change:.2f}")
        else:
            self.change_label.configure(text="Change: -")

    def _extract_price_from_notes(self, notes: str | None) -> float | None:
        """Derive the service price from the 'About:' portion of the notes field."""
        if not notes:
            return None

        about_value = None
        parts = [p.strip() for p in notes.split("|")]
        for part in parts:
            if part.startswith("About:"):
                about_value = part[len("About:") :].strip()
                break

        if not about_value:
            return None

        # First try exact match against known services
        if about_value in self.service_prices:
            return self.service_prices[about_value]

        import re

        # Fallback: extract a "123 PHP" style price
        m = re.search(r"(\d[\d,]*)\s*PHP", about_value)
        if not m:
            return None
        raw = m.group(1).replace(",", "")
        try:
            return float(raw)
        except ValueError:
            return None

    def _confirm_payment(self):
        if self.current_record is None:
            messagebox.showwarning("POS", "Verify a barcode first.")
            return

        try:
            total = float(self.amount_entry.get().strip()) if self.amount_entry.get().strip() else 0.0
            paid = float(self.paid_entry.get().strip()) if self.paid_entry.get().strip() else 0.0
        except ValueError:
            messagebox.showwarning("POS", "Amount fields must be numbers.")
            return

        if paid < total:
            messagebox.showwarning("POS", "Amount paid is less than total.")
            return

        change = paid - total
        self.change_label.configure(text=f"Change: {change:.2f}")

        # Build review modal before finalizing payment
        rid, patient, doctor, schedule, notes, barcode, is_paid = self.current_record

        review = ctk.CTkToplevel(self)
        review.title("")
        review.geometry("450x600")
        review.transient(self)
        review.grab_set()
        review.focus()

        # Header
        ctk.CTkLabel(
            review, 
            text="Review Receipt", 
            font=("Segoe UI", 22, "bold")
        ).pack(anchor="w", padx=30, pady=(25, 5))

        ctk.CTkLabel(
            review,
            text="Please verify the details below.",
            font=("Segoe UI", 14),
            text_color="gray70"
        ).pack(anchor="w", padx=30, pady=(0, 15))

        # Content Container
        container = ctk.CTkScrollableFrame(review, corner_radius=0, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=0, pady=(0, 80))
        container.grid_columnconfigure(0, weight=1)

        def _add_review_row(label, value, idx, highlight=False):
            frame = ctk.CTkFrame(
                container, 
                corner_radius=6, 
                fg_color="transparent", 
                border_width=1, 
                border_color="#3d3d3d"
            )
            frame.grid(row=idx, column=0, sticky="ew", padx=30, pady=6)
            frame.grid_columnconfigure(1, weight=1)
            
            ctk.CTkLabel(
                frame, 
                text=label, 
                font=("Segoe UI", 12, "bold"), 
                text_color="gray70",
                width=80,
                anchor="w"
            ).grid(row=0, column=0, padx=15, pady=12, sticky="w")

            val_font = ("Segoe UI", 14, "bold") if highlight else ("Segoe UI", 13)
            val_color = "#16a34a" if highlight else "gray90"

            ctk.CTkLabel(
                frame, 
                text=value, 
                font=val_font,
                text_color=val_color,
                anchor="w",
                justify="left"
            ).grid(row=0, column=1, padx=(5, 15), pady=12, sticky="w")

        # Prepare Schedule Text
        try:
            dt = datetime.strptime(schedule, "%Y-%m-%d %H:%M")
            sched_text = dt.strftime("%Y-%m-%d %I:%M %p")
        except Exception:
            sched_text = schedule

        _add_review_row("Barcode:", barcode or "-", 0)
        _add_review_row("Patient:", patient, 1)
        _add_review_row("Doctor:", doctor, 2)
        _add_review_row("Schedule:", sched_text, 3)
        _add_review_row("Total:", f"₱{total:,.2f}", 4)
        _add_review_row("Paid:", f"₱{paid:,.2f}", 5)
        _add_review_row("Change:", f"₱{change:,.2f}", 6, highlight=True)

        # Buttons (pinned to bottom)
        btn_frame = ctk.CTkFrame(review, fg_color="transparent")
        btn_frame.place(relx=0.5, rely=0.92, anchor="center", relwidth=1)
        
        def _cancel():
            review.destroy()

        def _ok():
            # Finalize payment in DB
            conn = self._connect()
            cur = conn.cursor()
            try:
                cur.execute(
                    "UPDATE appointments SET is_paid = 1, amount_paid = ? WHERE id = ?",
                    (paid, rid),
                )
                conn.commit()
            finally:
                conn.close()

            if "paid" in self.detail_labels:
                self.detail_labels["paid"].configure(text="Yes")

            # Create receipt folder and file
            project_root = os.path.dirname(os.path.abspath(DB_NAME))
            receipts_dir = os.path.join(project_root, "CASHIER_RECEIPT")
            os.makedirs(receipts_dir, exist_ok=True)

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_barcode = (barcode or "NO_BARCODE").replace(os.sep, "_")
            filename = f"receipt_{safe_barcode}_{ts}.bmp"
            filepath = os.path.join(receipts_dir, filename)

            # Extract Service Name for Particulars
            service_name = "Medical Services"
            if notes:
                parts = [p.strip() for p in notes.split("|")]
                for part in parts:
                    if part.startswith("About:"):
                        service_name = part[len("About:") :].strip()
                        break
            
            # Lines for invoice-style layout
            # The receiver function will just print these in order. 
            lines = [
                "CASHIER INVOICE",
                f"Date/Time: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}",
                "---",
                f"Barcode:   {barcode or '-'}",
                f"Patient:   {patient}",
                f"Doctor:    {doctor}",
                f"Schedule:  {sched_text}",
                "---",
                "PARTICULARS",
                f"{service_name}",
                "---",
                f"Total Amount:    ₱{total:,.2f}",
                f"Payment Made:    ₱{paid:,.2f}",
                f"Change:          ₱{change:,.2f}",
                "---",
                "Thank you for trusting Medisked!",
            ]

            _write_receipt_image(filepath, lines)

            # Show a checkmark or success instead of just "Printing"
            printing = ctk.CTkToplevel(self)
            printing.title("")
            printing.geometry("300x150")
            printing.transient(self)
            printing.grab_set()
            
            # Center
            printing.update_idletasks()
            pw = 300
            ph = 150
            mx = self.winfo_rootx() + (self.winfo_width() - pw) // 2
            my = self.winfo_rooty() + (self.winfo_height() - ph) // 2
            printing.geometry(f"{pw}x{ph}+{mx}+{my}")

            ctk.CTkLabel(printing, text="✅ Payment Successful\n& Receipt Printed!", font=("Segoe UI", 16, "bold"), text_color="#16a34a").pack(expand=True, pady=20)
            
            def _finish_printing():
                printing.destroy()
                review.destroy()
                # Reset all POS fields
                self._clear()

            printing.after(1500, _finish_printing)

            # Log cashier payment confirmation
            try:
                top = self.winfo_toplevel()
                username = getattr(top, "username", "cashier")
                detail = (
                    f"Confirmed payment for appointment #{rid} "
                    f"(barcode={barcode or '-'}, total={total:.2f}, paid={paid:.2f}, change={change:.2f})"
                )
                log_activity(username, "cashier", "confirm_payment", detail)
            except Exception:
                pass

        cancel_btn = ctk.CTkButton(
            btn_frame, 
            text="Cancel", 
            width=100,
            fg_color="transparent",
            border_width=1,
            border_color="#d97706",
            text_color="#d97706",
            hover_color="#332200", 
            command=_cancel
        )
        cancel_btn.pack(side="left", padx=20, expand=True)

        ok_btn = ctk.CTkButton(
            btn_frame, 
            text="Confirm Print", 
            width=140, 
            fg_color="#16a34a", 
            hover_color="#15803d", 
            command=_ok
        )
        ok_btn.pack(side="right", padx=20, expand=True)

        # Center the review window
        review.update_idletasks()
        mw = self.winfo_toplevel().winfo_width()
        mh = self.winfo_toplevel().winfo_height()
        mx = self.winfo_toplevel().winfo_rootx()
        my = self.winfo_toplevel().winfo_rooty()
        rw = 450
        rh = 600
        rx = mx + (mw - rw) // 2
        ry = my + (mh - rh) // 2
        review.geometry(f"{rw}x{rh}+{rx}+{ry}")


def _write_receipt_image(filepath: str, lines: list[str]) -> None:
    """Render a MEDISKED hospital-style cashier invoice as a BMP image.

    If Pillow is not installed, fall back to writing a .txt file next to the
    intended image path.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont  # type: ignore
    except Exception:
        # Fallback: save plain text receipt
        fallback = filepath[:-4] + ".txt" if filepath.lower().endswith(".bmp") else filepath + ".txt"
        try:
            with open(fallback, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
        except Exception:
            pass
        return

    # Canvas
    width = 600
    height = 1000  # Adjusted height for linear content
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        title_font = ImageFont.truetype("arial.ttf", 28)
        header_font = ImageFont.truetype("arial.ttf", 14)
        text_font = ImageFont.truetype("arial.ttf", 13)
        bold_font = ImageFont.truetype("arialbd.ttf", 13)
    except Exception:
        title_font = header_font = text_font = bold_font = ImageFont.load_default()

    x_margin = 40
    y = 50

    # Header: MEDISKED hospital info
    draw.text((x_margin, y), "MEDISKED HOSPITAL", fill="black", font=title_font)
    y += 40
    # Updated Address/Contact
    draw.text((x_margin, y), "ADDRESS: Davao City", fill="black", font=header_font)
    y += 20
    draw.text((x_margin, y), "CONTACT: 09092313242", fill="black", font=header_font)
    y += 40

    # Draw a thin separator line
    draw.line((x_margin, y, width - x_margin, y), fill="black", width=2)
    y += 30

    # Body
    for line in lines:
        if line == "---":
            # Separator
            y += 10
            draw.line((x_margin, y, width - x_margin, y), fill="gray", width=1)
            y += 20
            continue
        
        # Check for key:value pairs to bold keys (e.g., "Patient: John Doe")
        if ":" in line:
            # We want to bold the label part but keep the value normal
            key, val = line.split(":", 1)
            label_text = key.strip() + ":"
            
            draw.text((x_margin, y), label_text, fill="black", font=bold_font)
            
            # calculate width to offset value
            bbox = draw.textbbox((0,0), label_text, font=bold_font)
            label_w = bbox[2] - bbox[0]
            
            draw.text((x_margin + label_w + 12, y), val.strip(), fill="black", font=text_font)
        else:
            # Plain text (like headers "PARTICULARS" or footer)
            # If it's a known header or footer, make it bold or centered?
            if line in ["CASHIER INVOICE", "PARTICULARS"]:
                 draw.text((x_margin, y), line, fill="black", font=bold_font)
            else:
                 draw.text((x_margin, y), line, fill="black", font=text_font)
        
        y += 30

    try:
        img.save(filepath, format="BMP")
    except Exception:
        # If saving BMP fails, attempt text fallback
        fallback = filepath[:-4] + ".txt" if filepath.lower().endswith(".bmp") else filepath + ".txt"
        try:
            with open(fallback, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
        except Exception:
            pass
