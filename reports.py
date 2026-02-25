import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, timedelta, datetime

class ReportsMixin:

    def build_reports_tab(self):
        frame = ttk.Frame(self.reports_tab, padding=30)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Select Report Type").pack(pady=5)
        self.report_type = ttk.Combobox(frame, values=["Weekly", "Monthly", "Yearly", "Custom"], width=20)
        self.report_type.pack()
        self.report_type.set("Weekly")
        self.report_type.bind("<<ComboboxSelected>>", self.on_report_type_change)

        # Custom dates frame (hidden initially)
        self.custom_frame = ttk.Frame(frame)
        ttk.Label(self.custom_frame, text="From (YYYY-MM-DD)").grid(row=0, column=0, pady=2)
        self.from_entry = ttk.Entry(self.custom_frame)
        self.from_entry.grid(row=0, column=1, pady=2)
        ttk.Label(self.custom_frame, text="To (YYYY-MM-DD)").grid(row=1, column=0, pady=2)
        self.to_entry = ttk.Entry(self.custom_frame)
        self.to_entry.grid(row=1, column=1, pady=2)

        self.generate_btn = ttk.Button(frame, text="Generate Report", command=self.generate_selected_report)
        self.generate_btn.pack(pady=10)

        self.report_box = tk.Text(frame, height=20)
        self.report_box.pack(fill="both", expand=True)

    def on_report_type_change(self, event):
        if self.report_type.get() == "Custom":
            self.custom_frame.pack(pady=5)
        else:
            self.custom_frame.pack_forget()

    def generate_selected_report(self):
        rtype = self.report_type.get()
        if rtype == "Weekly":
            self.generate_period_report(7)
        elif rtype == "Monthly":
            self.generate_period_report(30)
        elif rtype == "Yearly":
            self.generate_period_report(365)
        elif rtype == "Custom":
            self.custom_report()

    def generate_period_report(self, days):
        end = date.today()
        start = end - timedelta(days=days)
        self.generate_report(start, end)

    def custom_report(self):
        try:
            start = datetime.strptime(self.from_entry.get(), "%Y-%m-%d").date()
            end = datetime.strptime(self.to_entry.get(), "%Y-%m-%d").date()
            self.generate_report(start, end)
        except:
            messagebox.showerror("Error", "Invalid date format.")

    def generate_report(self, start, end):
        # Total amount and transaction count
        self.cursor.execute(
            "SELECT COALESCE(SUM(total_amount),0), COUNT(id) FROM sales WHERE sale_date BETWEEN %s AND %s",
            (start, end)
        )
        total, count = self.cursor.fetchone()

        # Medicine sales
        self.cursor.execute("""
            SELECT m.name, COALESCE(SUM(si.quantity),0), COALESCE(SUM(si.subtotal),0)
            FROM medicines m
            JOIN sale_items si ON m.id = si.medicine_id
            JOIN sales s ON s.id = si.sale_id
            WHERE s.sale_date BETWEEN %s AND %s
            GROUP BY m.id, m.name
            ORDER BY SUM(si.quantity) DESC, m.name ASC
        """, (start, end))
        medicine_sales = self.cursor.fetchall()

        # Quantity per day
        self.cursor.execute("""
            SELECT s.sale_date, COALESCE(SUM(si.quantity),0)
            FROM sales s
            JOIN sale_items si ON s.id = si.sale_id
            WHERE s.sale_date BETWEEN %s AND %s
            GROUP BY s.sale_date
            ORDER BY s.sale_date ASC
        """, (start, end))
        quantity_per_day = self.cursor.fetchall()

        # Inventory left
        self.cursor.execute("SELECT name, quantity FROM medicines ORDER BY name ASC")
        inventory_left = self.cursor.fetchall()

        if medicine_sales:
            top_name, top_qty, top_amount = medicine_sales[0]
            top_line = f"Most Sold Drug: {top_name} (Qty: {int(top_qty)}, Amount: {float(top_amount):.2f})"
        else:
            top_line = "Most Sold Drug: No sales in selected period"

        sold_lines = "\n".join(
            f"- {name}: Qty Sold={int(qty)}, Amount={float(amount):.2f}" for name, qty, amount in medicine_sales
        ) or "- No medicine sales in selected period"

        qty_time_lines = "\n".join(
            f"- {sale_day}: Qty Sold={int(qty)}" for sale_day, qty in quantity_per_day
        ) or "- No quantity movement in selected period"

        inventory_lines = "\n".join(
            f"- {name}: Left={qty if qty is not None else 0}" for name, qty in inventory_left
        ) or "- No medicines in inventory"

        report = f"""
SALES REPORT
From: {start}
To: {end}

Transactions: {count}
Total Amount: {float(total):.2f}

{top_line}

Quantity Sold Per Medicine (Selected Period):
{sold_lines}

Quantity Sold Per Day (Selected Period):
{qty_time_lines}

Inventory Left (Current):
{inventory_lines}
"""
        self.report_box.delete("1.0", tk.END)
        self.report_box.insert(tk.END, report)