import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date

class InventoryMixin:

    def build_inventory_tab(self):
        frame = ttk.Frame(self.inventory_tab, padding=30)
        frame.pack(fill="both", expand=True)

        # -------- FORM --------
        form = ttk.LabelFrame(frame, text="Add / Edit Medicine", padding=20)
        form.pack(fill="x", pady=20)

        ttk.Label(form, text="Name").grid(row=0, column=0, padx=5, pady=5)
        self.name_entry = ttk.Entry(form, width=30)
        self.name_entry.grid(row=0, column=1)

        ttk.Label(form, text="Type").grid(row=1, column=0, padx=5, pady=5)
        self.type_combo = ttk.Combobox(
            form,
            values=["Tablet", "Capsule", "Syrup", "Injection", "Cream", "Other"],
            width=27
        )
        self.type_combo.grid(row=1, column=1)
        self.type_combo.set("Tablet")

        ttk.Label(form, text="Expiry (YYYY-MM-DD)").grid(row=2, column=0, padx=5, pady=5)
        self.expiry_entry = ttk.Entry(form, width=30)
        self.expiry_entry.grid(row=2, column=1)

        ttk.Label(form, text="Price").grid(row=3, column=0, padx=5, pady=5)
        self.price_entry = ttk.Entry(form, width=30)
        self.price_entry.grid(row=3, column=1)

        ttk.Label(form, text="Quantity").grid(row=4, column=0, padx=5, pady=5)
        self.qty_entry = ttk.Entry(form, width=30)
        self.qty_entry.grid(row=4, column=1)

        self.save_btn = tk.Button(
            form,
            text="Add Medicine",
            bg="#51fd0d",
            fg="white",
            activebackground="#2ad70b",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            command=self.add_medicine
        )
        self.save_btn.grid(row=5, column=0, columnspan=2, pady=10)

        self.selected_medicine_id = None

        # -------- TABLE --------
        table_frame = ttk.LabelFrame(frame, text="Inventory List", padding=20)
        table_frame.pack(fill="both", expand=True)

        columns = ("ID", "Name", "Type", "Price", "Quantity", "Expiry", "Edit", "Delete")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree.pack(fill="both", expand=True)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=150 if col not in ("Edit", "Delete") else 110)

        self.tree.bind("<Button-1>", self.handle_inventory_click)
        self.load_inventory()

    def add_medicine(self):
        try:
            name = self.name_entry.get().strip()
            med_type = self.type_combo.get()
            expiry = datetime.strptime(self.expiry_entry.get().strip(), "%Y-%m-%d").date()
            price = float(self.price_entry.get())
            quantity = int(self.qty_entry.get())

            if expiry < date.today():
                messagebox.showerror("Error", "Cannot add expired medicine.")
                return

            cursor = self.db.cursor(dictionary=True)
            if self.selected_medicine_id:
                # Update existing medicine
                cursor.execute(
                    "UPDATE medicines SET name=%s, type=%s, expiry_date=%s, price=%s, quantity=%s WHERE id=%s",
                    (name, med_type, expiry, price, quantity, self.selected_medicine_id)
                )
                self.selected_medicine_id = None
            else:
                # Add new medicine
                cursor.execute(
                    "INSERT INTO medicines (name, type, expiry_date, price, quantity) VALUES (%s, %s, %s, %s, %s)",
                    (name, med_type, expiry, price, quantity)
                )

            self.db.commit()
            messagebox.showinfo("Success", "Medicine saved successfully.")
            self.clear_inventory_form()
            self.load_inventory()

            if hasattr(self, "load_medicines_for_sale"):
                self.load_medicines_for_sale()

        except Exception as e:
            self.db.rollback()
            messagebox.showerror("Error", str(e))

    def load_inventory(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        cursor = self.db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM medicines")
        medicines = cursor.fetchall()

        for med in medicines:
            self.tree.insert(
                "",
                "end",
                values=(
                    med['id'],
                    med['name'],
                    med['type'],
                    med['price'],
                    med['quantity'],
                    med['expiry_date'],
                    "Edit",
                    "Delete"
                )
            )

    def handle_inventory_click(self, event):
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)

        if not item:
            return

        col_index = int(column.replace("#", "")) - 1
        values = self.tree.item(item, "values")
        med_id = values[0]

        if col_index == 6:
            self.edit_medicine(med_id)
        elif col_index == 7:
            self.delete_medicine(med_id)

    def edit_medicine(self, med_id):
        cursor = self.db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM medicines WHERE id=%s", (med_id,))
        medicine = cursor.fetchone()
        if not medicine:
            return

        self.selected_medicine_id = med_id
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, medicine['name'])
        self.type_combo.set(medicine['type'])
        self.expiry_entry.delete(0, tk.END)
        self.expiry_entry.insert(0, str(medicine['expiry_date']))
        self.price_entry.delete(0, tk.END)
        self.price_entry.insert(0, medicine['price'])
        self.qty_entry.delete(0, tk.END)
        self.qty_entry.insert(0, medicine['quantity'])

    def delete_medicine(self, med_id):
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this medicine?")
        if not confirm:
            return

        cursor = self.db.cursor()
        cursor.execute("DELETE FROM medicines WHERE id=%s", (med_id,))
        self.db.commit()
        self.load_inventory()

    def clear_inventory_form(self):
        self.name_entry.delete(0, tk.END)
        self.type_combo.set("Tablet")
        self.expiry_entry.delete(0, tk.END)
        self.price_entry.delete(0, tk.END)
        self.qty_entry.delete(0, tk.END)
        self.selected_medicine_id = None