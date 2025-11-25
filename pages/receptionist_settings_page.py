import customtkinter as ctk


class ReceptionistSettingsPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, corner_radius=0)

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Settings",
            font=("Segoe UI", 24, "bold"),
        )
        title.grid(row=0, column=0, padx=30, pady=(30, 10), sticky="w")

        subtitle = ctk.CTkLabel(
            self,
            text="",
            font=("Segoe UI", 14),
        )
        subtitle.grid(row=1, column=0, padx=30, pady=(0, 10), sticky="w")
