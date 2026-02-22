import tkinter as tk
from tkinter import ttk, messagebox
from models import User

class UserMixin:

    def build_users_tab(self):
        frame = ttk.Frame(self.users_tab, padding=30)
        frame.pack(fill="both", expand=True)

        form = ttk.LabelFrame(frame, text="Create / Edit Staff", padding=20)
        form.pack(fill="x", pady=10)

        ttk.Label(form, text="Username").grid(row=0, column=0, pady=5)
        self.user_username = ttk.Entry(form, width=30)
        self.user_username.grid(row=0, column=1)

        ttk.Label(form, text="Password").grid(row=1, column=0, pady=5)
        self.user_password = ttk.Entry(form, width=30)
        self.user_password.grid(row=1, column=1)

        ttk.Label(form, text="Role").grid(row=2, column=0, pady=5)
        self.user_role = ttk.Combobox(form, values=["manager", "staff"], width=27)
        self.user_role.grid(row=2, column=1)
        self.user_role.set("staff")

        tk.Button(
            form,
            text="Save User",
            bg="#0d6efd",
            fg="white",
            activebackground="#0b5ed7",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            command=self.save_user
        ).grid(row=3, column=0, columnspan=2, pady=10)

        self.selected_user_id = None

        columns = ("ID", "Username", "Role", "Edit", "Delete")
        self.users_tree = ttk.Treeview(frame, columns=columns, show="headings")
        self.users_tree.pack(fill="both", expand=True)
        for col in columns:
            self.users_tree.heading(col, text=col)
            if col in ("Edit", "Delete"):
                self.users_tree.column(col, width=120, anchor="center")
            else:
                self.users_tree.column(col, width=190, anchor="center")
        self.users_tree.bind("<Button-1>", self.handle_user_click)

        self.load_users()

    def load_users(self):
        for row in self.users_tree.get_children():
            self.users_tree.delete(row)
        users = self.session.query(User).all()
        for user in users:
            self.users_tree.insert("", "end", values=(user.id, user.username, user.role, "Edit", "Delete"))

    def save_user(self):
        username = self.user_username.get()
        password = self.user_password.get()
        role = self.user_role.get()
        if not username:
            messagebox.showerror("Error", "Username is required.")
            return

        if self.selected_user_id:
            user = self.session.query(User).get(self.selected_user_id)
            if not user:
                messagebox.showerror("Error", "User not found.")
                return
            user.username = username
            if password:
                user.password = password
            user.role = role
            self.selected_user_id = None
        else:
            if not password:
                messagebox.showerror("Error", "Password is required for new user.")
                return
            user = User(username=username, password=password, role=role)
            self.session.add(user)

        self.session.commit()
        messagebox.showinfo("Success", "User saved successfully.")
        self.clear_user_form()
        self.load_users()

    def handle_user_click(self, event):
        item = self.users_tree.identify_row(event.y)
        column = self.users_tree.identify_column(event.x)

        if not item:
            return

        col_index = int(column.replace("#", "")) - 1
        if col_index not in (3, 4):
            return

        values = self.users_tree.item(item, "values")
        user_id = values[0]

        if col_index == 3:
            self.edit_user(user_id)
        elif col_index == 4:
            self.delete_user(user_id)

    def edit_user(self, user_id):
        user = self.session.query(User).get(user_id)
        if not user:
            return

        self.selected_user_id = user_id
        self.user_username.delete(0, tk.END)
        self.user_username.insert(0, user.username)
        self.user_password.delete(0, tk.END)
        self.user_role.set(user.role)

    def delete_user(self, user_id):
        user = self.session.query(User).get(user_id)
        if not user:
            return

        if user.role == "manager":
            messagebox.showerror("Error", "Cannot delete manager accounts.")
            return

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this staff member?")
        if not confirm:
            return

        self.session.delete(user)
        self.session.commit()
        self.clear_user_form()
        self.load_users()

    def clear_user_form(self):
        self.user_username.delete(0, tk.END)
        self.user_password.delete(0, tk.END)
        self.user_role.set("staff")
        self.selected_user_id = None

   