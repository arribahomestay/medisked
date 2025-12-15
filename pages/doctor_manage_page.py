import customtkinter as ctk
import sqlite3
import calendar
from datetime import date
from tkinter import messagebox

from database import DB_NAME


class DoctorManagePage(ctk.CTkFrame):
    def __init__(self, master, doctor_id, doctor_name: str):
        super().__init__(master, corner_radius=0, fg_color="transparent")

        self.doctor_id = doctor_id
        self.doctor_name = doctor_name

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header
        header_card = ctk.CTkFrame(self, fg_color="transparent")
        header_card.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        ctk.CTkLabel(
            header_card,
            text="Manage Availability",
            font=("Inter", 20, "bold"),
            text_color="white"
        ).pack(anchor="w")

        ctk.CTkLabel(
            header_card,
            text=f"Set your working schedule, {self.doctor_name or 'Doctor'}",
            font=("Inter", 13),
            text_color="#94a3b8"
        ).pack(anchor="w")

        # 2. Main Content Card
        content = ctk.CTkFrame(self, corner_radius=16, fg_color="#1e293b")
        content.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=0) # Controls
        content.grid_rowconfigure(1, weight=0) # Calendar
        content.grid_rowconfigure(2, weight=1) # Details

        # Month Controls
        controls = ctk.CTkFrame(content, fg_color="transparent")
        controls.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        controls.grid_columnconfigure(1, weight=1)

        self.current_year = date.today().year
        self.current_month = date.today().month

        prev_btn = ctk.CTkButton(
            controls, text="<", width=40, height=32, 
            fg_color="#334155", hover_color="#475569", 
            font=("Inter", 14, "bold"), command=self._prev_month
        )
        prev_btn.grid(row=0, column=0, padx=(0, 10))

        self.month_label = ctk.CTkLabel(
            controls, text="", font=("Inter", 16, "bold"), text_color="white"
        )
        self.month_label.grid(row=0, column=1, sticky="w")

        next_btn = ctk.CTkButton(
            controls, text=">", width=40, height=32, 
            fg_color="#334155", hover_color="#475569", 
            font=("Inter", 14, "bold"), command=self._next_month
        )
        next_btn.grid(row=0, column=2, padx=(10, 0))

        # Calendar
        self.calendar_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.calendar_frame.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="ew")
        
        # Grid Init
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, wd in enumerate(days):
            self.calendar_frame.grid_columnconfigure(i, weight=1, uniform="cal_col")
            lbl = ctk.CTkLabel(self.calendar_frame, text=wd.upper(), font=("Inter", 11, "bold"), text_color="#94a3b8")
            lbl.grid(row=0, column=i, pady=(0, 10))

        # View Holder for Buttons: 6 rows x 7 cols
        self.cal_buttons = []
        for r in range(1, 7): # Rows 1-6
            self.calendar_frame.grid_rowconfigure(r, weight=1, uniform="cal_row")
            row_btns = []
            for c in range(7):
                btn = ctk.CTkButton(
                    self.calendar_frame,
                    text="",
                    font=("Inter", 12, "bold"),
                    width=40, 
                    height=40,
                    corner_radius=8,
                    fg_color="transparent", # Default invisible
                    hover=False,
                    state="disabled"
                )
                btn.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")
                row_btns.append(btn)
            self.cal_buttons.append(row_btns)

        # Day Detail Section (Below Calendar)
        div = ctk.CTkFrame(content, height=2, fg_color="#334155")
        div.grid(row=2, column=0, sticky="new", padx=20)

        self.day_detail_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.day_detail_frame.grid(row=2, column=0, padx=20, pady=(20, 20), sticky="nsew")
        self.day_detail_frame.grid_columnconfigure(0, weight=1)
        self.day_detail_frame.grid_rowconfigure(2, weight=1)

        self.selected_date = None
        self._refresh_calendar()

    def _connect(self):
        return sqlite3.connect(DB_NAME)

    def _edit_slot(self, slot_id: int, start_t: str, end_t: str, slot_len: int | None, max_appt: int | None):
        """Open a small window to edit an existing time slot."""
        if self.selected_date is None or self.doctor_id is None: return

        master = self.winfo_toplevel()
        win = ctk.CTkToplevel(master)
        win.title("Edit Time Slot")
        win.geometry("500x350")
        win.configure(fg_color="#0f172a")
        win.transient(master)
        win.grab_set()

        # Center
        win.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() - 500) // 2
        y = master.winfo_rooty() + (master.winfo_height() - 350) // 2
        win.geometry(f"+{x}+{y}")

        win.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(win, text="Edit Time Slot", font=("Inter", 18, "bold"), text_color="white").grid(row=0, column=0, columnspan=2, pady=(20, 20))

        hours = [f"{h:02d}" for h in range(1, 13)]
        minutes = ["00", "30"]
        periods = ["AM", "PM"]

        def _from_24h(t: str):
            try: h, m = map(int, t.split(":"))
            except: return "09", "00", "AM"
            period = "AM"
            if h >= 12:
                period = "PM"
                if h > 12: h -= 12
            elif h == 0: h = 12
            return f"{h:02d}", f"{m:02d}", period

        s_h, s_m, s_p = _from_24h(start_t)
        e_h, e_m, e_p = _from_24h(end_t)

        def _create_time_row(row_idx, label, h_val, m_val, p_val):
            ctk.CTkLabel(win, text=label, font=("Inter", 14), text_color="#cbd5e1").grid(row=row_idx, column=0, padx=30, pady=10, sticky="w")
            f = ctk.CTkFrame(win, fg_color="transparent")
            f.grid(row=row_idx, column=1, padx=30, pady=10, sticky="w")
            hc = ctk.CTkComboBox(f, values=hours, width=70, font=("Inter", 13)); hc.set(h_val); hc.pack(side="left", padx=(0, 5))
            mc = ctk.CTkComboBox(f, values=minutes, width=70, font=("Inter", 13)); mc.set(m_val); mc.pack(side="left", padx=5)
            pc = ctk.CTkComboBox(f, values=periods, width=70, font=("Inter", 13)); pc.set(p_val); pc.pack(side="left", padx=5)
            return hc, mc, pc

        sh_c, sm_c, sp_c = _create_time_row(1, "Start Time", s_h, s_m, s_p)
        eh_c, em_c, ep_c = _create_time_row(2, "End Time", e_h, e_m, e_p)

        def _to_24h(h, m, p):
            try: hh = int(h)
            except: return ""
            if p == "PM" and hh != 12: hh += 12
            if p == "AM" and hh == 12: hh = 0
            return f"{hh:02d}:{m}"

        def save():
            ns = _to_24h(sh_c.get(), sm_c.get(), sp_c.get())
            ne = _to_24h(eh_c.get(), em_c.get(), ep_c.get())
            if ns >= ne:
                messagebox.showerror("Error", "End time must be after start time.")
                return
            conn = self._connect()
            cur = conn.cursor()
            cur.execute("UPDATE doctor_availability SET start_time=?, end_time=? WHERE id=?", (ns, ne, slot_id))
            conn.commit()
            conn.close()
            win.destroy()
            self._load_day_data(self.selected_date)

        def delete():
            if messagebox.askyesno("Confirm", "Delete this time slot?"):
                self._delete_slot(slot_id)
                win.destroy()

        btn_box = ctk.CTkFrame(win, fg_color="transparent")
        btn_box.grid(row=3, column=0, columnspan=2, pady=30)
        ctk.CTkButton(btn_box, text="Save Changes", font=("Inter", 13, "bold"), fg_color="#3b82f6", width=120, command=save).pack(side="left", padx=10)
        ctk.CTkButton(btn_box, text="Delete Slot", font=("Inter", 13, "bold"), fg_color="#ef4444", hover_color="#b91c1c", width=120, command=delete).pack(side="left", padx=10)

    def _prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self._refresh_calendar()

    def _next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self._refresh_calendar()

    def _refresh_calendar(self):
        # Update title
        self.month_label.configure(text=f"{calendar.month_name[self.current_month]} {self.current_year}")

        # Fetch Data efficiently
        availability_map = {}
        if self.doctor_id is not None:
            conn = self._connect()
            cur = conn.cursor()
            start = f"{self.current_year:04d}-{self.current_month:02d}-01"
            end = f"{self.current_year:04d}-{self.current_month:02d}-31"
            # Get only dates that have explicitly marked status
            cur.execute("""
                SELECT date, is_available FROM doctor_availability 
                WHERE doctor_id=? AND date BETWEEN ? AND ? AND start_time IS NULL
            """, (self.doctor_id, start, end))
            for d, avail in cur.fetchall():
                availability_map[d] = avail
            conn.close()

        # Fill Grid (Reuse Buttons)
        cal = calendar.Calendar(firstweekday=0)
        month_weeks = cal.monthdayscalendar(self.current_year, self.current_month)
        
        today_str = date.today().strftime("%Y-%m-%d")

        for r in range(6):
            # If this week doesn't exist in the month, clear row
            if r >= len(month_weeks):
                for c in range(7):
                    self.cal_buttons[r][c].configure(text="", fg_color="transparent", state="disabled")
                continue
                
            week = month_weeks[r]
            for c in range(7):
                day_num = week[c]
                btn = self.cal_buttons[r][c]

                if day_num == 0:
                    btn.configure(text="", fg_color="transparent", state="disabled")
                    continue

                d_str = f"{self.current_year:04d}-{self.current_month:02d}-{day_num:02d}"
                status = availability_map.get(d_str)

                # Style Logic
                text_col = "white"
                fg_col = "#334155" # Default available (Slate 700)
                hover_col = "#475569"
                state = "normal"
                hover = True

                if d_str < today_str:
                    fg_col = "transparent" # Or extremely washed out
                    text_col = "#475569"
                    state = "disabled"
                    hover = False
                    cmd = None
                elif status == 0:
                    fg_col = "#ef4444" # Red (Unavail)
                    hover_col = "#dc2626"
                    cmd = lambda d=d_str: self._open_day_detail(d)
                elif d_str == self.selected_date:
                    fg_col = "#3b82f6" # Blue (Selected)
                    hover_col = "#2563eb"
                    cmd = lambda d=d_str: self._open_day_detail(d)
                else:
                    # Default Available
                    cmd = lambda d=d_str: self._open_day_detail(d)

                btn.configure(
                    text=str(day_num),
                    state=state,
                    fg_color=fg_col,
                    hover_color=hover_col,
                    text_color=text_col,
                    hover=hover,
                    command=cmd
                )

        # Trigger detail view logic if needed
        if self.selected_date and self.selected_date.startswith(f"{self.current_year:04d}-{self.current_month:02d}"):
            # If current selection is visible, we already updated its color above
            # But we might need to refresh details if logic demands (rare)
            pass
        elif self.selected_date and not self.selected_date.startswith(f"{self.current_year:04d}-{self.current_month:02d}"):
             # Selection is in another month, leave details open but calendar won't highlight it
             pass
        else:
             # No selection
             self._render_day_detail(None)

    def _open_day_detail(self, d_str: str):
        self.selected_date = d_str
        self._refresh_calendar() # To highlight selection
        self._render_day_detail(d_str)

    def _render_day_detail(self, d_str: str):
        for child in self.day_detail_frame.winfo_children(): child.destroy()

        if d_str is None:
            ctk.CTkLabel(self.day_detail_frame, text="Select a date to manage availability.", font=("Inter", 14), text_color="#64748b").pack(pady=40)
            return

        # Header
        h_row = ctk.CTkFrame(self.day_detail_frame, fg_color="transparent")
        h_row.pack(fill="x", pady=(0, 10))
        from datetime import datetime
        dt = datetime.strptime(d_str, "%Y-%m-%d")
        ctk.CTkLabel(h_row, text=dt.strftime("%B %d, %Y"), font=("Inter", 16, "bold"), text_color="white").pack(side="left")

        # Switch
        self.day_status_switch = ctk.CTkSwitch(
            h_row, text="Available", font=("Inter", 13),
            command=self._toggle_day_status, progress_color="#3b82f6"
        )
        self.day_status_switch.pack(side="right", padx=10)

        self.slots_frame = ctk.CTkScrollableFrame(self.day_detail_frame, fg_color="transparent")
        self.slots_frame.pack(fill="both", expand=True)

        self._load_day_data(d_str)

        ctk.CTkButton(
            self.day_detail_frame, text="+ Add Time Slot", font=("Inter", 13, "bold"),
            fg_color="#3b82f6", hover_color="#2563eb", height=36,
            command=self._open_add_slot
        ).pack(fill="x", pady=(10, 0))

    def _load_day_data(self, d_str: str, update_switch: bool = True):
        if self.doctor_id is None: return
        conn = self._connect()
        cur = conn.cursor()
        
        # Check Status
        cur.execute("SELECT is_available FROM doctor_availability WHERE doctor_id=? AND date=? AND start_time IS NULL ORDER BY id DESC LIMIT 1", (self.doctor_id, d_str))
        row = cur.fetchone()
        is_avail = 1 if row is None else row[0]
        if update_switch:
            if is_avail: self.day_status_switch.select()
            else: self.day_status_switch.deselect()

        # Fetch Slots
        cur.execute("SELECT id, start_time, end_time, max_appointments, slot_length_minutes FROM doctor_availability WHERE doctor_id=? AND date=? AND is_available=1 AND start_time IS NOT NULL ORDER BY start_time", (self.doctor_id, d_str))
        slots = cur.fetchall()
        conn.close()

        if not hasattr(self, "slots_frame"): return
        for c in self.slots_frame.winfo_children(): c.destroy()

        if is_avail == 0:
            ctk.CTkLabel(self.slots_frame, text="Marked as Unavailable", font=("Inter", 13), text_color="#ef4444").pack(pady=20)
            return

        if not slots:
            ctk.CTkLabel(self.slots_frame, text="No time slots arranged.", font=("Inter", 13), text_color="#64748b").pack(pady=20)
            return

        def _fmt(t):
            try: return datetime.strptime(t, "%H:%M").strftime("%I:%M %p").lstrip("0")
            except: return t

        for sid, st, et, ma, sl in slots:
            row = ctk.CTkFrame(self.slots_frame, fg_color="#334155", corner_radius=8)
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=f"{_fmt(st)} - {_fmt(et)}", font=("Inter", 13, "bold"), text_color="white").pack(side="left", padx=15, pady=10)
            ctk.CTkButton(row, text="Edit", width=60, height=24, font=("Inter", 11), fg_color="#475569", hover_color="#64748b", command=lambda s=sid, a=st, b=et, c=sl, d=ma: self._edit_slot(s, a, b, c, d)).pack(side="right", padx=10)

    def _toggle_day_status(self):
        if not self.selected_date: return
        val = 1 if self.day_status_switch.get() else 0
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM doctor_availability WHERE doctor_id=? AND date=? AND start_time IS NULL", (self.doctor_id, self.selected_date))
        cur.execute("INSERT INTO doctor_availability (doctor_id, date, is_available) VALUES (?, ?, ?)", (self.doctor_id, self.selected_date, val))
        conn.commit()
        conn.close()
        self._refresh_calendar()
        self._load_day_data(self.selected_date, update_switch=False)

    def _open_add_slot(self):
        if not self.selected_date or not self.day_status_switch.get(): return
        master = self.winfo_toplevel()
        win = ctk.CTkToplevel(master)
        win.title("Add Slot")
        win.geometry("500x350")
        win.configure(fg_color="#0f172a")
        win.transient(master)
        win.grab_set()
        
        # Center
        win.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() - 500) // 2
        y = master.winfo_rooty() + (master.winfo_height() - 350) // 2
        win.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(win, text="Add New Time Slot", font=("Inter", 18, "bold"), text_color="white").pack(pady=20)
        f = ctk.CTkFrame(win, fg_color="transparent")
        f.pack(pady=10)
        
        hours = [f"{h:02d}" for h in range(1, 13)]
        mins = ["00", "30"]
        ps = ["AM", "PM"]
        
        start_h = ctk.CTkComboBox(f, values=hours, width=60); start_h.set("09"); start_h.grid(row=0, column=0, padx=2)
        start_m = ctk.CTkComboBox(f, values=mins, width=60); start_m.set("00"); start_m.grid(row=0, column=1, padx=2)
        start_p = ctk.CTkComboBox(f, values=ps, width=60); start_p.set("AM"); start_p.grid(row=0, column=2, padx=2)
        ctk.CTkLabel(f, text="to", text_color="#cbd5e1").grid(row=0, column=3, padx=10)
        end_h = ctk.CTkComboBox(f, values=hours, width=60); end_h.set("05"); end_h.grid(row=0, column=4, padx=2)
        end_m = ctk.CTkComboBox(f, values=mins, width=60); end_m.set("00"); end_m.grid(row=0, column=5, padx=2)
        end_p = ctk.CTkComboBox(f, values=ps, width=60); end_p.set("PM"); end_p.grid(row=0, column=6, padx=2)
        
        def _to_24h(h, m, p):
             hh = int(h)
             if p == "PM" and hh != 12: hh += 12
             if p == "AM" and hh == 12: hh = 0
             return f"{hh:02d}:{m}"

        def save():
             s = _to_24h(start_h.get(), start_m.get(), start_p.get())
             e = _to_24h(end_h.get(), end_m.get(), end_p.get())
             # Basic check if s < e? Or can end next day? Assuming same day for now.
             conn = self._connect()
             cur = conn.cursor()
             cur.execute("INSERT INTO doctor_availability (doctor_id, date, start_time, end_time, is_available, max_appointments, slot_length_minutes) VALUES (?, ?, ?, ?, 1, 1, 30)", (self.doctor_id, self.selected_date, s, e))
             conn.commit()
             conn.close()
             win.destroy()
             self._load_day_data(self.selected_date)

        ctk.CTkButton(win, text="Add Slot", font=("Inter", 13, "bold"), fg_color="#3b82f6", width=200, command=save).pack(pady=30)

    def _delete_slot(self, slot_id: int):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM doctor_availability WHERE id=?", (slot_id,))
        conn.commit()
        conn.close()
