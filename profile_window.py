import sqlite3
import customtkinter as ctk
from tkinter import messagebox
from database import DB_NAME

class ProfileWindow(ctk.CTkToplevel):
    def __init__(self, master, username: str, anchor_widget=None, mode="settings"):
        super().__init__(master)
        
        self.mode = mode
        self.username = username
        self.master_ref = master
        self.selected_image_path = None
        
        # Determine Title and Size based on mode
        if self.mode == "security":
            title_text = "Security Settings"
            width, height = 400, 360 # Smaller for password only
        else:
            title_text = "Profile Settings"
            width, height = 400, 500

        self.title(title_text)
        self.geometry(f"{width}x{height}")
        self.resizable(False, False)
        self.configure(fg_color="#0f172a") # Theme BG
        self.transient(master)
        self.update_idletasks()

        if anchor_widget is not None:
            # Position just below/right of anchor
            ax = anchor_widget.winfo_rootx()
            ay = anchor_widget.winfo_rooty()
            aw = anchor_widget.winfo_width()
            ah = anchor_widget.winfo_height()
            x = int(ax + aw - width)
            y = int(ay + ah + 4)
        else:
            # Center on master
            master_x = master.winfo_rootx()
            master_y = master.winfo_rooty()
            master_w = master.winfo_width()
            master_h = master.winfo_height()
            x = master_x + (master_w - width) // 2
            y = master_y + (master_h - height) // 2
        
        # Ensure within screen bounds
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(0, min(x, screen_w - width))
        y = max(0, min(y, screen_h - height))

        self.geometry(f"{width}x{height}+{x}+{y}")
        
        # DB Load
        self.current_image_path = None
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT password, profile_image_path, full_name FROM users WHERE username = ?", (self.username,))
        row = cur.fetchone()
        conn.close()
        
        if row:
            self.current_password = row[0]
            self.current_image_path = row[1]
            self.current_full_name = row[2] if row[2] else ""
        else:
            self.current_password = ""
            self.current_image_path = None
            self.current_full_name = ""

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Main content area

        # Title Label
        title = ctk.CTkLabel(self, text=title_text, font=("Inter", 20, "bold"), text_color="white")
        title.grid(row=0, column=0, padx=24, pady=(24, 15), sticky="w")

        # Main Content Container
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)

        if self.mode == "security":
             self._build_security_ui()
        else:
             self._build_settings_ui()
        
        # Bottom Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=24, pady=24, sticky="ew")
        
        ctk.CTkButton(
            btn_frame, 
            text="Cancel", 
            fg_color="transparent", 
            border_width=1, 
            border_color="#64748b",
            text_color="#cbd5e1",
            hover_color="#334155",
            width=80, 
            command=self.destroy
        ).pack(side="left")
        
        save_btn_txt = "Change Password" if self.mode == "security" else "Save Changes"
        ctk.CTkButton(
            btn_frame, 
            text=save_btn_txt, 
            width=120, 
            fg_color="#3b82f6",
            hover_color="#2563eb",
            font=("Inter", 13, "bold"),
            command=self._on_save
        ).pack(side="right")

    def _build_settings_ui(self):
        # Avatar
        self.avatar_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.avatar_frame.pack(fill="x", pady=(0, 15))
        
        self.avatar_size = 90
        # Wrap avatar in a small frame to center it
        av_wrap = ctk.CTkFrame(self.avatar_frame, fg_color="transparent")
        av_wrap.pack()
        
        self.avatar_preview = ctk.CTkLabel(av_wrap, text="", width=self.avatar_size, height=self.avatar_size)
        self.avatar_preview.pack(pady=(0, 8))
        self._load_avatar_preview(self.current_image_path)
        
        ctk.CTkButton(
            av_wrap, 
            text="Upload New Photo", 
            font=("Inter", 11),
            height=26,
            width=110,
            fg_color="#334155", 
            hover_color="#475569",
            command=self._select_photo
        ).pack()

        # Fields frame
        f = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        f.pack(fill="x", padx=24)
        f.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(f, text="Display Name", font=("Inter", 13), text_color="#94a3b8").pack(anchor="w", pady=(5, 2))
        self.fullname_entry = ctk.CTkEntry(f, fg_color="#1e293b", border_color="#334155", text_color="white", height=38)
        self.fullname_entry.insert(0, self.current_full_name)
        self.fullname_entry.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(f, text="Username", font=("Inter", 13), text_color="#94a3b8").pack(anchor="w", pady=(5, 2))
        self.username_entry = ctk.CTkEntry(f, fg_color="#1e293b", border_color="#334155", text_color="white", height=38)
        self.username_entry.insert(0, self.username)
        self.username_entry.pack(fill="x")

    def _build_security_ui(self):
        f = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        f.pack(fill="x", padx=24, pady=10)
        
        def _field(label, var_name):
            ctk.CTkLabel(f, text=label, font=("Inter", 13), text_color="#94a3b8").pack(anchor="w", pady=(5, 2))
            ent = ctk.CTkEntry(f, show="*", fg_color="#1e293b", border_color="#334155", text_color="white", height=38)
            ent.pack(fill="x", pady=(0, 12))
            setattr(self, var_name, ent)

        _field("Current Password", "curr_pass_entry")
        _field("New Password", "new_pass_entry")
        _field("Confirm New Password", "confirm_pass_entry")

    def _on_save(self):
        if self.mode == "security":
            self._save_password()
        else:
            self._save_profile()

    def _save_password(self):
        curr = self.curr_pass_entry.get().strip()
        new_p = self.new_pass_entry.get().strip()
        conf_p = self.confirm_pass_entry.get().strip()

        if not curr or not new_p or not conf_p:
            messagebox.showwarning("Incomplete", "All fields are required.")
            return

        if curr != self.current_password:
            messagebox.showerror("Error", "Incorrect current password.")
            return

        if new_p != conf_p:
            messagebox.showerror("Error", "New passwords do not match.")
            return
        
        if len(new_p) < 4:
            messagebox.showerror("Security", "Password must be at least 4 characters.")
            return

        # Upate DB
        try:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("UPDATE users SET password = ? WHERE username = ?", (new_p, self.username))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Password changed successfully.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update password: {e}")

    def _save_profile(self):
        new_username = self.username_entry.get().strip()
        new_fullname = self.fullname_entry.get().strip()

        if not new_username:
            messagebox.showwarning("Validation", "Username cannot be empty.")
            return

        import os
        import shutil

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
                messagebox.showerror("Error", f"Failed to save image: {e}")
                return

        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()

        # If username changed, ensure it's unique
        if new_username != self.username:
            cur.execute("SELECT COUNT(*) FROM users WHERE username = ?", (new_username,))
            if cur.fetchone()[0] > 0:
                conn.close()
                messagebox.showerror("Error", "Username already exists.")
                return

        cur.execute(
            "UPDATE users SET username = ?, profile_image_path = ?, full_name = ? WHERE username = ?",
            (new_username, final_image_path, new_fullname, self.username),
        )

        if new_username != self.username:
            cur.execute(
                "UPDATE recent_logins SET username = ? WHERE username = ?",
                (new_username, self.username)
            )

        conn.commit()
        conn.close()

        self.username = new_username
        self.current_image_path = final_image_path
        self.current_full_name = new_fullname

        messagebox.showinfo("Profile", "Profile updated successfully.")
        
        # Callback to update avatar
        if hasattr(self.master_ref, "_update_avatar_ui"):
             self.master_ref._update_avatar_ui(final_image_path)
        
        self.destroy()

    def _load_avatar_preview(self, path):
        from PIL import Image
        import os
        
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
            self.avatar_preview.configure(image=None, text="NO PHOTO", fg_color="#1e293b", corner_radius=40)

    def _select_photo(self):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(
            title="Select Profile Photo",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if file_path:
            self.selected_image_path = file_path
            self._load_avatar_preview(file_path)
