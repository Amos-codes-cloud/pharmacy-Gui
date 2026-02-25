from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from connector import Base

# ---------------- USER ----------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # "manager" or "staff"

# ---------------- MEDICINE ----------------
class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False, default="Tablet")  # e.g., Tablet, Capsule, Syrup
    expiry_date = Column(Date)
    price = Column(Float)
    quantity = Column(Integer)

    sale_items = relationship("SaleItem", back_populates="medicine")
    stock_entries = relationship("StockEntry", back_populates="medicine")

# ---------------- PATIENT ----------------
class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    medical_history = Column(String)

    sales = relationship("Sale", back_populates="patient")

# ---------------- SALE ----------------
class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True)
    sale_date = Column(Date)
    total_amount = Column(Float)
    patient_id = Column(Integer, ForeignKey("patients.id"))

    patient = relationship("Patient", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale")

# ---------------- SALE ITEM ----------------
class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    medicine_id = Column(Integer, ForeignKey("medicines.id"))
    quantity = Column(Integer)
    subtotal = Column(Float)
    prescription = Column(String)

    sale = relationship("Sale", back_populates="items")
    medicine = relationship("Medicine", back_populates="sale_items")

# ---------------- STOCK ENTRY ----------------
class StockEntry(Base):
    __tablename__ = "stock_entries"

    id = Column(Integer, primary_key=True)
    medicine_id = Column(Integer, ForeignKey("medicines.id"))
    quantity_added = Column(Integer)
    entry_date = Column(Date)

    medicine = relationship("Medicine", back_populates="stock_entries")