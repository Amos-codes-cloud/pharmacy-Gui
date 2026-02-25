import tkinter as tk
from tkinter import ttk, messagebox


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
            text="Add User",
            bg="#51fd0d",
            fg="white",
            command=self.save_user
        ).grid(row=3, column=0, columnspan=2, pady=10)

        self.selected_user_id = None

        columns = ("ID", "Username", "Role", "Edit", "Delete")
        self.users_tree = ttk.Treeview(frame, columns=columns, show="headings")
        self.users_tree.pack(fill="both", expand=True)

        for col in columns:
            self.users_tree.heading(col, text=col)
            self.users_tree.column(col, width=150, anchor="center")

        self.users_tree.bind("<Button-1>", self.handle_user_click)

        self.load_users()

    def load_users(self):
        for row in self.users_tree.get_children():
            self.users_tree.delete(row)

        self.cursor.execute("SELECT id, username, role FROM users")
        users = self.cursor.fetchall()

        for user in users:
            self.users_tree.insert(
                "", "end",
                values=(user[0], user[1], user[2], "Edit", "Delete")
            )

    def save_user(self):
        username = self.user_username.get()
        password = self.user_password.get()
        role = self.user_role.get()

        if not username:
            messagebox.showerror("Error", "Username is required.")
            return

        if self.selected_user_id:
            if password:
                self.cursor.execute(
                    "UPDATE users SET username=%s, password=%s, role=%s WHERE id=%s",
                    (username, password, role, self.selected_user_id)
                )
            else:
                self.cursor.execute(
                    "UPDATE users SET username=%s, role=%s WHERE id=%s",
                    (username, role, self.selected_user_id)
                )
        else:
            if not password:
                messagebox.showerror("Error", "Password is required for new user.")
                return

            self.cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, password, role)
            )

        self.conn.commit()
        messagebox.showinfo("Success", "User saved successfully.")

        self.clear_user_form()
        self.load_users()

    def handle_user_click(self, event):
        item = self.users_tree.identify_row(event.y)
        column = self.users_tree.identify_column(event.x)

        if not item:
            return

        col_index = int(column.replace("#", "")) - 1
        values = self.users_tree.item(item, "values")
        user_id = values[0]

        if col_index == 3:
            self.edit_user(user_id)
        elif col_index == 4:
            self.delete_user(user_id)

    def edit_user(self, user_id):
        self.cursor.execute(
            "SELECT username, role FROM users WHERE id=%s",
            (user_id,)
        )
        user = self.cursor.fetchone()

        if not user:
            return

        self.selected_user_id = user_id
        self.user_username.delete(0, tk.END)
        self.user_username.insert(0, user[0])
        self.user_password.delete(0, tk.END)
        self.user_role.set(user[1])

    def delete_user(self, user_id):
        self.cursor.execute(
            "SELECT role FROM users WHERE id=%s",
            (user_id,)
        )
        user = self.cursor.fetchone()

        if not user:
            return

        if user[0] == "manager":
            messagebox.showerror("Error", "Cannot delete manager accounts.")
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            "Are you sure you want to delete this staff member?"
        )
        if not confirm:
            return

        self.cursor.execute(
            "DELETE FROM users WHERE id=%s",
            (user_id,)
        )
        self.conn.commit()

        self.clear_user_form()
        self.load_users()

    def clear_user_form(self):
        self.user_username.delete(0, tk.END)
        self.user_password.delete(0, tk.END)
        self.user_role.set("staff")
        self.selected_user_id = None