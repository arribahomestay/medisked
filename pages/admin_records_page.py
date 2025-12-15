import customtkinter as ctk
import sqlite3
import csv
from datetime import datetime

from tkinter import filedialog, messagebox, Menu
from database import DB_NAME, log_activity


class AdminRecordsPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0, fg_color="transparent")

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header & Controls Container as a Floating Card
        controls_card = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=16) # Slate 800
        controls_card.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        controls_card.grid_columnconfigure(0, weight=1)
        # Controls layout
        controls_card.grid_columnconfigure(1, weight=0)

        # Title & Subtitle Group
        title_frame = ctk.CTkFrame(controls_card, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        title = ctk.CTkLabel(
            title_frame,
            text="All Records", 
            font=("Inter", 20, "bold"),
            text_color="white"
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_frame,
            text="Manage all patient appointments and history.",
            font=("Inter", 13),
            text_color="#94a3b8"
        )
        subtitle.pack(anchor="w", pady=(2, 0))

        # Action Buttons Group
        actions_frame = ctk.CTkFrame(controls_card, fg_color="transparent")
        actions_frame.grid(row=0, column=1, padx=20, pady=20, sticky="e")

        self.search_entry = ctk.CTkEntry(
            actions_frame,
            placeholder_text="Search patient or doctor...",
            width=200,
            height=36,
            corner_radius=8,
            border_width=0,
            fg_color="#334155", # Slate 700
            text_color="white",
            placeholder_text_color="#94a3b8"
        )
        self.search_entry.pack(side="left", padx=(0, 10))

        self.refresh_button = ctk.CTkButton(
            actions_frame,
            text="Refresh",
            width=80,
            height=36,
            corner_radius=8,
            fg_color="#3b82f6", # Blue
            hover_color="#2563eb",
            font=("Inter", 13, "bold"),
            command=self.reload_records,
        )
        self.refresh_button.pack(side="left", padx=(0, 10))

        self.clear_button = ctk.CTkButton(
            actions_frame,
            text="Clear",
            width=70,
            height=36,
            corner_radius=8,
            fg_color="#334155",
            hover_color="#475569",
            font=("Inter", 13),
            command=self.clear_filters,
        )
        self.clear_button.pack(side="left", padx=(0, 10))

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
        self.export_button.pack(side="left", padx=(0, 0))

        # 2. Results List Container
        # Instead of a simple frame, we use a dark container for the list
        list_container = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=16) # Slate 800
        list_container.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")
        list_container.grid_rowconfigure(1, weight=1)
        list_container.grid_columnconfigure(0, weight=1)

        # Header Row for List
        header_row = ctk.CTkFrame(list_container, fg_color="transparent", height=40)
        # Match row padding (5px left) + Scrollbar compensation on right (~20px)
        header_row.grid(row=0, column=0, sticky="ew", padx=(5, 20), pady=(10, 0))
        
        # Configure columns with uniform group for data columns to enforce equal width
        header_row.grid_columnconfigure(0, weight=0, minsize=60)  # ID
        header_row.grid_columnconfigure((1, 2, 3), weight=1, uniform="data_cols") # Patient, Doctor, Schedule
        header_row.grid_columnconfigure(4, weight=0, minsize=100) # Status
        header_row.grid_columnconfigure(5, weight=0, minsize=100) # Paid
        header_row.grid_columnconfigure(6, weight=0, minsize=140) # Actions

        def _hlabel(col, text, align="w", px=10):
            lbl = ctk.CTkLabel(
                header_row, 
                text=text.upper(), 
                font=("Inter", 11, "bold"), 
                text_color="#64748b",
                anchor=align
            )
            lbl.grid(row=0, column=col, sticky="ew", padx=px)
        
        _hlabel(0, "#ID")
        _hlabel(1, "PATIENT")
        _hlabel(2, "DOCTOR")
        _hlabel(3, "SCHEDULE")
        _hlabel(4, "STATUS")
        _hlabel(5, "PAID")
        _hlabel(6, "ACTIONS", "e")

        # Divider (Optional)
        # div = ctk.CTkFrame(list_container, height=2, fg_color="#334155")
        # div.grid(row=0, column=0, sticky="ew", pady=(40, 0), padx=20) 
        # Using pady to push it below the header row labels roughly

        self.table_frame = ctk.CTkScrollableFrame(list_container, corner_radius=0, fg_color="transparent")
        self.table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(10, 10))
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
            "SELECT id, patient_name, doctor_name, schedule, notes, COALESCE(is_paid, 0), COALESCE(amount_paid, 0) FROM appointments ORDER BY id DESC"
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
            
            # Use a card-like row container for distinct look
            row_frame = ctk.CTkFrame(
                self.table_frame, 
                corner_radius=8,
                fg_color="#334155", # Slate 700 (Card background)
                border_width=1,
                border_color="#475569", # Slate 600 (Border)
                height=50
            ) 
            row_frame.grid(row=row_index, column=0, sticky="ew", pady=5, padx=5)
            
            # Grid layout matching the header EXACTLY
            row_frame.grid_columnconfigure(0, weight=0, minsize=60)  # ID
            row_frame.grid_columnconfigure((1, 2, 3), weight=1, uniform="data_cols") # Patient, Doctor, Schedule
            row_frame.grid_columnconfigure(4, weight=0, minsize=100) # Status
            row_frame.grid_columnconfigure(5, weight=0, minsize=100) # Paid
            row_frame.grid_columnconfigure(6, weight=0, minsize=140) # Actions

            # 1. ID
            ctk.CTkLabel(row_frame, text=str(rid), font=("Inter", 12), text_color="#cbd5e1", anchor="w").grid(row=0, column=0, sticky="ew", padx=10, pady=10)

            # 2. Patient
            ctk.CTkLabel(row_frame, text=patient, font=("Inter", 13, "bold"), text_color="white", anchor="w").grid(row=0, column=1, sticky="ew", padx=10)

            # 3. Doctor
            ctk.CTkLabel(row_frame, text=f"Dr. {doctor}", font=("Inter", 13), text_color="#94a3b8", anchor="w").grid(row=0, column=2, sticky="ew", padx=10)

            # 4. Schedule
            pretty_schedule = self._format_schedule(schedule)
            ctk.CTkLabel(row_frame, text=pretty_schedule, font=("Inter", 12), text_color="#cbd5e1", anchor="w").grid(row=0, column=3, sticky="ew", padx=10)

            # 5. Status
            status_text = "PAID" if is_paid else "UNPAID"
            status_color = "#10b981" if is_paid else "#ef4444" 
            ctk.CTkLabel(row_frame, text=status_text, font=("Inter", 11, "bold"), text_color=status_color, anchor="w").grid(row=0, column=4, sticky="ew", padx=10)

            # 6. Amount
            amount_text = f"₱{amount_paid:,.2f}" if amount_paid else "-"
            ctk.CTkLabel(row_frame, text=amount_text, font=("Inter", 12), text_color="white", anchor="w").grid(row=0, column=5, sticky="ew", padx=10)

            # 7. Actions
            actions_panel = ctk.CTkFrame(row_frame, fg_color="transparent")
            actions_panel.grid(row=0, column=6, sticky="e", padx=10)

            # Helper for icon-like small buttons
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

            del_btn = _action_btn("Del", "#ef4444", lambda r=rec: self._delete_record(r))
            del_btn.pack(side="left", padx=2)

            # Separator line at bottom of row
            sep = ctk.CTkFrame(self.table_frame, height=1, fg_color="#334155")
            sep.grid(row=row_index, column=0, sticky="ew", pady=(45, 0)) 
            # Place sep "behind" or "below" row_frame by adjusting row span or using a container?
            # Easiest way in a grid is just to make the row frame taller or put sep in next grid row.
            # But let's simplify: Just add a border to the generic frame if we want separators.
            # Actually, let's skip separators for a cleaner look if spacing is good, or put them inside row_frame.
            sep_inner = ctk.CTkFrame(row_frame, height=1, fg_color="#334155")
            sep_inner.place(relx=0, rely=0.95, relwidth=1.0, anchor="sw")


    def _show_row_menu(self, event, record):
        menu = Menu(self, tearoff=0)
        menu.add_command(label="View details", command=lambda r=record: self._view_details(r))
        menu.add_command(label="Edit", command=lambda r=record: self._edit_record(r))
        menu.add_command(label="Delete", command=lambda r=record: self._delete_record(r))
        menu.tk_popup(event.x_root, event.y_root)

    def _format_schedule(self, schedule_str: str) -> str:
        try:
            dt = datetime.strptime(schedule_str, "%Y-%m-%d %H:%M")
            return dt.strftime("%b %d, %I:%M %p") # Slightly shorter date format
        except Exception:
            return schedule_str

    def _view_details(self, record):
        rid, patient, doctor, schedule, notes, is_paid, amount_paid = record

        win = ctk.CTkToplevel(self)
        win.title("Appointment Details")
        win.geometry("500x550")
        win.transient(self)
        win.grab_set()
        
        # Center
        win.update_idletasks()
        try:
            x = self.winfo_rootx() + (self.winfo_width() - 500) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 550) // 2
            win.geometry(f"+{x}+{y}")
        except: pass
        
        win.configure(fg_color="#0f172a") # Dark background

        ctk.CTkLabel(win, text="Appointment Details", font=("Inter", 20, "bold"), text_color="white").pack(padx=24, pady=(24, 4), anchor="w")
        ctk.CTkLabel(win, text=f"ID: #{rid}", font=("Inter", 13), text_color="#64748b").pack(padx=24, pady=(0, 24), anchor="w")

        content = ctk.CTkFrame(win, fg_color="#1e293b", corner_radius=12)
        content.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        def _row(label, val):
            f = ctk.CTkFrame(content, fg_color="transparent")
            f.pack(fill="x", padx=16, pady=12)
            ctk.CTkLabel(f, text=label, font=("Inter", 13, "bold"), text_color="#94a3b8", width=100, anchor="w").pack(side="left")
            ctk.CTkLabel(f, text=val, font=("Inter", 13), text_color="white", wraplength=300, justify="left").pack(side="left", fill="x", expand=True)

        _row("Patient", patient)
        _row("Doctor", doctor)
        _row("Schedule", self._format_schedule(schedule))
        
        # Status
        st_frame = ctk.CTkFrame(content, fg_color="transparent")
        st_frame.pack(fill="x", padx=16, pady=12)
        ctk.CTkLabel(st_frame, text="Status", font=("Inter", 13, "bold"), text_color="#94a3b8", width=100, anchor="w").pack(side="left")
        
        st_txt = "PAID" if is_paid else "UNPAID"
        st_col = "#10b981" if is_paid else "#ef4444"
        ctk.CTkLabel(st_frame, text=st_txt, font=("Inter", 13, "bold"), text_color=st_col).pack(side="left")
        
        _row("Amount", f"₱{amount_paid:,.2f}" if amount_paid else "-")
        _row("Notes", notes or "No notes provided.")

        btn = ctk.CTkButton(win, text="Close", font=("Inter", 13), fg_color="#334155", hover_color="#475569", command=win.destroy)
        btn.pack(pady=(0, 24))

    def _edit_record(self, record):
        # Existing edit logic is functional, just needs a quick reskin if we want consistency
        # For brevity, let's keep logic but wrap in darker window
        rid, patient, doctor, schedule, notes, _is_paid, _amount_paid = record
        
        win = ctk.CTkToplevel(self)
        win.title(f"Edit Appointment #{rid}")
        win.geometry("520x450")
        win.configure(fg_color="#0f172a")
        win.transient(self)
        win.grab_set()

        # Center
        win.update_idletasks()
        try:
            x = self.winfo_rootx() + (self.winfo_width() - 520) // 2
            y = self.winfo_rooty() + (self.winfo_height() - 450) // 2
            win.geometry(f"+{x}+{y}")
        except: pass

        grid_frame = ctk.CTkFrame(win, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=24, pady=24)
        grid_frame.grid_columnconfigure(1, weight=1)

        def _entry(row, label, val):
            ctk.CTkLabel(grid_frame, text=label, font=("Inter", 13), text_color="#cbd5e1").grid(row=row, column=0, padx=(0, 16), pady=8, sticky="w")
            e = ctk.CTkEntry(grid_frame, fg_color="#1e293b", border_width=1, border_color="#334155", text_color="white")
            e.insert(0, val)
            e.grid(row=row, column=1, pady=8, sticky="ew")
            return e

        p_entry = _entry(0, "Patient", patient)
        d_entry = _entry(1, "Doctor", doctor)
        s_entry = _entry(2, "Schedule", schedule)

        # Meta parsing (simplified for UI)
        meta_note = notes or ""
        
        n_label = ctk.CTkLabel(grid_frame, text="Notes", font=("Inter", 13), text_color="#cbd5e1")
        n_label.grid(row=3, column=0, padx=(0, 16), pady=8, sticky="nw")
        n_entry = ctk.CTkTextbox(grid_frame, height=100, fg_color="#1e293b", border_width=1, border_color="#334155", text_color="white")
        n_entry.insert("1.0", meta_note)
        n_entry.grid(row=3, column=1, pady=8, sticky="nsew")

        def save():
            # Basic save logic mirroring original
            new_p = p_entry.get().strip()
            new_d = d_entry.get().strip()
            new_s = s_entry.get().strip()
            new_n = n_entry.get("1.0", "end").strip()
            
            if not new_p or not new_d or not new_s:
                messagebox.showwarning("Error", "Missing fields")
                return

            conn = sqlite3.connect(DB_NAME)
            try:
                cur = conn.cursor()
                cur.execute("UPDATE appointments SET patient_name=?, doctor_name=?, schedule=?, notes=? WHERE id=?", 
                            (new_p, new_d, new_s, new_n, rid))
                conn.commit()
            finally:
                conn.close()
            
            # Log
            try:
                 log_activity("admin", "admin", "edit_appointment", f"Edited #{rid}")
            except: pass

            win.destroy()
            self.reload_records()

        save_btn = ctk.CTkButton(win, text="Save Changes", font=("Inter", 13, "bold"), fg_color="#3b82f6", hover_color="#2563eb", command=save)
        save_btn.pack(pady=(0, 24))

    def _delete_record(self, record):
        rid, patient, doctor, schedule, _notes, _is_paid, _amount_paid = record
        if not messagebox.askyesno("Confirm Delete", f"Delete appointment #{rid}?"):
            return

        conn = sqlite3.connect(DB_NAME)
        try:
            conn.execute("DELETE FROM appointments WHERE id = ?", (rid,))
            conn.commit()
        finally:
            conn.close()
        
        self.reload_records()
        try:
            log_activity("admin", "admin", "delete_appointment", f"Deleted #{rid}")
        except: pass

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

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Patient", "Doctor", "Schedule", "Notes"])
                for rid, patient, doctor, schedule, notes, _is_paid, _amount_paid in filtered:
                    writer.writerow([rid, patient, doctor, self._format_schedule(schedule), notes or ""])
            messagebox.showinfo("Success", "Export successful.")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")

