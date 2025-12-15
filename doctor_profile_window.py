import sqlite3
import os
import shutil
import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image

from database import DB_NAME

class DoctorProfileWindow(ctk.CTkToplevel):
    def __init__(self, master, username: str, doctor_id: int, anchor_widget=None):
        super().__init__(master)

        self.title("Doctor Profile")
        width, height = 400, 650
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.configure(fg_color="#0f172a") # Theme BG

        self.transient(master)
        self.update_idletasks()

        if anchor_widget is not None:
            # Position the window just below and aligned to the right of the anchor widget
            ax = anchor_widget.winfo_rootx()
            ay = anchor_widget.winfo_rooty()
            aw = anchor_widget.winfo_width()
            ah = anchor_widget.winfo_height()

            x = int(ax + aw - width)
            y = int(ay + ah + 4)
        else:
            master_x = master.winfo_rootx()
            master_y = master.winfo_rooty()
            master_w = master.winfo_width()
            master_h = master.winfo_height()
            x = master_x + (master_w - width) // 2
            y = master_y + (master_h - height) // 2

        self.geometry(f"{width}x{height}+{x}+{y}")

        # Lock window position so it cannot be moved by dragging
        self._fixed_pos = (x, y)
        self._lock_position = False

        def _enforce_position(_event):
            if self._lock_position:
                return
            cur_x, cur_y = self.winfo_x(), self.winfo_y()
            if (cur_x, cur_y) != self._fixed_pos:
                self._lock_position = True
                self.geometry(f"{width}x{height}+{self._fixed_pos[0]}+{self._fixed_pos[1]}")
                self._lock_position = False

        self.bind("<Configure>", _enforce_position)

        self.old_username = username
        self.doctor_id = doctor_id
        self.master_ref = master
        self.selected_image_path = None
        
        self.current_image_path = None
        self.current_full_name = ""
        self.username_value = ""
        self.prof_value = ""
        self.password_value = ""

        # Load data first
        self._load_data()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(10, weight=1)

        title = ctk.CTkLabel(self, text="Doctor Profile", font=("Segoe UI", 20, "bold"), text_color="white")
        title.grid(row=0, column=0, padx=20, pady=(20, 15), sticky="w")

        # Avatar Preview
        self.avatar_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.avatar_frame.grid(row=1, column=0, pady=(0, 15))
        
        self.avatar_size = 100
        self.avatar_preview = ctk.CTkLabel(self.avatar_frame, text="", width=self.avatar_size, height=self.avatar_size)
        self.avatar_preview.pack()
        self._load_avatar_preview(self.current_image_path)

        change_photo_btn = ctk.CTkButton(
            self.avatar_frame, 
            text="Change Photo", 
            font=("Segoe UI", 11),
            height=24,
            width=100,
            fg_color="#334155", 
            hover_color="#475569",
            command=self._select_photo
        )
        change_photo_btn.pack(pady=8)

        # Display Name (Full Name)
        name_label = ctk.CTkLabel(self, text="Display Name", font=("Segoe UI", 12), text_color="#94a3b8")
        name_label.grid(row=2, column=0, padx=24, pady=(5, 0), sticky="w")

        self.fullname_entry = ctk.CTkEntry(self, fg_color="#1e293b", border_color="#334155", text_color="white")
        self.fullname_entry.insert(0, self.current_full_name or "")
        self.fullname_entry.grid(row=3, column=0, padx=24, pady=(0, 10), sticky="ew")

        # Username
        user_label = ctk.CTkLabel(self, text="Username", font=("Segoe UI", 12), text_color="#94a3b8")
        user_label.grid(row=4, column=0, padx=24, pady=(5, 0), sticky="w")

        self.username_entry = ctk.CTkEntry(self, fg_color="#1e293b", border_color="#334155", text_color="white")
        self.username_entry.insert(0, self.username_value or "")
        self.username_entry.grid(row=5, column=0, padx=24, pady=(0, 10), sticky="ew")

        # Profession
        prof_label = ctk.CTkLabel(self, text="Profession", font=("Segoe UI", 12), text_color="#94a3b8")
        prof_label.grid(row=6, column=0, padx=24, pady=(5, 0), sticky="w")

        self.prof_entry = ctk.CTkEntry(self, fg_color="#1e293b", border_color="#334155", text_color="white")
        self.prof_entry.insert(0, self.prof_value or "")
        self.prof_entry.grid(row=7, column=0, padx=24, pady=(0, 10), sticky="ew")

        # Password
        pwd_label = ctk.CTkLabel(self, text="Password (leave blank to keep current)", font=("Segoe UI", 12), text_color="#94a3b8")
        pwd_label.grid(row=8, column=0, padx=24, pady=(5, 0), sticky="w")

        self.password_entry = ctk.CTkEntry(self, show="*", fg_color="#1e293b", border_color="#334155", text_color="white")
        # Don't pre-fill password for security/ux, let them type if they want to change it
        self.password_entry.grid(row=9, column=0, padx=24, pady=(0, 10), sticky="ew")

        # Buttons
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.grid(row=11, column=0, padx=24, pady=(10, 24), sticky="ew")
        buttons_frame.grid_columnconfigure(0, weight=1)

        logout_button = ctk.CTkButton(
            buttons_frame,
            text="Logout",
            width=90,
            fg_color="#b91c1c",
            hover_color="#991b1b",
            command=self._logout,
        )
        logout_button.grid(row=0, column=0, sticky="w")

        save_button = ctk.CTkButton(buttons_frame, text="Save Changes", width=120, command=self.save_profile)
        save_button.grid(row=0, column=1, padx=(10, 0), sticky="e")

    def _load_data(self):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        cur.execute("SELECT username, password, profile_image_path, full_name FROM users WHERE username = ?", (self.old_username,))
        row = cur.fetchone()
        if row:
            self.username_value = row[0]
            self.password_value = row[1]
            self.current_image_path = row[2]
            self.current_full_name = row[3]

        if self.doctor_id is not None:
            cur.execute("SELECT specialty FROM doctors WHERE id = ?", (self.doctor_id,))
            doc_row = cur.fetchone()
            if doc_row:
                self.prof_value = doc_row[0]

        conn.close()

    def _load_avatar_preview(self, path):
        image = None
        if path and os.path.exists(path):
             try:
                pil_img = Image.open(path)
                image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(self.avatar_size, self.avatar_size))
             except Exception:
                pass
        
        if image:
            self.avatar_preview.configure(image=image, text="")
        else:
            self.avatar_preview.configure(image=None, text="No Image", fg_color="#1e293b", corner_radius=10)

    def _select_photo(self):
        file_path = filedialog.askopenfilename(
            title="Select Profile Photo",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if file_path:
            self.selected_image_path = file_path
            self._load_avatar_preview(file_path)

    def save_profile(self):
        new_username = self.username_entry.get().strip()
        new_prof = self.prof_entry.get().strip()
        new_password = self.password_entry.get().strip()
        new_fullname = self.fullname_entry.get().strip()

        if not new_username:
            messagebox.showwarning("Validation", "Username cannot be empty.")
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Check unique username
        if new_username != self.old_username:
            cur.execute("SELECT COUNT(*) FROM users WHERE username = ?", (new_username,))
            if cur.fetchone()[0] > 0:
                conn.close()
                messagebox.showerror("Error", "Username already exists.")
                return

        # Prepare image path
        final_image_path = self.current_image_path
        if self.selected_image_path:
            ext = os.path.splitext(self.selected_image_path)[1]
            new_filename = f"{new_username}_profile{ext}"
            target_dir = os.path.join(os.getcwd(), "profile_images")
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
            target_path = os.path.join(target_dir, new_filename)
            try:
                shutil.copy2(self.selected_image_path, target_path)
                final_image_path = target_path
            except Exception as e:
                conn.close()
                messagebox.showerror("Error", f"Failed to save image: {e}")
                return
        
        # Use existing password if new one is empty
        password_to_save = new_password if new_password else self.password_value

        # Update Users table
        cur.execute(
            "UPDATE users SET username = ?, password = ?, profile_image_path = ?, full_name = ? WHERE username = ?",
            (new_username, password_to_save, final_image_path, new_fullname, self.old_username),
        )

        # Update Doctors table and Appointments if username changed
        # We need to find the old doctor name to update appointments correctly
        old_doctor_name = None
        if self.doctor_id is not None:
            cur.execute("SELECT name FROM doctors WHERE id = ?", (self.doctor_id,))
            row = cur.fetchone()
            if row:
                old_doctor_name = row[0]
            
            # Update Doctor info
            # Sync doctor Name with Username (as per established pattern) or Full Name?
            # Creating uniformity: The system seems to rely on doctor_name in appointments matching the doctor_name in doctors table.
            # And previously it synced with 'new_username'.
            # Let's keep syncing with 'new_username' as the primary ID-like Name, 
            # OR we can switch to using 'new_fullname' if that's preferred.
            # But changing that logic might break other parts relying on username.
            # Safest bet: Keep syncing 'name' column in doctors table with 'username' from users table,
            # unless instructed otherwise.
            # User asked "change a display name", which we added as 'full_name'.
            
            cur.execute(
                "UPDATE doctors SET name = ?, specialty = ? WHERE id = ?",
                (new_username, new_prof, self.doctor_id),
            )
            
            # If username changed, update all appointments
            if old_doctor_name and new_username != old_doctor_name:
                cur.execute(
                    "UPDATE appointments SET doctor_name = ? WHERE doctor_name = ?",
                    (new_username, old_doctor_name),
                )

        conn.commit()
        conn.close()

        # Update main app avatar immediately
        if hasattr(self.master_ref, "_update_avatar_ui"):
             self.master_ref._update_avatar_ui(final_image_path)

        # Also update username on the dashboard if it changed
        if new_username != self.old_username:
             self.master_ref.username = new_username
             # You might need to refresh dashboard labels, but usually a restart is safer for deep changes.
             # However, we can try to refresh the avatar button text if it were visible (we hid it).
             pass

        messagebox.showinfo("Profile", "Profile updated successfully.")
        self.destroy()

    def _logout(self):
        if not hasattr(self.master_ref, "logout"):
            self.destroy()
            return
        if not messagebox.askyesno("Confirm Logout", "Are you sure you want to logout?"):
            return
        self.master_ref.should_relogin = True
        self.master_ref.destroy()
        self.destroy()
