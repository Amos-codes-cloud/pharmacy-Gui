import tkinter as tk
from tkinter import ttk, messagebox
from sqlalchemy import text
from models import Patient, Sale

class PatientMixin:

    def build_patients_tab(self):
        self.ensure_patient_age_column()

        frame = ttk.Frame(self.patients_tab, padding=20)
        frame.pack(fill="both", expand=True)

        # -------- FORM --------
        form = ttk.LabelFrame(frame, text="Register Patient", padding=15)
        form.pack(fill="x", pady=10)

        ttk.Label(form, text="Name").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.patient_name = ttk.Entry(form, width=30)
        self.patient_name.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form, text="Age").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.patient_age = ttk.Entry(form, width=30)
        self.patient_age.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form, text="Medical History").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.patient_history = ttk.Entry(form, width=30)
        self.patient_history.grid(row=2, column=1, padx=5, pady=5)

        add_btn = tk.Button(
            form,
            text="Add Patient",
            bg="#28a745",
            fg="white",
            width=20,
            command=self.add_patient
        )
        add_btn.grid(row=3, column=0, columnspan=2, pady=10)

        # -------- TABLE --------
        table_frame = ttk.LabelFrame(frame, text="Patients List", padding=10)
        table_frame.pack(fill="both", expand=True)

        columns = ("ID", "Name", "Age", "History", "Edit", "Delete")
        self.patient_list = ttk.Treeview(table_frame, columns=columns, show="headings")

        for col in columns:
            self.patient_list.heading(col, text=col)

        self.patient_list.column("ID", width=60)
        self.patient_list.column("Name", width=180)
        self.patient_list.column("Age", width=80)
        self.patient_list.column("History", width=110)
        self.patient_list.column("Edit", width=110)
        self.patient_list.column("Delete", width=110)

        self.patient_list.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.patient_list.yview)
        scrollbar.pack(side="right", fill="y")
        self.patient_list.configure(yscrollcommand=scrollbar.set)

        self.patient_list.bind("<Button-1>", self.handle_patient_action)

        self.load_patients()


    def add_patient(self):
        try:
            name = self.patient_name.get().strip()
            age_text = self.patient_age.get().strip()
            history = self.patient_history.get().strip()

            if not name or not age_text:
                messagebox.showerror("Error", "Name and age required.")
                return

            age = int(age_text)
            if age <= 0:
                messagebox.showerror("Error", "Age must be greater than 0.")
                return

            patient = Patient(
                name=name,
                age=age,
                medical_history=history
            )

            self.session.add(patient)
            self.session.commit()

            messagebox.showinfo("Success", "Patient added successfully.")

            self.patient_name.delete(0, tk.END)
            self.patient_age.delete(0, tk.END)
            self.patient_history.delete(0, tk.END)

            self.load_patients()
            self.load_patients_for_sale()

        except Exception as e:
            self.session.rollback()
            messagebox.showerror("Error", str(e))


    def load_patients(self):
        for row in self.patient_list.get_children():
            self.patient_list.delete(row)

        patients = self.session.query(Patient).all()

        for p in patients:
            self.patient_list.insert(
                "",
                "end",
                values=(p.id, p.name, p.age if p.age is not None else "-", "View", "Edit", "Delete")
            )


    def handle_patient_action(self, event):
        item = self.patient_list.identify_row(event.y)
        column = self.patient_list.identify_column(event.x)

        if not item:
            return

        col_index = int(column.replace("#", "")) - 1
        if col_index not in (3, 4, 5):
            return

        values = self.patient_list.item(item, "values")
        patient_id = values[0]

        if col_index == 3:
            self.view_patient_history(patient_id)
        elif col_index == 4:
            self.edit_patient(patient_id)
        elif col_index == 5:
            self.delete_patient(patient_id)


    def view_patient_history(self, patient_id):
        patient = self.session.query(Patient).get(patient_id)
        if not patient:
            messagebox.showerror("Error", "Patient not found.")
            return

        history_window = tk.Toplevel(self.root)
        history_window.title(f"Sales History - {patient.name}")
        history_window.geometry("900x500")

        frame = ttk.Frame(history_window, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=f"Patient: {patient.name} (Age: {patient.age if patient.age else 'N/A'})", font=("Arial", 12, "bold")).pack(pady=10)

        # Medical History section
        med_history_frame = ttk.LabelFrame(frame, text="Medical History", padding=10)
        med_history_frame.pack(fill="x", pady=(0, 15))
        
        med_history_text = patient.medical_history if patient.medical_history else "No medical history recorded."
        ttk.Label(med_history_frame, text=med_history_text, wraplength=800, justify="left").pack()

        # Sales History section
        ttk.Label(frame, text="Sales History", font=("Arial", 11, "bold")).pack(pady=(5, 5))

        # Create treeview
        columns = ("Sale ID", "Date", "Medicine", "Quantity", "Prescription", "Subtotal", "Total")
        tree = ttk.Treeview(frame, columns=columns, show="headings")

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center")

        tree.column("Sale ID", width=70)
        tree.column("Date", width=100)
        tree.column("Medicine", width=200)
        tree.column("Quantity", width=80)
        tree.column("Prescription", width=120)
        tree.column("Subtotal", width=100)
        tree.column("Total", width=100)

        tree.pack(fill="both", expand=True)

        # Load sales history
        sales = self.session.query(Sale).filter_by(patient_id=patient_id).order_by(Sale.sale_date.desc()).all()

        if not sales:
            ttk.Label(frame, text="No sales history found.", font=("Arial", 10)).pack(pady=20)
        else:
            for sale in sales:
                for item in sale.items:
                    tree.insert(
                        "",
                        "end",
                        values=(
                            sale.id,
                            sale.sale_date,
                            item.medicine.name if item.medicine else "N/A",
                            item.quantity,
                            item.prescription if item.prescription else "-",
                            f"${item.subtotal:.2f}" if item.subtotal else "-",
                            f"${sale.total_amount:.2f}" if sale.total_amount else "-"
                        )
                    )

        close_btn = tk.Button(
            frame,
            text="Close",
            bg="#6c757d",
            fg="white",
            command=history_window.destroy
        )
        close_btn.pack(pady=10)

    def delete_patient(self, patient_id):
        try:
            patient = self.session.query(Patient).get(patient_id)
            if not patient:
                return

            confirm = messagebox.askyesno("Confirm", "Delete this patient?")
            if not confirm:
                return

            self.session.delete(patient)
            self.session.commit()

            messagebox.showinfo("Success", "Patient deleted.")
            self.load_patients()
            self.load_patients_for_sale()

        except Exception as e:
            self.session.rollback()
            messagebox.showerror("Error", str(e))


    def edit_patient(self, patient_id):
        patient = self.session.query(Patient).get(patient_id)
        if not patient:
            return

        self.patient_name.delete(0, tk.END)
        self.patient_name.insert(0, patient.name)

        self.patient_age.delete(0, tk.END)
        self.patient_age.insert(0, str(patient.age if patient.age is not None else ""))

        self.patient_history.delete(0, tk.END)
        self.patient_history.insert(0, patient.medical_history)

        def update():
            try:
                patient.name = self.patient_name.get()
                patient.age = int(self.patient_age.get())
                if patient.age <= 0:
                    messagebox.showerror("Error", "Age must be greater than 0.")
                    return
                patient.medical_history = self.patient_history.get()

                self.session.commit()
                messagebox.showinfo("Success", "Patient updated.")
                self.load_patients()
                self.load_patients_for_sale()
            except Exception as e:
                self.session.rollback()
                messagebox.showerror("Error", str(e))

        update_btn = tk.Button(
            self.patients_tab,
            text="Update Patient",
            bg="#0d6efd",
            fg="white",
            activebackground="#0b5ed7",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            command=update
        )
        update_btn.pack(pady=5)

    def ensure_patient_age_column(self):
        try:
            rows = self.session.execute(text("PRAGMA table_info(patients)")).fetchall()
            existing_columns = {row[1] for row in rows}
            if "age" not in existing_columns:
                self.session.execute(text("ALTER TABLE patients ADD COLUMN age INTEGER"))
                self.session.commit()
        except Exception:
            self.session.rollback()
