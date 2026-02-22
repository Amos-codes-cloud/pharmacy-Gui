import tkinter as tk
from tkinter import messagebox
from database import SessionLocal
from models import User

class LoginWindow:

    def __init__(self, root):
        self.root = root
        self.root.title("Loginpage")
        self.root.geometry("400x300")

        tk.Label(root, text="Username").pack(pady=10)
        self.username = tk.Entry(root)
        self.username.pack()

        tk.Label(root, text="Password").pack(pady=10)
        self.password = tk.Entry(root, show="*")
        self.password.pack()

        tk.Button(root, text="Login",
                  command=self.login).pack(pady=20)

    def login(self):
        session = SessionLocal()

        user = session.query(User).filter_by(
            username=self.username.get(),
            password=self.password.get()
        ).first()

        if user:
            self.root.destroy()
            from pharmacy import PharmacyApp
            main = tk.Tk()
            app = PharmacyApp(main, user.role, user.username)
            main.mainloop()
        else:
            messagebox.showerror("Error", "Invalid credentials")

   
