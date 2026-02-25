import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import re


class SalesMixin:

    def build_sales_tab(self):
        frame = ttk.Frame(self.sales_tab, padding=20)
        frame.pack(fill="both", expand=True)

        self.cart = []
        self.cart_panel_open = False
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
            text="A = units, B = times/day, C = days",
            foreground="#0d6efd",
        )
        self.prescription_hint.grid(row=4, column=0, columnspan=2, sticky="w")

        self.sale_combo.bind("<<ComboboxSelected>>", self.update_prescription_hint)
        self.sale_combo.bind("<KeyRelease>", self.filter_medicines_for_sale)
        self.patient_combo.bind("<KeyRelease>", self.filter_patients_for_sale)
        self.patient_combo.bind("<Button-1>", lambda _e: self.load_patients_for_sale())

        tk.Button(
            form,
            text="Add to Cart",
            bg="#51fd0d",
            fg="white",
            width=20,
            command=self.add_item_to_cart,
        ).grid(row=5, column=0, columnspan=2, pady=10)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="View Cart",
            bg="#6c757d",
            fg="white",
            width=15,
            command=lambda: self.toggle_cart_panel(True),
        ).pack(side="left", padx=10)

        tk.Button(
            btn_frame,
            text="Refresh",
            bg="#17a2b8",
            fg="white",
            width=15,
            command=self.refresh_sales_tab,
        ).pack(side="left", padx=10)

        tk.Button(
            btn_frame,
            text="Clear Cart",
            bg="#dc3545",
            fg="white",
            width=15,
            command=self.clear_cart,
        ).pack(side="left", padx=10)

        body = ttk.Frame(frame)
        body.pack(fill="both", expand=True)

        history_frame = ttk.LabelFrame(body, text="Sales History", padding=15)
        history_frame.pack(side="left", fill="both", expand=True)

        columns = ("ID", "Patient", "Date", "Prescription", "Total")
        self.sales_tree = ttk.Treeview(history_frame, columns=columns, show="headings")
        self.sales_tree.pack(fill="both", expand=True)

        for col in columns:
            self.sales_tree.heading(col, text=col)
            self.sales_tree.column(col, width=150)

        self.cart_panel = ttk.LabelFrame(body, text="Cart", padding=10)

        cart_columns = ("Medicine", "Prescription", "Qty", "Price", "Subtotal")
        self.cart_tree = ttk.Treeview(self.cart_panel, columns=cart_columns, show="headings", height=14)
        self.cart_tree.pack(fill="both", expand=True)

        for col in cart_columns:
            self.cart_tree.heading(col, text=col)
            self.cart_tree.column(col, width=110, anchor="center")

        self.cart_total_label = ttk.Label(self.cart_panel, text="Total: 0.00", font=("Arial", 11, "bold"))
        self.cart_total_label.pack(pady=8)

        cart_btn_frame = ttk.Frame(self.cart_panel)
        cart_btn_frame.pack(pady=5)

        tk.Button(
            cart_btn_frame,
            text="Checkout",
            bg="#007bff",
            fg="white",
            width=12,
            command=self.finalize_sale,
        ).pack(side="left", padx=5)

        tk.Button(
            cart_btn_frame,
            text="Clear",
            bg="#dc3545",
            fg="white",
            width=12,
            command=self.clear_cart,
        ).pack(side="left", padx=5)

        tk.Button(
            cart_btn_frame,
            text="Close",
            bg="#6c757d",
            fg="white",
            width=12,
            command=lambda: self.toggle_cart_panel(False),
        ).pack(side="left", padx=5)

        self.load_medicines_for_sale()
        self.load_patients_for_sale()
        self.refresh_sales_tab()

    def ensure_sale_item_prescription_column(self):
        try:
            self.cursor.execute("SHOW COLUMNS FROM sale_items LIKE 'prescription'")
            has_prescription = self.cursor.fetchone() is not None
            if not has_prescription:
                self.cursor.execute("ALTER TABLE sale_items ADD COLUMN prescription VARCHAR(255)")
                self.conn.commit()
        except Exception:
            self.conn.rollback()

    def toggle_cart_panel(self, show=None):
        target = (not self.cart_panel_open) if show is None else show

        if target and not self.cart_panel_open:
            self.cart_panel.pack(side="right", fill="y", padx=(12, 0))
            self.cart_panel_open = True
        elif not target and self.cart_panel_open:
            self.cart_panel.pack_forget()
            self.cart_panel_open = False

        if self.cart_panel_open:
            self.refresh_cart_panel()

    def refresh_cart_panel(self):
        for row in self.cart_tree.get_children():
            self.cart_tree.delete(row)

        for item in self.cart:
            med = item["medicine"]
            self.cart_tree.insert(
                "",
                "end",
                values=(
                    med["name"],
                    item.get("prescription", "-"),
                    item["quantity"],
                    med["price"],
                    item["subtotal"],
                ),
            )

        total = sum(item["subtotal"] for item in self.cart)
        self.cart_total_label.config(text=f"Total: {total:.2f}")

    def add_item_to_cart(self):
        med_name = self.sale_combo.get().strip()
        qty_text = self.sale_qty.get().strip()
        prescription_text = self.prescription_entry.get().strip()

        if not med_name or not qty_text:
            messagebox.showerror("Error", "Medicine and quantity required")
            return

        try:
            quantity = int(qty_text)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a positive integer.")
            return

        med = self.medicine_map.get(med_name)
        if not med or med["quantity"] <= 0:
            messagebox.showerror("Error", "Medicine not available or out of stock.")
            return

        if not prescription_text:
            messagebox.showerror("Error", "Prescription required (A*B*C).")
            return

        dosage = self.parse_prescription(prescription_text)
        if dosage is None:
            messagebox.showerror("Error", "Invalid prescription format A*B*C")
            return

        existing_qty = sum(item["quantity"] for item in self.cart if item["medicine"]["id"] == med["id"])
        if existing_qty + quantity > med["quantity"]:
            messagebox.showerror("Error", f"Only {med['quantity'] - existing_qty} left in stock")
            return

        for item in self.cart:
            if item["medicine"]["id"] == med["id"] and item["prescription"] == prescription_text:
                item["quantity"] += quantity
                item["subtotal"] = item["quantity"] * med["price"]
                break
        else:
            self.cart.append(
                {
                    "medicine": med,
                    "quantity": quantity,
                    "subtotal": quantity * med["price"],
                    "prescription": prescription_text,
                    "dosage": dosage,
                }
            )

        self.sale_qty.delete(0, tk.END)
        self.prescription_entry.delete(0, tk.END)
        self.refresh_cart_panel()
        self.toggle_cart_panel(True)

    def parse_prescription(self, text):
        match = re.fullmatch(r"\s*(\d+)\*(\d+)\*(\d+)\s*", text)
        if not match:
            return None
        a, b, c = map(int, match.groups())
        if a <= 0 or b <= 0 or c <= 0:
            return None
        return a, b, c

    def update_prescription_hint(self, event=None):
        med_name = self.sale_combo.get().strip()
        med = self.medicine_map.get(med_name)
        med_type = (med.get("type") or "").lower() if med else ""

        if med_type in ("tablet", "capsule"):
            unit = "tabs/caps"
        elif med_type == "syrup":
            unit = "ml"
        else:
            unit = "units"

        self.prescription_hint.config(text=f"A = {unit}, B = times/day, C = days")

    def clear_cart(self):
        self.cart = []
        self.refresh_cart_panel()

    def finalize_sale(self):
        if not self.cart:
            messagebox.showerror("Error", "Cart is empty")
            return

        patient_name = self.patient_combo.get().strip()
        patient = self.patient_map.get(patient_name)
        if not patient:
            messagebox.showerror("Error", "Please select a valid patient")
            return

        try:
            for item in self.cart:
                med = item["medicine"]
                if med["quantity"] < item["quantity"]:
                    raise ValueError(f"Insufficient stock for {med['name']}")

            total = sum(item["subtotal"] for item in self.cart)
            self.cursor.execute(
                "INSERT INTO sales (sale_date, total_amount, patient_id) VALUES (%s, %s, %s)",
                (date.today(), total, patient["id"]),
            )
            sale_id = self.cursor.lastrowid

            for item in self.cart:
                med = item["medicine"]
                self.cursor.execute(
                    "UPDATE medicines SET quantity = quantity - %s WHERE id=%s",
                    (item["quantity"], med["id"]),
                )
                self.cursor.execute(
                    "INSERT INTO sale_items (sale_id, medicine_id, quantity, subtotal, prescription) VALUES (%s, %s, %s, %s, %s)",
                    (sale_id, med["id"], item["quantity"], item["subtotal"], item.get("prescription")),
                )

            self.conn.commit()
            self.cart = []
            self.refresh_cart_panel()
            self.toggle_cart_panel(False)
            self.load_medicines_for_sale()
            self.refresh_sales_tab()
            if hasattr(self, "load_inventory"):
                self.load_inventory()
            messagebox.showinfo("Success", "Sale completed successfully")
        except Exception as exc:
            self.conn.rollback()
            messagebox.showerror("Error", str(exc))

    def load_medicines_for_sale(self):
        self.medicine_map = {}
        self.all_medicine_names = []

        self.cursor.execute("SELECT id, name, type, price, quantity FROM medicines")
        for med in self.cursor.fetchall():
            med_dict = {"id": med[0], "name": med[1], "type": med[2], "price": med[3], "quantity": med[4]}
            self.medicine_map[med[1]] = med_dict
            self.all_medicine_names.append(med[1])

        self.sale_combo["values"] = tuple(self.all_medicine_names)

    def load_patients_for_sale(self):
        self.patient_map = {}
        self.all_patient_names = []

        self.cursor.execute("SELECT id, name FROM patients")
        for pat in self.cursor.fetchall():
            self.patient_map[pat[1]] = {"id": pat[0], "name": pat[1]}
            self.all_patient_names.append(pat[1])

        self.patient_combo["values"] = tuple(self.all_patient_names)

    def filter_medicines_for_sale(self, event=None):
        query = self.sale_combo.get().strip().lower()
        self.sale_combo["values"] = tuple([name for name in self.all_medicine_names if query in name.lower()])

    def filter_patients_for_sale(self, event=None):
        query = self.patient_combo.get().strip().lower()
        self.patient_combo["values"] = tuple([name for name in self.all_patient_names if query in name.lower()])

    def refresh_sales_tab(self):
        for row in self.sales_tree.get_children():
            self.sales_tree.delete(row)

        self.cursor.execute(
            """
            SELECT s.id, p.name, s.sale_date, s.total_amount
            FROM sales s
            LEFT JOIN patients p ON s.patient_id = p.id
            ORDER BY s.id DESC
            """
        )
        sales = self.cursor.fetchall()

        try:
            for sale in sales:
                sale_id, patient_name, sale_date, total = sale
                self.cursor.execute(
                    """
                    SELECT m.name, si.prescription
                    FROM sale_items si
                    LEFT JOIN medicines m ON si.medicine_id = m.id
                    WHERE si.sale_id = %s
                    """,
                    (sale_id,),
                )
                items = self.cursor.fetchall()
                prescription_text = " ; ".join([f"{m}:{presc}" for m, presc in items]) if items else "-"
                self.sales_tree.insert("", "end", values=(sale_id, patient_name, sale_date, prescription_text, total))
        except Exception:
            for sale in sales:
                sale_id, patient_name, sale_date, total = sale
                self.sales_tree.insert("", "end", values=(sale_id, patient_name, sale_date, "-", total))
