import tkinter as tk
from tkinter import ttk
from loginpage import LoginForm  # Your login form widget

class Homepage(tk.Frame):
    def __init__(self, parent, controller=None):
        super().__init__(parent, bg="white")
        self.controller = controller

        # Notebook for tabs
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=20, pady=20)

        # Tabs
        intro_tab = tk.Frame(notebook, bg="white")
        login_tab = tk.Frame(notebook, bg="white")
        notebook.add(intro_tab, text="Intro")
        notebook.add(login_tab, text="Login")

        # Intro content
        tk.Label(
            intro_tab,
            text="Welcome to Groly Pharma Ltd. Your health, our priority.",
            font=("Arial", 14),
            wraplength=550,
            justify="center",
            bg="white",
        ).pack(pady=(80, 20))

        tk.Button(
            intro_tab,
            text="Go to Login",
            font=("Arial", 14),
            bg="#28a745",
            fg="white",
            padx=20,
            pady=10,
            command=lambda: notebook.select(login_tab)
        ).pack(pady=10)

        # Embed login form
        LoginForm(login_tab).pack(padx=30, pady=30, fill="x")