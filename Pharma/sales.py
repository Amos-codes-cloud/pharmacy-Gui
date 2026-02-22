import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import re
from sqlalchemy import text
from models import Sale, SaleItem, Patient, Medicine


class SalesMixin:

    def build_sales_tab(self):
        frame = ttk.Frame(self.sales_tab, padding=20)
        frame.pack(fill="both", expand=True)

        self.cart = []
        self.ensure_sale_item_prescription_column()

        form = ttk.LabelFrame(frame, text="Create Sale", padding=15)
        form.pack(fill="x", pady=10)

        ttk.Label(form, text="Patient").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.patient_combo = ttk.Combobox(form, width=35)
        self.patient_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Medicine").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.sale_combo = ttk.Combobox(form, width=35)
        self.sale_combo.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form, text="Quantity").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.sale_qty = ttk.Entry(form, width=38)
        self.sale_qty.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(form, text="Prescription (A*B*C)").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.prescription_entry = ttk.Entry(form, width=38)
        self.prescription_entry.grid(row=3, column=1, padx=5, pady=5)

        self.prescription_hint = ttk.Label(
            form,
            text="A = units (tabs/caps/ml), B = times per day, C = days",
            foreground="#0d6efd"
        )
        self.prescription_hint.grid(row=4, column=0, columnspan=2, padx=5, pady=(0, 5), sticky="w")

        self.sale_combo.bind("<<ComboboxSelected>>", self.update_prescription_hint)
        self.sale_combo.bind("<KeyRelease>", self.filter_medicines_for_sale)
        self.patient_combo.bind("<KeyRelease>", self.filter_patients_for_sale)

        tk.Button(
            form,
            text="Add to Cart",
            bg="#28a745",
            fg="white",
            width=20,
            command=self.add_item_to_cart
        ).grid(row=5, column=0, columnspan=2, pady=10)

        # Action Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="View Cart",
            bg="#6c757d",
            fg="white",
            width=15,
            command=self.open_cart_window
        ).pack(side="left", padx=10)

        tk.Button(
            btn_frame,
            text="Refresh",
            bg="#17a2b8",
            fg="white",
            width=15,
            command=self.refresh_sales_tab
        ).pack(side="left", padx=10)

        tk.Button(
            btn_frame,
            text="Clear Cart",
            bg="#dc3545",
            fg="white",
            width=15,
            command=self.clear_cart
        ).pack(side="left", padx=10)

        # Sales history
        history_frame = ttk.LabelFrame(frame, text="Sales History", padding=15)
        history_frame.pack(fill="both", expand=True)

        columns = ("ID", "Patient", "Date", "Prescription", "Total")
        self.sales_tree = ttk.Treeview(history_frame, columns=columns, show="headings")
        self.sales_tree.pack(fill="both", expand=True)

        for col in columns:
            self.sales_tree.heading(col, text=col)
            self.sales_tree.column(col, width=150)

        self.load_medicines_for_sale()
        self.load_patients_for_sale()
        self.refresh_sales_tab()  # now safe

    def ensure_sale_item_prescription_column(self):
        try:
            rows = self.session.execute(text("PRAGMA table_info(sale_items)")).fetchall()
            existing_columns = {row[1] for row in rows}
            if "prescription" not in existing_columns:
                self.session.execute(text("ALTER TABLE sale_items ADD COLUMN prescription VARCHAR"))
                self.session.commit()
        except Exception:
            self.session.rollback()

    def add_item_to_cart(self):
        med_name = self.sale_combo.get().strip()
        qty_text = self.sale_qty.get().strip()
        prescription_text = self.prescription_entry.get().strip()

        if not med_name:
            messagebox.showerror("Error", "Please select a medicine.")
            return

        try:
            quantity = int(qty_text)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a positive integer.")
            return

        medicine = self.medicine_map.get(med_name)
        if not medicine:
            messagebox.showerror("Error", "Selected medicine is not available.")
            return

        if not prescription_text:
            messagebox.showerror("Error", "Prescription is required (A*B*C).")
            return

        dosage = self.parse_prescription(prescription_text)
        if dosage is None:
            messagebox.showerror(
                "Error",
                "Invalid prescription format. Use A*B*C where A,B,C are positive numbers."
            )
            return

        if medicine.quantity is None or medicine.quantity <= 0:
            messagebox.showerror("Error", "Medicine is out of stock.")
            return

        existing_qty = 0
        for item in self.cart:
            if item["medicine"].id == medicine.id:
                existing_qty += item["quantity"]

        if existing_qty + quantity > medicine.quantity:
            messagebox.showerror("Error", f"Only {medicine.quantity - existing_qty} unit(s) left for this item.")
            return

        for item in self.cart:
            if item["medicine"].id == medicine.id and item["prescription"] == prescription_text:
                item["quantity"] += quantity
                item["subtotal"] = item["quantity"] * medicine.price
                break
        else:
            self.cart.append({
                "medicine": medicine,
                "quantity": quantity,
                "subtotal": quantity * medicine.price,
                "prescription": prescription_text,
                "dosage": dosage,
            })

        self.sale_qty.delete(0, tk.END)
        self.prescription_entry.delete(0, tk.END)
        messagebox.showinfo("Added", "Item added to cart.")

    def parse_prescription(self, prescription_text):
        match = re.fullmatch(r"\s*(\d+)\*(\d+)\*(\d+)\s*", prescription_text)
        if not match:
            return None

        a, b, c = map(int, match.groups())
        if a <= 0 or b <= 0 or c <= 0:
            return None

        return a, b, c

    def update_prescription_hint(self, event=None):
        med_name = self.sale_combo.get().strip()
        medicine = self.medicine_map.get(med_name)
        med_type = (medicine.type.lower() if medicine and medicine.type else "")

        if med_type in ("tablet", "capsule"):
            unit = "tabs/caps"
        elif med_type == "syrup":
            unit = "mls"
        else:
            unit = "units"

        self.prescription_hint.config(
            text=f"A = no. of {unit}, B = times per day, C = no. of usage days (Format: A*B*C)"
        )

    def clear_cart(self):
        self.cart = []
        messagebox.showinfo("Cart", "Cart cleared.")

    def open_cart_window(self):
        window = tk.Toplevel(self.sales_tab)
        window.title("Cart")
        window.geometry("700x400")

        columns = ("Medicine", "Prescription", "Qty", "Price", "Subtotal")
        cart_tree = ttk.Treeview(window, columns=columns, show="headings")
        cart_tree.pack(fill="both", expand=True, padx=10, pady=10)

        for col in columns:
            cart_tree.heading(col, text=col)
            cart_tree.column(col, width=150, anchor="center")

        for item in self.cart:
            cart_tree.insert(
                "",
                "end",
                values=(
                    item["medicine"].name,
                    item.get("prescription", "-"),
                    item["quantity"],
                    item["medicine"].price,
                    item["subtotal"],
                ),
            )

        total = sum(item["subtotal"] for item in self.cart)
        total_label = ttk.Label(window, text=f"Total: {total:.2f}", font=("Arial", 12, "bold"))
        total_label.pack(pady=5)

        btn_frame = ttk.Frame(window)
        btn_frame.pack(pady=10)

        def remove_selected_item():
            selected = cart_tree.focus()
            if not selected:
                return

            values = cart_tree.item(selected, "values")
            if not values:
                return

            med_name = values[0]
            self.cart = [item for item in self.cart if item["medicine"].name != med_name]
            cart_tree.delete(selected)

            new_total = sum(item["subtotal"] for item in self.cart)
            total_label.config(text=f"Total: {new_total:.2f}")

        tk.Button(
            btn_frame,
            text="Remove Selected",
            bg="#ffc107",
            width=15,
            command=remove_selected_item,
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame,
            text="Checkout",
            bg="#007bff",
            fg="white",
            width=15,
            command=lambda: self.finalize_sale(window),
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame,
            text="Close",
            bg="#6c757d",
            fg="white",
            width=15,
            command=window.destroy,
        ).pack(side="left", padx=5)

    def finalize_sale(self, cart_window=None):
        if not self.cart:
            messagebox.showerror("Error", "Cart is empty.")
            return

        patient_name = self.patient_combo.get().strip()
        patient = self.patient_map.get(patient_name)
        if not patient:
            messagebox.showerror("Error", "Please select a valid patient.")
            return

        try:
            for item in self.cart:
                med = self.session.query(Medicine).get(item["medicine"].id)
                if not med or med.quantity < item["quantity"]:
                    raise ValueError(f"Insufficient stock for {item['medicine'].name}.")

            total = sum(item["subtotal"] for item in self.cart)
            sale = Sale(
                sale_date=date.today(),
                total_amount=total,
                patient_id=patient.id,
            )
            self.session.add(sale)
            self.session.flush()

            for item in self.cart:
                med = self.session.query(Medicine).get(item["medicine"].id)
                med.quantity -= item["quantity"]

                self.session.add(
                    SaleItem(
                        sale_id=sale.id,
                        medicine_id=med.id,
                        quantity=item["quantity"],
                        subtotal=item["subtotal"],
                        prescription=item.get("prescription"),
                    )
                )

            self.session.commit()

            self.cart = []
            self.sale_qty.delete(0, tk.END)
            self.prescription_entry.delete(0, tk.END)

            self.load_medicines_for_sale()
            self.refresh_sales_tab()

            if hasattr(self, "load_inventory"):
                self.load_inventory()

            if cart_window is not None:
                cart_window.destroy()

            messagebox.showinfo("Success", "Sale completed successfully.")

        except Exception as e:
            self.session.rollback()
            messagebox.showerror("Error", str(e))

    def refresh_sales_tab(self):
        # Clear sales tree
        for item in self.sales_tree.get_children():
            self.sales_tree.delete(item)

        # Load sales
        sales = self.session.query(Sale).order_by(Sale.id.desc()).all()
        for sale in sales:
            patient_name = sale.patient.name if sale.patient else "N/A"
            prescriptions = []
            for item in sale.items:
                if getattr(item, "prescription", None):
                    med_name = item.medicine.name if item.medicine else "Medicine"
                    prescriptions.append(f"{med_name}:{item.prescription}")

            prescription_text = " ; ".join(prescriptions) if prescriptions else "-"
            self.sales_tree.insert(
                "",
                "end",
                values=(sale.id, patient_name, sale.sale_date, prescription_text, sale.total_amount)
            )

    def load_medicines_for_sale(self):
        self.medicine_map = {}
        self.all_medicine_names = []

        medicines = self.session.query(Medicine).all()
        for med in medicines:
            self.medicine_map[med.name] = med
            self.all_medicine_names.append(med.name)

        self.sale_combo['values'] = tuple(self.all_medicine_names)

    def load_patients_for_sale(self):
        self.patient_map = {}
        self.all_patient_names = []

        patients = self.session.query(Patient).all()
        for patient in patients:
            self.patient_map[patient.name] = patient
            self.all_patient_names.append(patient.name)

        self.patient_combo['values'] = tuple(self.all_patient_names)

    def filter_medicines_for_sale(self, event=None):
        query = self.sale_combo.get().strip().lower()
        if not query:
            matches = self.all_medicine_names
        else:
            matches = [name for name in self.all_medicine_names if query in name.lower()]
        self.sale_combo["values"] = tuple(matches)

    def filter_patients_for_sale(self, event=None):
        query = self.patient_combo.get().strip().lower()
        if not query:
            matches = self.all_patient_names
        else:
            matches = [name for name in self.all_patient_names if query in name.lower()]
        self.patient_combo["values"] = tuple(matches)