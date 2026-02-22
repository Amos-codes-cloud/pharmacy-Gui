import tkinter as tk
from tkinter import ttk, messagebox
from database import SessionLocal
from models import Medicine, Sale, SaleItem, StockEntry, Patient, User
from inventory import InventoryMixin
from users import UserMixin
from sales import SalesMixin
from patients import PatientMixin
from reports import ReportsMixin
from alert import AlertMixin

class PharmacyApp(tk.Tk, InventoryMixin, UserMixin, SalesMixin, PatientMixin, ReportsMixin, AlertMixin):

    def __init__(self, root, role, username):
        self.root = root
        self.root.title("Pharmacy Management System")
        self.root.geometry("1920x1080")
        self.root.state("zoomed")

        self.session = SessionLocal()
        self.role = role
        self.username = username

        main_frame = ttk.Frame(root)
        main_frame.pack(fill="both", expand=True)

        # ---------------- Sidebar ----------------
        sidebar = tk.Frame(main_frame, width=280, bg="#0d6efd")
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # User Info
        user_frame = tk.Frame(sidebar, bg="#0d6efd", padx=10, pady=10)
        user_frame.pack(pady=20)
        self.user_icon = tk.Label(user_frame, text="👤", font=("Arial", 30), bg="#0d6efd", fg="white")
        self.user_icon.pack()
        self.user_label = tk.Label(user_frame, text=f"{username} ({role.title()})", font=("Arial", 14, "bold"), bg="#0d6efd", fg="white")
        self.user_label.pack()

        # Menu Buttons
        menu_buttons = [
            ("Sales", self.show_sales_tab),
            ("Patients", self.show_patients_tab)
        ]
        if self.role == "manager":
            menu_buttons += [
                ("Inventory", self.show_inventory_tab),
                ("Reports", self.show_reports_tab),
                ("Alerts", self.show_alerts_tab),
                ("Staff Management", self.show_users_tab)
            ]
        for text, cmd in menu_buttons:
            tk.Button(
                sidebar,
                text=text,
                width=22,
                command=cmd,
                bg="#0b5ed7",
                fg="white",
                activebackground="#0a58ca",
                activeforeground="white",
                relief="flat",
                bd=0,
                padx=8,
                pady=8,
                cursor="hand2"
            ).pack(pady=6, padx=12, fill="x")

        tk.Button(
            sidebar,
            text="Account",
            width=22,
            command=self.open_account_window,
            bg="#ffffff",
            fg="#0d6efd",
            activebackground="#e9ecef",
            activeforeground="#0b5ed7",
            relief="flat",
            bd=0,
            padx=8,
            pady=8,
            cursor="hand2"
        ).pack(side="bottom", pady=14, padx=12, fill="x")

        # ---------------- Main Content ----------------
        content = ttk.Frame(main_frame)
        content.pack(side="right", fill="both", expand=True)

        header_bar = tk.Frame(content, bg="#f8f9fa", height=60)
        header_bar.pack(side="top", fill="x")
        header_bar.pack_propagate(False)

        tk.Label(
            header_bar,
            text="Pharmacy Management System",
            font=("Arial", 18, "bold"),
            bg="#f8f9fa",
            fg="#0d6efd"
        ).pack(expand=True)

        footer_bar = tk.Frame(content, bg="#198754", height=36)
        footer_bar.pack(side="bottom", fill="x")
        footer_bar.pack_propagate(False)

        tk.Label(
            footer_bar,
            text="© 2026 Pharmacy Management System",
            font=("Arial", 10, "bold"),
            bg="#198754",
            fg="white"
        ).pack(expand=True)

        body = ttk.Frame(content)
        body.pack(side="top", fill="both", expand=True)

        notebook_style = ttk.Style(self.root)
        notebook_style.layout("Tabless.TNotebook.Tab", [])

        self.notebook = ttk.Notebook(body, style="Tabless.TNotebook")
        self.notebook.pack(fill="both", expand=True)

        # Tabs
        self.inventory_tab = ttk.Frame(self.notebook)
        self.sales_tab = ttk.Frame(self.notebook)
        self.reports_tab = ttk.Frame(self.notebook)
        self.alerts_tab = ttk.Frame(self.notebook)
        self.patients_tab = ttk.Frame(self.notebook)
        self.users_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.sales_tab, text="Sales")
        self.notebook.add(self.patients_tab, text="Patients")

        if self.role == "manager":
            self.notebook.add(self.inventory_tab, text="Inventory")
            self.notebook.add(self.reports_tab, text="Reports")
            self.notebook.add(self.alerts_tab, text="Alerts")
            self.notebook.add(self.users_tab, text="Staff Management")

        # Build Tabs
        self._safe_build_tab(self.build_sales_tab, "Sales")
        self._safe_build_tab(self.build_patients_tab, "Patients")

        if self.role == "manager":
            self._safe_build_tab(self.build_inventory_tab, "Inventory")
            self._safe_build_tab(self.build_reports_tab, "Reports")
            self._safe_build_tab(self.build_alerts_tab, "Alerts")
            self._safe_build_tab(self.build_users_tab, "Staff Management")

        self.notebook.select(self.sales_tab)

    def _safe_build_tab(self, builder, tab_name):
        try:
            builder()
        except Exception as e:
            messagebox.showerror("Tab Error", f"Failed to load {tab_name} tab:\n{e}")

    # ---------------- Sidebar Tab Switching ----------------
    def show_sales_tab(self):
        self.notebook.select(self.sales_tab)

    def show_patients_tab(self):
        self.notebook.select(self.patients_tab)

    def show_inventory_tab(self):
        self.notebook.select(self.inventory_tab)

    def show_reports_tab(self):
        self.notebook.select(self.reports_tab)

    def show_alerts_tab(self):
        self.notebook.select(self.alerts_tab)

    def show_users_tab(self):
        self.notebook.select(self.users_tab)

    def open_account_window(self):
        account_win = tk.Toplevel(self.root)
        account_win.title("Account")
        account_win.geometry("340x220")
        account_win.resizable(False, False)
        account_win.transient(self.root)
        account_win.grab_set()

        tk.Label(
            account_win,
            text=f"Signed in as: {self.username}",
            font=("Arial", 11, "bold")
        ).pack(pady=(18, 12))

        tk.Button(
            account_win,
            text="Change Password",
            bg="#0d6efd",
            fg="white",
            activebackground="#0b5ed7",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            command=lambda: self.open_change_password_window(account_win)
        ).pack(pady=8, ipadx=8)

        tk.Button(
            account_win,
            text="Logout",
            bg="#dc3545",
            fg="white",
            activebackground="#bb2d3b",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            command=self.logout
        ).pack(pady=8, ipadx=45)

    def open_change_password_window(self, parent_window=None):
        if parent_window is not None and parent_window.winfo_exists():
            parent_window.destroy()

        pwd_win = tk.Toplevel(self.root)
        pwd_win.title("Change Password")
        pwd_win.geometry("380x270")
        pwd_win.resizable(False, False)
        pwd_win.transient(self.root)
        pwd_win.grab_set()

        tk.Label(pwd_win, text="Current Password").pack(pady=(16, 4))
        current_entry = tk.Entry(pwd_win, show="*", width=32)
        current_entry.pack()

        tk.Label(pwd_win, text="New Password").pack(pady=(10, 4))
        new_entry = tk.Entry(pwd_win, show="*", width=32)
        new_entry.pack()

        tk.Label(pwd_win, text="Confirm New Password").pack(pady=(10, 4))
        confirm_entry = tk.Entry(pwd_win, show="*", width=32)
        confirm_entry.pack()

        show_pwd_var = tk.BooleanVar(value=False)

        def toggle_password_visibility():
            show_char = "" if show_pwd_var.get() else "*"
            current_entry.config(show=show_char)
            new_entry.config(show=show_char)
            confirm_entry.config(show=show_char)

        tk.Checkbutton(
            pwd_win,
            text="Show Password",
            variable=show_pwd_var,
            command=toggle_password_visibility
        ).pack(pady=(8, 0))

        def submit_password_change():
            current_pwd = current_entry.get().strip()
            new_pwd = new_entry.get().strip()
            confirm_pwd = confirm_entry.get().strip()

            if not current_pwd or not new_pwd or not confirm_pwd:
                messagebox.showerror("Error", "All fields are required.")
                return

            if new_pwd != confirm_pwd:
                messagebox.showerror("Error", "New password and confirmation do not match.")
                return

            user = self.session.query(User).filter_by(username=self.username).first()
            if not user:
                messagebox.showerror("Error", "User account not found.")
                return

            if user.password != current_pwd:
                messagebox.showerror("Error", "Current password is incorrect.")
                return

            user.password = new_pwd
            self.session.commit()
            messagebox.showinfo("Success", "Password changed successfully.")
            pwd_win.destroy()

        tk.Button(
            pwd_win,
            text="Update Password",
            bg="#198754",
            fg="white",
            activebackground="#157347",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            command=submit_password_change
        ).pack(pady=18)

    def logout(self):
        confirm = messagebox.askyesno("Logout", "Are you sure you want to logout?")
        if not confirm:
            return

        self.root.destroy()
        from login import LoginWindow
        login_root = tk.Tk()
        LoginWindow(login_root)
        login_root.mainloop()