import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

class PatientMixin:

    def build_patients_tab(self):
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

        tk.Button(
            form,
            text="Add Patient",
            bg="#28a745",
            fg="white",
            width=20,
            command=self.add_patient
        ).grid(row=3, column=0, columnspan=2, pady=10)

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
        name = self.patient_name.get().strip()
        age_text = self.patient_age.get().strip()
        history = self.patient_history.get().strip()

        if not name or not age_text:
            messagebox.showerror("Error", "Name and age required.")
            return

        try:
            age = int(age_text)
            if age <= 0:
                messagebox.showerror("Error", "Age must be greater than 0.")
                return
        except:
            messagebox.showerror("Error", "Invalid age.")
            return

        try:
            self.db.cursor.execute(
                "INSERT INTO patients (name, age, medical_history) VALUES (%s, %s, %s)",
                (name, age, history)
            )
            self.db.commit()
            messagebox.showinfo("Success", "Patient added successfully.")
            self.patient_name.delete(0, tk.END)
            self.patient_age.delete(0, tk.END)
            self.patient_history.delete(0, tk.END)
            self.load_patients()
            if hasattr(self, "load_patients_for_sale"):
                self.load_patients_for_sale()
        except Exception as e:
            self.db.rollback()
            messagebox.showerror("Error", str(e))

    def load_patients(self):
        for row in self.patient_list.get_children():
            self.patient_list.delete(row)

        self.db.cursor.execute("SELECT * FROM patients")
        patients = self.db.cursor.fetchall()
        for p in patients:
            self.patient_list.insert(
                "",
                "end",
                values=(p['id'], p['name'], p['age'], p['medical_history'], "Edit", "Delete")
            )

    def handle_patient_action(self, event):
        item = self.patient_list.identify_row(event.y)
        column = self.patient_list.identify_column(event.x)
        if not item:
            return
        col_index = int(column.replace("#", "")) - 1
        if col_index not in (4, 5):
            return
        values = self.patient_list.item(item, "values")
        patient_id = values[0]

        if col_index == 4:
            self.edit_patient(patient_id)
        elif col_index == 5:
            self.delete_patient(patient_id)

    def edit_patient(self, patient_id):
        self.db.cursor.execute("SELECT * FROM patients WHERE id=%s", (patient_id,))
        patient = self.db.cursor.fetchone()
        if not patient:
            return

        self.patient_name.delete(0, tk.END)
        self.patient_name.insert(0, patient['name'])
        self.patient_age.delete(0, tk.END)
        self.patient_age.insert(0, str(patient['age']))
        self.patient_history.delete(0, tk.END)
        self.patient_history.insert(0, patient['medical_history'])

        def update():
            name = self.patient_name.get().strip()
            try:
                age = int(self.patient_age.get())
                if age <= 0:
                    messagebox.showerror("Error", "Age must be > 0")
                    return
            except:
                messagebox.showerror("Error", "Invalid age")
                return
            history = self.patient_history.get().strip()
            try:
                self.db.cursor.execute(
                    "UPDATE patients SET name=%s, age=%s, medical_history=%s WHERE id=%s",
                    (name, age, history, patient_id)
                )
                self.db.commit()
                messagebox.showinfo("Success", "Patient updated.")
                self.load_patients()
                if hasattr(self, "load_patients_for_sale"):
                    self.load_patients_for_sale()
            except Exception as e:
                self.db.rollback()
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

    def delete_patient(self, patient_id):
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure?")
        if not confirm:
            return
        try:
            self.db.cursor.execute("DELETE FROM patients WHERE id=%s", (patient_id,))
            self.db.commit()
            messagebox.showinfo("Success", "Patient deleted.")
            self.load_patients()
            if hasattr(self, "load_patients_for_sale"):
                self.load_patients_for_sale()
        except Exception as e:
            self.db.rollback()
            messagebox.showerror("Error", str(e))