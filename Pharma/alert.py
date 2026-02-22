import tkinter as tk
from tkinter import ttk
from datetime import date
from models import Medicine


class AlertMixin:

    def build_alerts_tab(self):
        frame = ttk.Frame(self.alerts_tab, padding=30)
        frame.pack(fill="both", expand=True)

        header = ttk.Frame(frame)
        header.pack(fill="x", pady=(0, 10))

        ttk.Label(
            header,
            text="Drug Alerts (Expired / Expiring Soon / Low Stock)",
            font=("Arial", 12, "bold")
        ).pack(side="left")

        ttk.Button(header, text="Refresh Alerts", command=self.load_alerts).pack(side="right")

        table_frame = ttk.LabelFrame(frame, text="Alerts", padding=15)
        table_frame.pack(fill="both", expand=True)

        columns = ("Medicine", "Type", "Quantity Left", "Expiry Date", "Days Left", "Alert")
        self.alerts_tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.alerts_tree.pack(side="left", fill="both", expand=True)

        widths = {
            "Medicine": 220,
            "Type": 120,
            "Quantity Left": 120,
            "Expiry Date": 140,
            "Days Left": 120,
            "Alert": 380,
        }

        for col in columns:
            self.alerts_tree.heading(col, text=col)
            self.alerts_tree.column(col, anchor="center", width=widths[col])

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.alerts_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.alerts_tree.configure(yscrollcommand=scrollbar.set)

        self.load_alerts()

    def load_alerts(self):
        for row in self.alerts_tree.get_children():
            self.alerts_tree.delete(row)

        medicines = self.session.query(Medicine).all()
        today = date.today()

        for med in medicines:
            quantity = med.quantity or 0
            med_type = (med.type or "").strip().lower()
            threshold = 50 if med_type in ("tablet", "capsule") else 30

            expiry_date = med.expiry_date
            days_left = "N/A"
            alert_messages = []

            if quantity < threshold:
                alert_messages.append(f"Low stock (threshold < {threshold})")

            if expiry_date:
                delta_days = (expiry_date - today).days
                days_left = str(delta_days)

                if delta_days < 0:
                    alert_messages.append("Expired")
                elif delta_days <= 90:
                    alert_messages.append(f"Expiring soon ({delta_days} day(s) left)")
            else:
                alert_messages.append("No expiry date")

            if alert_messages:
                self.alerts_tree.insert(
                    "",
                    "end",
                    values=(
                        med.name,
                        med.type,
                        quantity,
                        expiry_date if expiry_date else "-",
                        days_left,
                        " | ".join(alert_messages)
                    )
                )
