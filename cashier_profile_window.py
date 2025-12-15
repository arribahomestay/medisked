import sqlite3
import os
import shutil
import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image

from database import DB_NAME, log_activity

class CashierProfileWindow(ctk.CTkToplevel):
    def __init__(self, master, username: str, anchor_widget=None):
        super().__init__(master)

        self.title("Cashier Profile Settings")
        width, height = 400, 600
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.configure(fg_color="#0f172a") # Theme BG

        self.transient(master)
        self.update_idletasks()

        if anchor_widget is not None:
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

        self.username = username
        self.master_ref = master
        self.selected_image_path = None
        self.current_image_path = None
        self.current_full_name = ""
        self.password_value = ""
        
        # Load Existing Data
        self._load_data()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(9, weight=1)

        title = ctk.CTkLabel(self, text="Cashier Profile Settings", font=("Segoe UI", 20, "bold"), text_color="white")
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
        self.username_entry.insert(0, self.username)
        self.username_entry.grid(row=5, column=0, padx=24, pady=(0, 10), sticky="ew")

        # Password
        pwd_label = ctk.CTkLabel(self, text="Password (leave blank to keep current)", font=("Segoe UI", 12), text_color="#94a3b8")
        pwd_label.grid(row=6, column=0, padx=24, pady=(5, 0), sticky="w")

        self.password_entry = ctk.CTkEntry(self, show="*", fg_color="#1e293b", border_color="#334155", text_color="white")
        self.password_entry.grid(row=7, column=0, padx=24, pady=(0, 10), sticky="ew")

        # Buttons
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        buttons_frame.grid(row=10, column=0, padx=24, pady=(10, 24), sticky="ew")
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
        cur.execute("SELECT password, profile_image_path, full_name FROM users WHERE username = ?", (self.username,))
        row = cur.fetchone()
        if row:
            self.password_value = row[0]
            self.current_image_path = row[1]
            self.current_full_name = row[2]
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
        new_password = self.password_entry.get().strip()
        new_fullname = self.fullname_entry.get().strip()

        if not new_username:
            messagebox.showwarning("Validation", "Username cannot be empty.")
            return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # Check unique username
        if new_username != self.username:
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

        password_to_save = new_password if new_password else self.password_value

        cur.execute(
            "UPDATE users SET username = ?, password = ?, profile_image_path = ?, full_name = ? WHERE username = ?",
            (new_username, password_to_save, final_image_path, new_fullname, self.username),
        )
        conn.commit()
        conn.close()

        # Update main app avatar immediately
        if hasattr(self.master_ref, "_update_avatar_ui"):
             self.master_ref._update_avatar_ui(final_image_path)
        
        if new_username != self.username:
             self.master_ref.username = new_username

        self.username = new_username
        self.current_image_path = final_image_path

        try:
            log_activity(self.username, "cashier", "update_profile", f"Updated cashier profile for '{self.username}'")
        except Exception:
            pass

        messagebox.showinfo(
            "Profile",
            "Profile updated successfully.",
        )
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
