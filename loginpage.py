import tkinter as tk
from tkinter import ttk, messagebox

from connector import SessionLocal
from models import User


class LoginForm(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padding=20)

        ttk.Label(self, text="Username").pack(pady=(0, 6), anchor="w")
        self.username = ttk.Entry(self, width=35)
        self.username.pack(fill="x")

        ttk.Label(self, text="Password").pack(pady=(12, 6), anchor="w")
        self.password = ttk.Entry(self, show="*", width=35)
        self.password.pack(fill="x")

        ttk.Button(self, text="Login", command=self.login).pack(pady=(18, 0), fill="x")

    def login(self):
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(
                username=self.username.get().strip(),
                password=self.password.get().strip(),
            ).first()
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))
            return
        finally:
            session.close()

        if user:
            root = self.winfo_toplevel()
            root.destroy()
            from pharmacy import PharmacyApp

            main = tk.Tk()
            PharmacyApp(main, user.role, user.username)
            main.mainloop()
        else:
            messagebox.showerror("Error", "Invalid credentials")


class LoginPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        self.controller = controller

        ttk.Label(self, text="Sign in to continue", font=("Arial", 16, "bold")).pack(pady=(24, 8))
        LoginForm(self).pack(padx=24, pady=10, fill="x")

        tk.Button(
            self,
            text="Back to Home",
            font=("Arial", 12),
            bg="#6c757d",
            fg="white",
            padx=16,
            pady=8,
            command=lambda: controller.show_frame("Homepage"),
        ).pack(pady=(8, 18))
