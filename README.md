# 🚖 Ride-Sharing & Carpooling System (DBMS Mini Project)

## 📌 Project Title

**Ride-Sharing & Carpooling Management System using MySQL and Streamlit**

---

## 🧾 Project Overview

This project is a database-driven Ride-Sharing and Carpooling system designed to manage users, bookings, trips, vehicles, and payments efficiently. It supports three user roles: Admin, Driver, and Passenger. The system enables real-time booking, intelligent trip formation for carpooling, automated fare calculation, and payment tracking.

A Streamlit-based GUI is used for ease of interaction, while MySQL serves as the backend database supporting procedures, triggers, functions, joins, and aggregate queries as required by DBMS lab specifications.

---

## 🎯 Objectives

* To implement a real-world carpooling system using relational database concepts
* To demonstrate usage of triggers, stored procedures, and SQL functions
* To provide role-based access and secure data handling
* To satisfy DBMS mini-project rubric requirements

---

## 🛠️ Technologies Used

| Component            | Technology             |
| -------------------- | ---------------------- |
| Frontend             | Streamlit (Python GUI) |
| Backend              | MySQL Database         |
| Programming Language | Python 3               |
| Database Connector   | mysql-connector-python |
| Data Handling        | Pandas                 |

---

## 📂 Folder Structure

```
ride-sharing-carpooling-system/
│
├── schema.sql
├── procedures_triggers.sql
├── requirements.txt
├── ER_diagram.jpg
├── Relational_schema.jpg
├── schema.sql
├── README.md
├── ride-sharing-streamlit/
│   ├── streamlit_app.py
│   ├── .streamlit/config.toml
│   └── assets/banner.png
```

---

## ⚙️ Features

### 🔐 Authentication System

* Secure login for Admin, Driver, and Passenger
* Role-based dashboard display

### 🚗 Passenger Module

* Create ride booking requests
* View personal booking history
* View total spent using SQL function

### 🧑‍✈️ Driver Module

* View assigned trips
* Mark trip as completed
* View total earnings

### 🛠 Admin Module

* Dynamically create trips from booking requests (carpool logic)
* Assign drivers and vehicles automatically
* View all users and bookings
* Run reports & analytics

---

## 💾 Database Functionalities Implemented

### ✅ Triggers

* Auto-calculate total fare when trip is created
* Update payment status when trip is marked completed

### ✅ Stored Procedures

* AssignDriver
* FormTripFromBookings

### ✅ SQL Functions

* GetPassengerTotalSpent(user_id)
* GetTotalEarnings(driver_id)
* GetTripRevenue(trip_id)

### ✅ Views

* TopTrips

### ✅ Queries

* Nested Queries
* Join Queries
* Aggregate Queries

---

## ▶️ How to Run the Project

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Setup Database

Run in MySQL:

```sql
source schema.sql;
source procedures_triggers.sql;
```

### Step 3: Run the Application

```bash
streamlit run streamlit_app.py
```

---

## 📑 SQL Features Demonstration

```sql
CALL FormTripFromBookings('Whitefield','Challagatta',20,3);
SELECT GetPassengerTotalSpent(5);
SELECT GetTotalEarnings(2);
SELECT GetTripRevenue(1);
SELECT * FROM TopTrips;
```

---

## 📌 Future Enhancements

* Online payment gateway integration
* Ride tracking and live location updates
* Rating system for drivers
* Mobile app version

---

## 👨‍🏫 Academic Compliance

This project fulfills all DBMS Mini Project requirements including:

* ER Diagram & Relational Schema
* Triggers, Functions, Stored Procedures
* CRUD operations via GUI
* SQL query types (nested, join, aggregate)
* Frontend integration

---

✅ Developed for DBMS Mini Project Evaluation at PES University
