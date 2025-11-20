#python -m streamlit run streamlit_app.py


import streamlit as st
import mysql.connector
import pandas as pd

# ---------------- DB ----------------
def get_conn():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="ride_sharing",
        autocommit=False,
        charset="utf8mb4",
        collation="utf8mb4_general_ci",
    )

def run_query(query, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params or ())
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description] if cur.description else []
    conn.close()
    return pd.DataFrame(rows, columns=cols)

def run_exec(query, params=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params or ())
    conn.commit()
    conn.close()

def call_proc(name, args=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.callproc(name, args)
    conn.commit()
    conn.close()

# ---------------- Session ----------------
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "role" not in st.session_state:
    st.session_state.role = None
if "name" not in st.session_state:
    st.session_state.name = None

# ---------------- Auth ----------------
def do_login(email, password, role):
    df = run_query(
        "SELECT UserID, Name, Role FROM Users WHERE Email=%s AND PasswordHash=%s",
        (email, password)
    )
    if len(df) == 1 and df.iloc[0]["Role"] == role:
        st.session_state.user_id = int(df.iloc[0]["UserID"])
        st.session_state.role = df.iloc[0]["Role"]
        st.session_state.name = df.iloc[0]["Name"]
        return True
    return False

def do_logout():
    st.session_state.user_id = None
    st.session_state.role = None
    st.session_state.name = None
    st.rerun()


def register_user(name, email, phone, password, role):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Users (Name, Email, Phone, PasswordHash, Role) VALUES (%s,%s,%s,%s,%s)",
            (name, email, phone, password, role)
        )
        user_id = cur.lastrowid
        conn.commit()
        return user_id, None
    except mysql.connector.Error as e:
        conn.rollback()
        return None, str(e)
    finally:
        conn.close()

def create_driver_and_vehicle(user_id, license_no, experience, plate, model, capacity):
    # separate connection ensures clean transaction for driver+vehicle
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Drivers (UserID, LicenseNo, ExperienceYears) VALUES (%s,%s,%s)",
            (user_id, license_no, int(experience or 0))
        )
        driver_id = cur.lastrowid
        cur.execute(
            "INSERT INTO Vehicles (DriverID, PlateNo, Model, Capacity) VALUES (%s,%s,%s,%s)",
            (driver_id, plate, model, int(capacity or 4))
        )
        conn.commit()
        return None
    except mysql.connector.Error as e:
        conn.rollback()
        return str(e)
    finally:
        conn.close()

# ---------------- UI Blocks ----------------
def ui_login():
    st.header("Ride-Sharing System — Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ["admin", "driver", "passenger"], index=2)
    if st.button("Login"):
        if do_login(email, password, role):
            st.success(f"Welcome, {st.session_state.name} ({role})")
            st.rerun()

        else:
            st.error("Invalid credentials or role mismatch")

    with st.expander("Create a new account"):
        with st.form("register_form", clear_on_submit=False):
            r_name = st.text_input("Full Name")
            r_email = st.text_input("Email*")
            r_phone = st.text_input("Phone*")
            r_pwd = st.text_input("Password*", type="password")
            r_role = st.selectbox("Account Type", ["passenger", "driver"])
            st.caption("Fields marked * are required.")
            # Driver extras
            if r_role == "driver":
                st.subheader("🧑‍✈️ Driver Details")
                r_license = st.text_input("License No*")
                r_exp = st.number_input("Experience (years)", min_value=0, step=1, value=0)
                st.subheader("🚖 Vehicle Details")
                r_plate = st.text_input("Plate No*")
                r_model = st.text_input("Model")
                r_capacity = st.number_input("Capacity", min_value=1, step=1, value=4)
            submitted = st.form_submit_button("Register")
            if submitted:
                # Basic validation
                if not (r_name and r_email and r_phone and r_pwd):
                    st.error("Please fill all required user details.")
                    st.stop()

                if r_role == "driver":
                    # Validate driver-specific fields BEFORE inserting any data
                    if not (r_license and r_plate):
                        st.error("Please enter License Number and Vehicle Plate Number for driver registration.")
                        st.stop()

                # Proceed to insert user
                user_id, err = register_user(r_name, r_email, r_phone, r_pwd, r_role)
                if err:
                    st.error(f"User creation failed: {err}")
                    st.stop()

                # If driver, also insert driver & vehicle
                if r_role == "driver":
                    derr = create_driver_and_vehicle(
                        user_id, r_license, r_exp, r_plate, r_model, r_capacity
                    )
                    if derr:
                        st.error(f"Driver + Vehicle creation failed: {derr}")
                        st.stop()
                    st.success("✅ Driver + Vehicle registered successfully! You can login now.")
                else:
                    st.success("✅ Passenger account created successfully! You can login now.")

                # Reset form by rerunning
                st.rerun()


def ui_profile():
    st.subheader("👤 My Profile")
    df = run_query(
        "SELECT UserID, Name, Email, Phone, Role, CreatedAt FROM Users WHERE UserID=%s",
        (st.session_state.user_id,)
    )
    st.dataframe(df, hide_index=True)
    st.button("Logout", on_click=do_logout)

# -------- Passenger --------
def ui_passenger():
    st.subheader("🧍 Passenger — Book Ride")
    with st.form("book_form"):
        src = st.text_input("Source")
        dst = st.text_input("Destination")
        dist = st.number_input("Distance (km)", min_value=0.1, step=0.1, format="%.2f")
        submitted = st.form_submit_button("Create Booking")
        if submitted:
            if not (src and dst and dist):
                st.error("Please fill all fields.")
            else:
                try:
                    run_exec(
                        "INSERT INTO Bookings (UserID, Source, Destination, Distance) VALUES (%s,%s,%s,%s)",
                        (st.session_state.user_id, src.strip(), dst.strip(), float(dist))
                    )
                    st.success("Booking created. It will be grouped into a Trip when admin forms a carpool.")
                except mysql.connector.Error as e:
                    st.error(f"DB Error: {e}")

    st.markdown("---")
    st.subheader("My Bookings")
    dfb = run_query(
        "SELECT BookingID, Source, Destination, Distance, Status, TripID, RequestedAt "
        "FROM Bookings WHERE UserID=%s ORDER BY RequestedAt DESC",
        (st.session_state.user_id,)
    )
    st.dataframe(dfb, hide_index=True, width='stretch')

    if st.button("Show My Total Spending (completed trips)"):
        df = run_query("SELECT GetPassengerTotalSpent(%s)", (st.session_state.user_id,))
        total = df.iloc[0, 0] if not df.empty else 0
        st.info(f"Total Amount Spent: ₹{float(total):.2f}")

# -------- Driver --------
def ui_driver():
    # resolve DriverID
    dfd = run_query("SELECT DriverID FROM Drivers WHERE UserID=%s", (st.session_state.user_id,))
    if dfd.empty:
        st.warning("Driver profile not found. Ask admin to link driver details.")
        return
    driver_id = int(dfd.iloc[0]["DriverID"])

    st.subheader("Driver — My Trips")
    dft = run_query(
        "SELECT TripID, Source, Destination, Distance, SeatsFilled, Status, CreatedAt "
        "FROM Trips WHERE DriverID=%s ORDER BY CreatedAt DESC",
        (driver_id,)
    )
    st.dataframe(dft, hide_index=True, width='stretch')

    # select a trip to complete
    open_trips = dft[dft["Status"].isin(["Open", "Ongoing"])]
    if not open_trips.empty:
        trip_choice = st.selectbox(
            "Select a Trip to mark Completed",
            open_trips["TripID"].tolist()
        )
        if st.button("Mark Trip Completed"):
            try:
                run_exec("UPDATE Trips SET Status='Completed' WHERE TripID=%s", (int(trip_choice),))
                st.success("Trip marked completed. Payments converted to Success by trigger.")
                st.rerun()

            except mysql.connector.Error as e:
                st.error(f"DB Error: {e}")
    else:
        st.info("No open/ongoing trips right now.")

    if st.button("Show My Total Earnings (completed trips)"):
        df = run_query("SELECT GetTotalEarnings(%s)", (driver_id,))
        total = df.iloc[0, 0] if not df.empty else 0
        st.info(f"Total Earnings: ₹{float(total):.2f}")

# -------- Admin --------
def ui_admin():
    tabs = st.tabs(["Trips & Bookings", "Manage Users", "Reports"])
    # --- Trips & Bookings ---
    with tabs[0]:
        st.subheader("Form Trip From Bookings (Carpool)")
        with st.form("form_trip"):
            s = st.text_input("Source")
            d = st.text_input("Destination")
            distance = st.number_input("Distance (km)", min_value=0.1, step=0.1, format="%.2f")
            capacity = st.number_input("Capacity (#passengers)", min_value=1, step=1)
            submitted = st.form_submit_button("Form Trip")
            if submitted:
                try:
                    call_proc("FormTripFromBookings", (s.strip(), d.strip(), float(distance), int(capacity)))
                    st.success("Trip formed from matching requested bookings (case-insensitive).")
                except mysql.connector.Error as e:
                    st.error(f"DB Error: {e}")

        st.markdown("### Trips")
        dft = run_query(
            """SELECT T.TripID, U.UserID AS DriverUserID, T.VehicleID, T.Source, T.Destination,
                      T.Distance, T.TotalFare, T.SeatsFilled, T.Status, T.CreatedAt
               FROM Trips T
               LEFT JOIN Drivers Dr ON T.DriverID = Dr.DriverID
               LEFT JOIN Users U ON Dr.UserID = U.UserID
               ORDER BY T.CreatedAt DESC"""
        )
        st.dataframe(dft, hide_index=True, width='stretch')

        st.markdown("### All Bookings")
        dfb = run_query(
            """SELECT B.BookingID, U.Name, B.Source, B.Destination, B.Distance, B.Status, IFNULL(B.TripID,'-') AS TripID, B.RequestedAt
               FROM Bookings B JOIN Users U ON B.UserID = U.UserID
               ORDER BY B.RequestedAt DESC"""
        )
        st.dataframe(dfb, hide_index=True, width='stretch')
        
        st.subheader("Trips with Multiple Passengers (Nested Query)")
        df_nested = run_query("""
            SELECT * FROM Trips 
            WHERE TripID IN (
                SELECT TripID FROM Bookings GROUP BY TripID HAVING COUNT(*) > 1
            )
        """)
        st.dataframe(df_nested, hide_index=True, width='stretch')

        # Delete row controls
        st.caption("Delete a booking (will cascade payments if any).")
        bid_to_delete = st.selectbox("BookingID to delete", dfb["BookingID"].tolist() if not dfb.empty else [])
        if st.button("Delete Selected Booking"):
            try:
                run_exec("DELETE FROM Bookings WHERE BookingID=%s", (int(bid_to_delete),))
                st.success(f"Booking #{bid_to_delete} deleted.")
                st.rerun()
            except mysql.connector.Error as e:
                st.error(f"DB Error: {e}")

    # --- Manage Users ---
    with tabs[1]:
        st.subheader("🧍Users")
        dfu = run_query("SELECT UserID, Name, Email, Phone, Role, CreatedAt FROM Users ORDER BY UserID")
        st.dataframe(dfu, hide_index=True, width='stretch')

        uid_to_delete = st.selectbox("UserID to delete (CASCADE will remove driver/vehicle/bookings/payments)", dfu["UserID"].tolist() if not dfu.empty else [])
        if st.button("Delete Selected User"):
            try:
                run_exec("DELETE FROM Users WHERE UserID=%s", (int(uid_to_delete),))
                st.success(f"User #{uid_to_delete} deleted.")
                st.rerun()

            except mysql.connector.Error as e:
                st.error(f"DB Error: {e}")

    # --- Reports ---
    with tabs[2]:
        st.subheader("Top Trips (by seats filled)")
        dfr = run_query("SELECT * FROM TopTrips")
        st.dataframe(dfr, hide_index=True, width='stretch')

        st.subheader("Trip Revenue Summary")
        trip_id = st.number_input("Enter Trip ID", min_value=1, step=1)
        if st.button("Show Trip Revenue"):
            df = run_query("SELECT GetTripRevenue(%s)", (int(trip_id),))
            total = df.iloc[0, 0] if not df.empty else 0
            st.info(f"Total Revenue for Trip #{trip_id}: ₹{float(total):.2f}")


# ---------------- Main ----------------
st.set_page_config(page_title="Ride-Sharing", layout="wide")
# ------------- Custom CSS -------------
st.markdown("""
    <style>
    /* Global background */
    .stApp {
        background: linear-gradient(135deg, #E3F2FD, #FFFFFF);
        font-family: 'Segoe UI', sans-serif;
    }

    /* Center title */
    .stMarkdown h1, h2, h3 {
        color: #003366;
        text-align: center;
    }

    /* Buttons */
    div.stButton > button {
        background-color: #FF6F00;
        color: white;
        border-radius: 8px;
        height: 2.8em;
        width: 100%;
        font-weight: bold;
        border: none;
    }
    div.stButton > button:hover {
        background-color: #FF8F00;
    }

    /* Input boxes */
    input, select, textarea {
        border-radius: 6px !important;
        border: 1px solid #ccc !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #003366;
    }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] p {
        color: white !important;
    }

    /* Table styling */
    .stDataFrame {
        border-radius: 10px;
        background-color: white;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    </style>
""", unsafe_allow_html=True)


st.sidebar.title("🚖 Ride-Sharing System")
if st.session_state.user_id:
    st.sidebar.success(f"👤 Logged in as {st.session_state.name} ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        do_logout()
else:
    st.sidebar.info("Not logged in")

st.title("Ride-Sharing & Carpooling")
st.image("assets/banner.png", use_container_width=True, caption="Smart Ride-Sharing & Carpooling System 🚗")

if st.session_state.user_id is None:
    ui_login()
else:
    ui_profile()
    st.markdown("---")
    role = st.session_state.role
    if role == "passenger":
        ui_passenger()
    elif role == "driver":
        ui_driver()
    elif role == "admin":
        ui_admin()
