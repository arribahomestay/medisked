import customtkinter as ctk
import sqlite3
from datetime import datetime
import os

from tkinter import messagebox

from database import DB_NAME


class CashierPOSPage(ctk.CTkFrame):
    """Simple POS interface for cashiers: verify APPT barcode and mark as paid."""

    def __init__(self, master):
        super().__init__(master, corner_radius=0)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

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
            "Ultrasound  Whole Abdomen - 1000 PHP": 1000.0,
            "Ultrasound  Pelvic / OB - 900 PHP": 900.0,
            "Ultrasound  Thyroid - 800 PHP": 800.0,
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
        }

        title = ctk.CTkLabel(
            self,
            text="POS - Payments",
            font=("Segoe UI", 24, "bold"),
        )
        title.grid(row=0, column=0, padx=30, pady=(10, 4), sticky="w")

        content = ctk.CTkFrame(self, corner_radius=10)
        content.grid(row=1, column=0, padx=30, pady=(0, 24), sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        # Barcode / receipt row
        top_row = ctk.CTkFrame(content, fg_color="transparent")
        top_row.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        top_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(top_row, text="Receipt / Barcode").grid(row=0, column=0, padx=(0, 8), pady=(0, 4), sticky="w")

        barcode_row = ctk.CTkFrame(top_row, fg_color="transparent")
        barcode_row.grid(row=1, column=0, sticky="ew")
        barcode_row.grid_columnconfigure(0, weight=1)

        self.barcode_entry = ctk.CTkEntry(barcode_row, placeholder_text="Scan or type APPT- code here...")
        self.barcode_entry.grid(row=0, column=0, padx=(0, 8), pady=(0, 0), sticky="ew")
        self.barcode_entry.bind("<Return>", lambda _e: self._lookup())

        verify_btn = ctk.CTkButton(
            barcode_row,
            text="Verify",
            width=90,
            fg_color="#16a34a",
            hover_color="#15803d",
            command=self._lookup,
        )
        verify_btn.grid(row=0, column=1, padx=(0, 0))

        # Details + payment area
        body = ctk.CTkFrame(content, corner_radius=10)
        body.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="nsew")
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(5, weight=1)

        # Appointment details labels
        self.detail_labels = {}
        fields = ["Barcode", "Patient", "Doctor", "Date", "Time", "Notes", "Paid"]
        for idx, label in enumerate(fields):
            ctk.CTkLabel(body, text=f"{label}:", font=("Segoe UI", 12, "bold")).grid(
                row=idx, column=0, padx=12, pady=3, sticky="w"
            )
            val_lbl = ctk.CTkLabel(body, text="-", font=("Segoe UI", 12), anchor="w", justify="left")
            val_lbl.grid(row=idx, column=1, padx=12, pady=3, sticky="w")
            self.detail_labels[label.lower()] = val_lbl

        # Payment row
        payment_row = ctk.CTkFrame(body, fg_color="transparent")
        payment_row.grid(row=len(fields), column=0, columnspan=2, padx=12, pady=(10, 4), sticky="ew")
        payment_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(payment_row, text="Total amount").grid(row=0, column=0, padx=(0, 8), pady=2, sticky="w")
        self.amount_entry = ctk.CTkEntry(payment_row)
        self.amount_entry.grid(row=0, column=1, padx=(0, 8), pady=2, sticky="ew")

        ctk.CTkLabel(payment_row, text="Amount paid").grid(row=1, column=0, padx=(0, 8), pady=2, sticky="w")
        self.paid_entry = ctk.CTkEntry(payment_row)
        self.paid_entry.grid(row=1, column=1, padx=(0, 8), pady=2, sticky="ew")

        self.change_label = ctk.CTkLabel(payment_row, text="Change: -", font=("Segoe UI", 11))
        self.change_label.grid(row=2, column=0, columnspan=2, padx=(0, 8), pady=(4, 2), sticky="w")

        # Realtime change computation when user types
        self.amount_entry.bind("<KeyRelease>", lambda _e: self._update_change())
        self.paid_entry.bind("<KeyRelease>", lambda _e: self._update_change())

        # Bottom actions
        actions = ctk.CTkFrame(content, fg_color="transparent")
        actions.grid(row=2, column=0, padx=16, pady=(0, 12), sticky="e")

        clear_btn = ctk.CTkButton(
            actions,
            text="Clear",
            width=80,
            fg_color="#4b5563",
            hover_color="#374151",
            command=self._clear,
        )
        clear_btn.grid(row=0, column=0, padx=(0, 8))

        pay_btn = ctk.CTkButton(
            actions,
            text="Confirm payment",
            width=150,
            fg_color="#16a34a",
            hover_color="#15803d",
            command=self._confirm_payment,
        )
        pay_btn.grid(row=0, column=1)

        self.current_record = None  # (id, patient, doctor, schedule, notes, barcode, is_paid)

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
        review.title("Review Receipt")
        review.geometry("420x320")
        review.transient(self)
        review.grab_set()
        review.focus()

        review.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(review, text="Barcode:").grid(row=0, column=0, padx=20, pady=(20, 4), sticky="w")
        ctk.CTkLabel(review, text=barcode or "-").grid(row=0, column=1, padx=20, pady=(20, 4), sticky="w")

        ctk.CTkLabel(review, text="Patient:").grid(row=1, column=0, padx=20, pady=4, sticky="w")
        ctk.CTkLabel(review, text=patient).grid(row=1, column=1, padx=20, pady=4, sticky="w")

        ctk.CTkLabel(review, text="Doctor:").grid(row=2, column=0, padx=20, pady=4, sticky="w")
        ctk.CTkLabel(review, text=doctor).grid(row=2, column=1, padx=20, pady=4, sticky="w")

        ctk.CTkLabel(review, text="Schedule:").grid(row=3, column=0, padx=20, pady=4, sticky="w")
        try:
            dt = datetime.strptime(schedule, "%Y-%m-%d %H:%M")
            sched_text = dt.strftime("%Y-%m-%d %I:%M %p")
        except Exception:
            sched_text = schedule
        ctk.CTkLabel(review, text=sched_text).grid(row=3, column=1, padx=20, pady=4, sticky="w")

        ctk.CTkLabel(review, text="Total:").grid(row=4, column=0, padx=20, pady=4, sticky="w")
        ctk.CTkLabel(review, text=f"{total:.2f}").grid(row=4, column=1, padx=20, pady=4, sticky="w")

        ctk.CTkLabel(review, text="Paid:").grid(row=5, column=0, padx=20, pady=4, sticky="w")
        ctk.CTkLabel(review, text=f"{paid:.2f}").grid(row=5, column=1, padx=20, pady=4, sticky="w")

        ctk.CTkLabel(review, text="Change:").grid(row=6, column=0, padx=20, pady=4, sticky="w")
        ctk.CTkLabel(review, text=f"{change:.2f}").grid(row=6, column=1, padx=20, pady=4, sticky="w")

        # Buttons row
        btn_row = ctk.CTkFrame(review, fg_color="transparent")
        btn_row.grid(row=7, column=0, columnspan=2, padx=20, pady=(16, 16), sticky="e")

        # Center the review window over the main cashier window
        review.update_idletasks()
        master = self.winfo_toplevel()
        master.update_idletasks()
        mx = master.winfo_rootx()
        my = master.winfo_rooty()
        mw = master.winfo_width()
        mh = master.winfo_height()
        ww = review.winfo_width()
        wh = review.winfo_height()
        x = mx + (mw - ww) // 2
        y = my + (mh - wh) // 2
        review.geometry(f"{ww}x{wh}+{x}+{y}")

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

            self.detail_labels["paid"].configure(text="Yes")

            # Create receipt folder and file
            project_root = os.path.dirname(os.path.dirname(__file__))
            receipts_dir = os.path.join(project_root, "CASHIER_RECEIPT")
            os.makedirs(receipts_dir, exist_ok=True)

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_barcode = (barcode or "NO_BARCODE").replace(os.sep, "_")
            filename = f"receipt_{safe_barcode}_{ts}.bmp"
            filepath = os.path.join(receipts_dir, filename)

            # Lines for invoice-style layout
            lines = [
                "MEDISKED: HOSPITAL SCHEDULING AND BILLING MANAGEMENT SYSTEM",
                "CASHIER INVOICE",
                "",
                f"Date/Time: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}",
                "",
                f"Barcode: {barcode or '-'}",
                f"Patient: {patient}",
                f"Doctor: {doctor}",
                f"Schedule: {sched_text}",
                "",
                f"Total amount: {total:.2f}",
                f"Amount paid: {paid:.2f}",
                f"Change: {change:.2f}",
            ]

            _write_receipt_image(filepath, lines)

            # Show a short 'PRINTING RECEIPT' window, then close and reset
            printing = ctk.CTkToplevel(self)
            printing.title("Printing")
            printing.geometry("260x120")
            printing.transient(self)
            printing.grab_set()

            msg = ctk.CTkLabel(printing, text="PRINTING RECEIPT...", font=("Segoe UI", 13, "bold"))
            msg.pack(expand=True, padx=20, pady=20)

            # Center printing window as well
            printing.update_idletasks()
            master = self.winfo_toplevel()
            master.update_idletasks()
            mx = master.winfo_rootx()
            my = master.winfo_rooty()
            mw = master.winfo_width()
            mh = master.winfo_height()
            pw = printing.winfo_width()
            ph = printing.winfo_height()
            px = mx + (mw - pw) // 2
            py = my + (mh - ph) // 2
            printing.geometry(f"{pw}x{ph}+{px}+{py}")

            def _finish_printing():
                printing.destroy()
                review.destroy()
                messagebox.showinfo("POS", "Payment confirmed, marked as paid, and receipt saved.")
                # Reset all POS fields after successful payment
                self._clear()

            # Close the printing window after a short delay (e.g., 1 second)
            printing.after(1000, _finish_printing)

        cancel_btn = ctk.CTkButton(btn_row, text="Cancel", width=90, fg_color="#4b5563", hover_color="#374151", command=_cancel)
        cancel_btn.grid(row=0, column=0, padx=(0, 8))

        ok_btn = ctk.CTkButton(btn_row, text="OK", width=90, fg_color="#16a34a", hover_color="#15803d", command=_ok)
        ok_btn.grid(row=0, column=1)


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
    width = 800
    height = 1000
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    # Fonts
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

    # Draw a thin separator line
    draw.line((x_margin, y, width - x_margin, y), fill="black", width=1)
    y += 20

    # Use the provided lines to fill patient/visit and payment info
    for line in lines:
        draw.text((x_margin, y), line, fill="black", font=text_font)
        y += 20

    # Simple table frame for totals at the bottom
    table_top = height - 260
    table_left = x_margin
    table_right = width - x_margin
    table_bottom = height - 80

    # Outer rectangle
    draw.rectangle((table_left, table_top, table_right, table_bottom), outline="black", width=1)

    # Columns: PARTICULARS | AMOUNT
    mid_x = table_left + int((table_right - table_left) * 0.55)
    draw.line((mid_x, table_top, mid_x, table_bottom), fill="black", width=1)

    # Header row
    row_h = 28
    draw.line((table_left, table_top + row_h, table_right, table_top + row_h), fill="black", width=1)
    draw.text((table_left + 8, table_top + 6), "PARTICULARS", fill="black", font=header_font)
    draw.text((mid_x + 8, table_top + 6), "AMOUNT", fill="black", font=header_font)

    # Label rows for subtotal/payment/total
    y_row = table_top + row_h
    for label in ["SUBTOTAL", "PAYMENT MADE", "TOTAL BILL"]:
        y_row += row_h
        draw.line((table_left, y_row, table_right, y_row), fill="black", width=1)
        draw.text((table_left + 8, y_row - row_h + 6), label, fill="black", font=text_font)

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
