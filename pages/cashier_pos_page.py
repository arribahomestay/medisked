import customtkinter as ctk
import sqlite3
from datetime import datetime
import os

from tkinter import messagebox

from database import DB_NAME, log_activity


class CashierPOSPage(ctk.CTkFrame):
    """Simple POS interface for cashiers: verify APPT barcode and mark as paid."""

    def __init__(self, master):
        super().__init__(master, corner_radius=10, fg_color="transparent")

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header 
        # (Assuming parent handles the main page title, but we can add a local one if needed)
        # Actually in other modern pages, we have a header strip. Let's add that.

        # 1. Page Header (Doctor style)
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 10))
        
        ctk.CTkLabel(
            header_frame, 
            text="Point of Sale", 
            font=("Inter", 24, "bold"),
            text_color="white"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            header_frame, 
            text="Scan verify barcodes and process payments.", 
            font=("Inter", 13),
            text_color="#94a3b8"
        ).pack(anchor="w")

        # 2. Main content container
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        main_content.grid_rowconfigure(0, weight=1)
        main_content.grid_columnconfigure(0, weight=3) # Left (Details)
        main_content.grid_columnconfigure(1, weight=2) # Right (Totals)

        # --- LEFT PANEL: Transaction Details (Slate Card) ---
        left_card = ctk.CTkFrame(main_content, corner_radius=16, fg_color="#1e293b")
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        left_card.grid_rowconfigure(2, weight=1)
        left_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left_card, 
            text="Transaction Details", 
            font=("Inter", 18, "bold"),
            text_color="white"
        ).grid(row=0, column=0, sticky="w", padx=25, pady=(25, 10))

        # Search Bar
        search_frame = ctk.CTkFrame(left_card, fg_color="transparent")
        search_frame.grid(row=1, column=0, sticky="ew", padx=25, pady=(0, 15))
        search_frame.grid_columnconfigure(0, weight=1)
        
        self.barcode_entry = ctk.CTkEntry(
            search_frame, 
            placeholder_text="Scan Appointment ID / Barcode...",
            height=45,
            font=("Inter", 14),
            border_width=0,
            fg_color="#334155",
            text_color="white",
            placeholder_text_color="#94a3b8"
        )
        self.barcode_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.barcode_entry.bind("<Return>", lambda _e: self._lookup())

        verify_btn = ctk.CTkButton(
            search_frame,
            text="Verify",
            width=100,
            height=45,
            fg_color="#3b82f6", # Blue 500
            hover_color="#2563eb",
            font=("Inter", 13, "bold"),
            command=self._lookup
        )
        verify_btn.grid(row=0, column=1)

        # Details List (Scrollable)
        self.details_scroll = ctk.CTkScrollableFrame(left_card, fg_color="transparent")
        self.details_scroll.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 25))
        self.details_scroll.grid_columnconfigure(0, weight=1)

        self.detail_labels = {}
        fields = ["Barcode", "Patient", "Doctor", "Date", "Time", "Notes", "Paid"]
        
        for idx, label in enumerate(fields):
            row_f = ctk.CTkFrame(self.details_scroll, corner_radius=10, fg_color="#334155", height=50) # Slate 700 rows
            row_f.grid(row=idx, column=0, sticky="ew", pady=5, padx=5)
            row_f.grid_columnconfigure(1, weight=1)
            
            ctk.CTkLabel(
                row_f, 
                text=label.upper(), 
                font=("Inter", 11, "bold"), 
                text_color="#94a3b8", 
                width=80, 
                anchor="w"
            ).grid(row=0, column=0, padx=20, pady=15)
            
            val_lbl = ctk.CTkLabel(
                row_f, 
                text="-", 
                font=("Inter", 13, "bold"), 
                text_color="white",
                anchor="w", 
                justify="left",
                wraplength=350
            )
            val_lbl.grid(row=0, column=1, padx=(0, 10), pady=15, sticky="w")
            
            self.detail_labels[label.lower()] = val_lbl


        # --- RIGHT PANEL: Actions (Slate Card) ---
        right_card = ctk.CTkFrame(main_content, corner_radius=16, fg_color="#1e293b")
        right_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        right_card.grid_rowconfigure(0, weight=1)
        right_card.grid_rowconfigure(2, weight=0) # Buttons
        right_card.grid_columnconfigure(0, weight=1)

        # Totals Section (Centered vertically in top half if possible, or just top)
        totals_frame = ctk.CTkFrame(right_card, fg_color="transparent")
        totals_frame.grid(row=0, column=0, sticky="nsew", padx=30, pady=40)
        totals_frame.grid_columnconfigure(0, weight=1)

        # Total Due
        ctk.CTkLabel(totals_frame, text="Total Amount Due", font=("Inter", 14), text_color="#cbd5e1").pack(anchor="w", pady=(0, 5))
        self.amount_entry = ctk.CTkEntry(
            totals_frame, 
            height=55, 
            font=("Inter", 28, "bold"),
            justify="right",
            fg_color="#0f172a", # Darker input
            border_width=1,
            border_color="#334155",
            text_color="white"
        )
        self.amount_entry.pack(fill="x", pady=(0, 20))

        # Amount Tendered
        ctk.CTkLabel(totals_frame, text="Amount Tendered", font=("Inter", 14), text_color="#cbd5e1").pack(anchor="w", pady=(0, 5))
        self.paid_entry = ctk.CTkEntry(
            totals_frame, 
            height=55, 
            font=("Inter", 28, "bold"),
            justify="right",
            fg_color="#0f172a",
            border_width=1,
            border_color="#334155",
            text_color="#4ade80" # Greenish text for paid
        )
        self.paid_entry.pack(fill="x", pady=(0, 20))
        
        # Change Display
        self.change_label = ctk.CTkLabel(
            totals_frame, 
            text="Change: ₱0.00", 
            font=("Inter", 24, "bold"),
            text_color="#4ade80" # Green 400
        )
        self.change_label.pack(anchor="e", pady=10)

        # Bindings
        self.amount_entry.bind("<KeyRelease>", lambda _e: self._update_change())
        self.paid_entry.bind("<KeyRelease>", lambda _e: self._update_change())

        # Buttons Grid (Bottom of Right Panel)
        actions_grid = ctk.CTkFrame(right_card, fg_color="transparent")
        actions_grid.grid(row=2, column=0, sticky="ew", padx=30, pady=(0, 30))
        actions_grid.grid_columnconfigure(0, weight=1)
        actions_grid.grid_columnconfigure(1, weight=1)

        # Helper Actions
        self.btn_drawer = ctk.CTkButton(
            actions_grid,
            text="OPEN DRAWER",
            font=("Inter", 12, "bold"),
            fg_color="#3b82f6", # Blue
            hover_color="#2563eb",
            height=50,
            command=lambda: messagebox.showinfo("POS", "Cash drawer opened.")
        )
        self.btn_drawer.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=10)

        self.btn_cancel = ctk.CTkButton(
            actions_grid,
            text="CANCEL",
            font=("Inter", 12, "bold"),
            fg_color="#f59e0b", # Amber 500
            hover_color="#d97706",
            height=50,
            command=self._clear
        )
        self.btn_cancel.grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=10)

        # Primary Action
        self.btn_proceed = ctk.CTkButton(
            actions_grid,
            text="CONFIRM PAYMENT",
            font=("Inter", 15, "bold"),
            fg_color="#10b981", # Emerald 500
            hover_color="#059669", # Emerald 600
            height=60,
            command=self._confirm_payment
        )
        self.btn_proceed.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))

        self.current_record = None

        # Prices
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
        }

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
            self.change_label.configure(text=f"Change: ₱{change:,.2f}")
        else:
            self.change_label.configure(text="Change: -")

    def _extract_price_from_notes(self, notes: str | None) -> float | None:
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

        if about_value in self.service_prices:
            return self.service_prices[about_value]

        import re
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
        
        rid, patient, doctor, schedule, notes, barcode, is_paid = self.current_record

        # Review Modal (Themed)
        review = ctk.CTkToplevel(self)
        review.title("Review Payment")
        review.geometry("450x650")
        review.transient(self)
        review.grab_set()
        review.configure(fg_color="#0f172a") # Dark background
        
        # Center
        review.update_idletasks()
        mw = self.winfo_toplevel().winfo_width()
        mh = self.winfo_toplevel().winfo_height()
        mx = self.winfo_toplevel().winfo_rootx()
        my = self.winfo_toplevel().winfo_rooty()
        review.geometry(f"+{mx + (mw - 450)//2}+{my + (mh - 650)//2}")

        ctk.CTkLabel(review, text="Review Receipt", font=("Inter", 22, "bold"), text_color="white").pack(anchor="w", padx=30, pady=(25, 5))
        ctk.CTkLabel(review, text="Please verify details before printing.", font=("Inter", 14), text_color="#94a3b8").pack(anchor="w", padx=30, pady=(0, 20))

        content = ctk.CTkFrame(review, fg_color="#1e293b", corner_radius=16)
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        content.grid_columnconfigure(1, weight=1)

        def _row(i, k, v, big=False):
            f = ctk.CTkFrame(content, fg_color="transparent")
            f.grid(row=i, column=0, columnspan=2, sticky="ew", padx=15, pady=8)
            ctk.CTkLabel(f, text=k, font=("Inter", 13, "bold"), text_color="#94a3b8", width=100, anchor="w").pack(side="left")
            
            c = "white"
            ft = ("Inter", 14)
            if big:
                c = "#4ade80"
                ft = ("Inter", 16, "bold")
                
            ctk.CTkLabel(f, text=v, font=ft, text_color=c).pack(side="right")

        _row(0, "Barcode:", barcode or "-")
        _row(1, "Patient:", patient)
        _row(2, "Doctor:", doctor)
        
        try:
            dt = datetime.strptime(schedule, "%Y-%m-%d %H:%M")
            st = dt.strftime("%Y-%m-%d %I:%M %p")
        except: st = schedule
        
        _row(3, "Schedule:", st)
        
        # Separator
        div = ctk.CTkFrame(content, height=2, fg_color="#334155")
        div.grid(row=4, column=0, columnspan=2, sticky="ew", padx=15, pady=10)
        
        _row(5, "Total Due:", f"₱{total:,.2f}")
        _row(6, "Payment:", f"₱{paid:,.2f}")
        _row(7, "Change:", f"₱{change:,.2f}", True)

        # Buttons
        btns = ctk.CTkFrame(review, fg_color="transparent")
        btns.pack(fill="x", pady=30, padx=20)
        
        ctk.CTkButton(btns, text="Cancel", fg_color="transparent", border_width=1, border_color="#f59e0b", text_color="#f59e0b", hover_color="#334155", width=120, command=review.destroy).pack(side="left", expand=True)
        
        def _ok():
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

            # Receipt logic (kept same, just ensuring paths)
            project_root = os.path.dirname(os.path.abspath(DB_NAME))
            receipts_dir = os.path.join(project_root, "CASHIER_RECEIPT")
            os.makedirs(receipts_dir, exist_ok=True)

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_barcode = (barcode or "NO_BARCODE").replace(os.sep, "_")
            filename = f"receipt_{safe_barcode}_{ts}.bmp"
            filepath = os.path.join(receipts_dir, filename)

            service_name = "Medical Services"
            if notes:
                parts = [p.strip() for p in notes.split("|")]
                for part in parts:
                    if part.startswith("About:"):
                        service_name = part[len("About:") :].strip()
                        break
            
            lines = [
                "CASHIER INVOICE",
                f"Date/Time: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}",
                "---",
                f"Barcode:   {barcode or '-'}",
                f"Patient:   {patient}",
                f"Doctor:    {doctor}",
                f"Schedule:  {st}",
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

            # Success Popup
            printing = ctk.CTkToplevel(self)
            printing.title("")
            printing.geometry("300x150")
            printing.configure(fg_color="#0f172a")
            printing.transient(self)
            printing.grab_set()
            
            printing.update_idletasks()
            mx = self.winfo_rootx() + (self.winfo_width() - 300) // 2
            my = self.winfo_rooty() + (self.winfo_height() - 150) // 2
            printing.geometry(f"+{mx}+{my}")

            ctk.CTkLabel(printing, text="✅ Payment Successful", font=("Inter", 18, "bold"), text_color="#10b981").pack(expand=True)
            ctk.CTkLabel(printing, text="Receipt Saved.", font=("Inter", 12), text_color="#94a3b8").pack(pady=(0, 20))
            
            def _finish():
                printing.destroy()
                review.destroy()
                self._clear()

            printing.after(1500, _finish)
            
            # Log
            try:
                top = self.winfo_toplevel()
                un = getattr(top, "username", "cashier")
                log_activity(un, "cashier", "confirm_payment", f"Paid appt #{rid} ({barcode})")
            except: pass

        ctk.CTkButton(btns, text="Confirm & Print", fg_color="#10b981", hover_color="#059669", width=150, font=("Inter", 13, "bold"), command=_ok).pack(side="right", expand=True)


def _write_receipt_image(filepath: str, lines: list[str]) -> None:
    """Render a MEDISKED hospital-style cashier invoice as a BMP image."""
    try:
        from PIL import Image, ImageDraw, ImageFont  # type: ignore
    except Exception:
        fallback = filepath[:-4] + ".txt" if filepath.lower().endswith(".bmp") else filepath + ".txt"
        try:
            with open(fallback, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
        except Exception: pass
        return

    width = 600
    height = 1000
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("arial.ttf", 28)
        header_font = ImageFont.truetype("arial.ttf", 14)
        text_font = ImageFont.truetype("arial.ttf", 13)
        bold_font = ImageFont.truetype("arialbd.ttf", 13)
    except Exception:
        title_font = header_font = text_font = bold_font = ImageFont.load_default()

    x_margin = 40
    y = 50

    draw.text((x_margin, y), "MEDISKED HOSPITAL", fill="black", font=title_font)
    y += 40
    draw.text((x_margin, y), "ADDRESS: Davao City", fill="black", font=header_font)
    y += 20
    draw.text((x_margin, y), "CONTACT: 09092313242", fill="black", font=header_font)
    y += 40

    draw.line((x_margin, y, width - x_margin, y), fill="black", width=2)
    y += 30

    for line in lines:
        if line == "---":
            y += 10
            draw.line((x_margin, y, width - x_margin, y), fill="gray", width=1)
            y += 20
            continue
        
        if ":" in line:
            key, val = line.split(":", 1)
            label_text = key.strip() + ":"
            draw.text((x_margin, y), label_text, fill="black", font=bold_font)
            bbox = draw.textbbox((0,0), label_text, font=bold_font)
            label_w = bbox[2] - bbox[0]
            draw.text((x_margin + label_w + 12, y), val.strip(), fill="black", font=text_font)
        else:
            if line in ["CASHIER INVOICE", "PARTICULARS"]:
                 draw.text((x_margin, y), line, fill="black", font=bold_font)
            else:
                 draw.text((x_margin, y), line, fill="black", font=text_font)
        y += 30

    try:
        img.save(filepath, format="BMP")
    except Exception:
        fallback = filepath[:-4] + ".txt"
        try:
            with open(fallback, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
        except: pass
