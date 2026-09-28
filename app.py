import sqlite3
from pathlib import Path
from datetime import datetime, date, timedelta

import pandas as pd
import streamlit as st


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="Hotel Management",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_FILE = Path("hotel.db")
HOTEL_IMAGE = Path("hotel.jpg")


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background-color: #f5f7fb;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    section[data-testid="stSidebar"] {
        background-color: #111827;
    }

    section[data-testid="stSidebar"] * {
        color: white;
    }

    .hotel-title {
        font-size: 32px;
        font-weight: 700;
        color: #111827;
    }

    .hotel-subtitle {
        color: #667085;
        margin-bottom: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def execute(sql, params=()):
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()


def query_df(sql, params=()):
    conn = get_connection()

    try:
        return pd.read_sql_query(
            sql,
            conn,
            params=params
        )

    finally:
        conn.close()


def execute_many(sql, data):
    conn = get_connection()

    try:
        cursor = conn.cursor()
        cursor.executemany(sql, data)
        conn.commit()

    finally:
        conn.close()


def column_exists(table, column):

    conn = get_connection()

    try:

        rows = conn.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()

        return any(
            row["name"] == column
            for row in rows
        )

    finally:
        conn.close()


def add_column_if_missing(
    table,
    column,
    definition
):

    if not column_exists(
        table,
        column
    ):

        execute(
            f"""
            ALTER TABLE {table}
            ADD COLUMN {column} {definition}
            """
        )


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_database():

    conn = get_connection()
    cursor = conn.cursor()

    # --------------------------------------------------------
    # ROOMS
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT UNIQUE NOT NULL,
            room_type TEXT NOT NULL,
            floor INTEGER NOT NULL DEFAULT 1,
            price REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Trống'
        )
        """
    )

    # --------------------------------------------------------
    # GUESTS
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            gender TEXT,
            date_of_birth TEXT,
            phone TEXT,
            email TEXT,
            id_number TEXT,
            nationality TEXT,
            address TEXT,
            company TEXT,
            note TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    # --------------------------------------------------------
    # BOOKINGS
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            guest_id INTEGER NOT NULL,
            check_in TEXT NOT NULL,
            check_out TEXT,
            adults INTEGER DEFAULT 1,
            children INTEGER DEFAULT 0,
            price_per_night REAL NOT NULL DEFAULT 0,
            total_amount REAL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Đang ở',
            note TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    # --------------------------------------------------------
    # PAYMENTS
    # --------------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT DEFAULT 'Tiền mặt',
            paid_at TEXT NOT NULL,
            note TEXT
        )
        """
    )

    conn.commit()
    conn.close()

    # ========================================================
    # DATABASE MIGRATION
    # ========================================================

    guest_columns = {
        "gender": "TEXT",
        "date_of_birth": "TEXT",
        "phone": "TEXT",
        "email": "TEXT",
        "id_number": "TEXT",
        "nationality": "TEXT",
        "address": "TEXT",
        "company": "TEXT",
        "note": "TEXT",
        "created_at": "TEXT",
    }

    for column, definition in guest_columns.items():

        add_column_if_missing(
            "guests",
            column,
            definition
        )

    booking_columns = {
        "adults": "INTEGER DEFAULT 1",
        "children": "INTEGER DEFAULT 0",
        "price_per_night": "REAL DEFAULT 0",
        "total_amount": "REAL DEFAULT 0",
        "status": "TEXT DEFAULT 'Đang ở'",
        "note": "TEXT",
        "created_at": "TEXT",
    }

    for column, definition in booking_columns.items():

        add_column_if_missing(
            "bookings",
            column,
            definition
        )

    # ========================================================
    # SAMPLE ROOMS
    # ========================================================

    count_df = query_df(
        """
        SELECT COUNT(*) AS total
        FROM rooms
        """
    )

    room_count = int(
        count_df.iloc[0]["total"]
    )

    if room_count == 0:

        rooms = [

            # Tầng 1
            ("101", "Standard", 1, 500000),
            ("102", "Standard", 1, 500000),
            ("103", "Standard", 1, 550000),
            ("104", "Standard", 1, 550000),

            # Tầng 2
            ("201", "Deluxe", 2, 800000),
            ("202", "Deluxe", 2, 800000),
            ("203", "Deluxe", 2, 850000),
            ("204", "Deluxe", 2, 850000),

            # Tầng 3
            ("301", "Suite", 3, 1200000),
            ("302", "Suite", 3, 1500000),
            ("303", "Family", 3, 1300000),
            ("304", "VIP", 3, 2000000),
        ]

        execute_many(
            """
            INSERT INTO rooms
            (
                room_number,
                room_type,
                floor,
                price,
                status
            )
            VALUES (?, ?, ?, ?, 'Trống')
            """,
            rooms
        )


# ============================================================
# HELPERS
# ============================================================

def now_string():

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def money(value):

    try:

        return (
            f"{float(value):,.0f} ₫"
        )

    except Exception:

        return "0 ₫"


def calculate_nights(
    check_in,
    check_out
):

    days = (
        check_out - check_in
    ).days

    return max(days, 1)


def update_room_status(
    room_id,
    status
):

    execute(
        """
        UPDATE rooms
        SET status = ?
        WHERE id = ?
        """,
        (
            status,
            room_id
        )
    )


def get_room_id(room_number):

    df = query_df(
        """
        SELECT id
        FROM rooms
        WHERE room_number = ?
        """,
        (room_number,)
    )

    if df.empty:

        return None

    return int(
        df.iloc[0]["id"]
    )


# ============================================================
# HOTEL IMAGE
# ============================================================

def show_hotel_image():

    if HOTEL_IMAGE.exists():

        st.image(
            str(HOTEL_IMAGE),
            use_container_width=True
        )

    else:

        st.image(
            "https://images.unsplash.com/"
            "photo-1566073771259-6a8506099945"
            "?auto=format&fit=crop&w=1800&q=85",
            use_container_width=True
        )


# ============================================================
# SIDEBAR
# ============================================================

def sidebar():

    st.sidebar.title(
        "🏨 HOTEL MANAGER"
    )

    st.sidebar.caption(
        "Hotel Management System"
    )

    st.sidebar.divider()

    menu = st.sidebar.radio(
        "MENU",
        [
            "📊 Tổng quan",
            "🛏️ Quản lý phòng",
            "📋 Check-in / Check-out",
            "👥 Khách hàng",
            "💰 Thanh toán",
            "📈 Báo cáo doanh thu",
        ]
    )

    st.sidebar.divider()

    st.sidebar.subheader(
        "Trạng thái phòng"
    )

    st.sidebar.write(
        "🟢 Trống"
    )

    st.sidebar.write(
        "🔴 Đang ở"
    )

    st.sidebar.write(
        "🧹 Đang dọn"
    )

    st.sidebar.write(
        "🔧 Bảo trì"
    )

    st.sidebar.divider()

    st.sidebar.caption(
        "Database: hotel.db"
    )

    return menu


# ============================================================
# DASHBOARD
# ============================================================

def dashboard():

    st.title(
        "🏨 Tổng quan khách sạn"
    )

    st.caption(
        "Theo dõi phòng, khách lưu trú và doanh thu"
    )

    # --------------------------------------------------------
    # HOTEL IMAGE
    # --------------------------------------------------------

    show_hotel_image()

    st.markdown(
        "### Paradise Hotel"
    )

    st.write(
        "Hệ thống quản lý phòng, khách hàng, "
        "check-in, check-out và doanh thu."
    )

    # --------------------------------------------------------
    # ROOM DATA
    # --------------------------------------------------------

    rooms = query_df(
        """
        SELECT *
        FROM rooms
        ORDER BY floor, room_number
        """
    )

    total_rooms = len(rooms)

    empty_rooms = len(
        rooms[
            rooms["status"] == "Trống"
        ]
    )

    occupied_rooms = len(
        rooms[
            rooms["status"] == "Đang ở"
        ]
    )

    cleaning_rooms = len(
        rooms[
            rooms["status"] == "Đang dọn"
        ]
    )

    maintenance_rooms = len(
        rooms[
            rooms["status"] == "Bảo trì"
        ]
    )

    # --------------------------------------------------------
    # REVENUE
    # --------------------------------------------------------

    revenue = query_df(
        """
        SELECT
            COALESCE(
                SUM(amount),
                0
            ) AS total
        FROM payments
        """
    )

    total_revenue = float(
        revenue.iloc[0]["total"]
    )

    today_revenue_df = query_df(
        """
        SELECT
            COALESCE(
                SUM(amount),
                0
            ) AS total
        FROM payments
        WHERE DATE(paid_at)
            = DATE('now', 'localtime')
        """
    )

    today_revenue = float(
        today_revenue_df.iloc[0]["total"]
    )

    # --------------------------------------------------------
    # KPI ROW 1
    # --------------------------------------------------------

    st.subheader(
        "📊 Tình trạng phòng"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "🏨 Tổng số phòng",
            total_rooms
        )

    with c2:

        st.metric(
            "🟢 Phòng trống",
            empty_rooms
        )

    with c3:

        st.metric(
            "🔴 Phòng đang ở",
            occupied_rooms
        )

    # --------------------------------------------------------
    # KPI ROW 2
    # --------------------------------------------------------

    c4, c5, c6 = st.columns(3)

    with c4:

        st.metric(
            "🧹 Phòng đang dọn",
            cleaning_rooms
        )

    with c5:

        st.metric(
            "🔧 Phòng bảo trì",
            maintenance_rooms
        )

    with c6:

        st.metric(
            "💰 Tổng doanh thu",
            money(total_revenue)
        )

    # --------------------------------------------------------
    # REVENUE
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "💵 Doanh thu"
    )

    r1, r2 = st.columns(2)

    with r1:

        st.metric(
            "💰 Tổng doanh thu",
            money(total_revenue)
        )

    with r2:

        st.metric(
            "📅 Doanh thu hôm nay",
            money(today_revenue)
        )

    # --------------------------------------------------------
    # OCCUPANCY
    # --------------------------------------------------------

    if total_rooms > 0:

        occupancy = (
            occupied_rooms
            / total_rooms
            * 100
        )

        st.write(
            f"📈 Công suất phòng: "
            f"**{occupancy:.1f}%**"
        )

        st.progress(
            min(
                occupancy / 100,
                1
            )
        )

    # --------------------------------------------------------
    # ROOM MAP
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "🛏️ Sơ đồ phòng"
    )

    if rooms.empty:

        st.info(
            "Chưa có phòng."
        )

    else:

        floors = sorted(
            rooms["floor"]
            .unique()
        )

        for floor in floors:

            st.markdown(
                f"### 🏢 Tầng {int(floor)}"
            )

            floor_rooms = rooms[
                rooms["floor"] == floor
            ]

            cols = st.columns(4)

            for col, (_, room) in zip(
                cols,
                floor_rooms.iterrows()
            ):

                with col:

                    status = room["status"]

                    if status == "Trống":

                        icon = "🟢"

                    elif status == "Đang ở":

                        icon = "🔴"

                    elif status == "Đang dọn":

                        icon = "🧹"

                    elif status == "Bảo trì":

                        icon = "🔧"

                    else:

                        icon = "⚪"

                    with st.container(
                        border=True
                    ):

                        st.subheader(
                            f"{icon} "
                            f"{room['room_number']}"
                        )

                        st.caption(
                            f"{room['room_type']} "
                            f"• Tầng {room['floor']}"
                        )

                        st.write(
                            f"**{status}**"
                        )

                        st.write(
                            f"{money(room['price'])}"
                            "/đêm"
                        )

    # --------------------------------------------------------
    # CURRENT GUESTS
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "👥 Khách đang lưu trú"
    )

    current = query_df(
        """
        SELECT
            b.id,
            r.room_number,
            r.room_type,
            g.full_name,
            g.phone,
            g.id_number,
            b.check_in,
            b.check_out,
            b.adults,
            b.children,
            b.total_amount
        FROM bookings b
        JOIN rooms r
            ON b.room_id = r.id
        JOIN guests g
            ON b.guest_id = g.id
        WHERE b.status = 'Đang ở'
        ORDER BY b.id DESC
        """
    )

    if current.empty:

        st.info(
            "Hiện chưa có khách đang ở."
        )

    else:

        display = current.copy()

        display["total_amount"] = (
            display["total_amount"]
            .apply(money)
        )

        display.columns = [
            "Booking",
            "Phòng",
            "Loại phòng",
            "Khách hàng",
            "Điện thoại",
            "CCCD/Passport",
            "Check-in",
            "Check-out",
            "Người lớn",
            "Trẻ em",
            "Tổng tiền",
        ]

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# ROOM MANAGEMENT
# ============================================================

def room_management():

    st.title(
        "🛏️ Quản lý phòng"
    )

    st.caption(
        "Theo dõi và cập nhật trạng thái phòng"
    )

    rooms = query_df(
        """
        SELECT *
        FROM rooms
        ORDER BY floor, room_number
        """
    )

    # --------------------------------------------------------
    # FILTER
    # --------------------------------------------------------

    c1, c2, c3 = st.columns(3)

    with c1:

        floor_options = ["Tất cả"]

        if not rooms.empty:

            floor_options += [
                str(int(x))
                for x in sorted(
                    rooms["floor"]
                    .dropna()
                    .unique()
                )
            ]

        selected_floor = st.selectbox(
            "🏢 Tầng",
            floor_options
        )

    with c2:

        selected_status = st.selectbox(
            "📌 Trạng thái",
            [
                "Tất cả",
                "Trống",
                "Đang ở",
                "Đang dọn",
                "Bảo trì",
            ]
        )

    with c3:

        search_room = st.text_input(
            "🔎 Tìm phòng",
            placeholder="Ví dụ: 101"
        )

    filtered = rooms.copy()

    if selected_floor != "Tất cả":

        filtered = filtered[
            filtered["floor"]
            == int(selected_floor)
        ]

    if selected_status != "Tất cả":

        filtered = filtered[
            filtered["status"]
            == selected_status
        ]

    if search_room:

        filtered = filtered[
            filtered["room_number"]
            .astype(str)
            .str.contains(
                search_room,
                case=False,
                na=False
            )
        ]

    st.write(
        f"Tìm thấy **{len(filtered)}** phòng"
    )

    # --------------------------------------------------------
    # ROOMS
    # --------------------------------------------------------

    floors = sorted(
        filtered["floor"].unique()
    )

    for floor in floors:

        st.subheader(
            f"🏢 Tầng {int(floor)}"
        )

        floor_rooms = filtered[
            filtered["floor"] == floor
        ]

        cols = st.columns(4)

        for col, (_, room) in zip(
            cols,
            floor_rooms.iterrows()
        ):

            with col:

                status = room["status"]

                if status == "Trống":
                    icon = "🟢"
                elif status == "Đang ở":
                    icon = "🔴"
                elif status == "Đang dọn":
                    icon = "🧹"
                elif status == "Bảo trì":
                    icon = "🔧"
                else:
                    icon = "⚪"

                with st.container(
                    border=True
                ):

                    st.subheader(
                        f"{icon} "
                        f"{room['room_number']}"
                    )

                    st.caption(
                        f"{room['room_type']} "
                        f"• Tầng {room['floor']}"
                    )

                    st.write(
                        f"Trạng thái: "
                        f"**{status}**"
                    )

                    st.write(
                        f"Giá: "
                        f"**{money(room['price'])}/đêm**"
                    )

                    status_list = [
                        "Trống",
                        "Đang ở",
                        "Đang dọn",
                        "Bảo trì",
                    ]

                    current_index = (
                        status_list.index(status)
                        if status in status_list
                        else 0
                    )

                    new_status = st.selectbox(
                        "Trạng thái mới",
                        status_list,
                        index=current_index,
                        key=f"status_{room['id']}"
                    )

                    if new_status != status:

                        update_room_status(
                            int(room["id"]),
                            new_status
                        )

                        st.success(
                            "Đã cập nhật phòng."
                        )

                        st.rerun()

    # --------------------------------------------------------
    # ADD ROOM
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "➕ Thêm phòng mới"
    )

    with st.form(
        "add_room_form",
        clear_on_submit=True
    ):

        c1, c2, c3, c4 = st.columns(4)

        with c1:

            room_number = st.text_input(
                "Số phòng *"
            )

        with c2:

            room_type = st.selectbox(
                "Loại phòng",
                [
                    "Standard",
                    "Deluxe",
                    "Suite",
                    "Family",
                    "VIP",
                ]
            )

        with c3:

            floor = st.number_input(
                "Tầng",
                min_value=1,
                max_value=100,
                value=1
            )

        with c4:

            price = st.number_input(
                "Giá / đêm",
                min_value=0.0,
                value=500000.0,
                step=50000.0
            )

        submit = st.form_submit_button(
            "💾 Thêm phòng",
            type="primary",
            use_container_width=True
        )

        if submit:

            if not room_number.strip():

                st.error(
                    "Vui lòng nhập số phòng."
                )

            elif price <= 0:

                st.error(
                    "Giá phòng phải lớn hơn 0."
                )

            else:

                try:

                    execute(
                        """
                        INSERT INTO rooms
                        (
                            room_number,
                            room_type,
                            floor,
                            price,
                            status
                        )
                        VALUES (?, ?, ?, ?, 'Trống')
                        """,
                        (
                            room_number.strip(),
                            room_type,
                            floor,
                            price
                        )
                    )

                    st.success(
                        "Đã thêm phòng."
                    )

                    st.rerun()

                except sqlite3.IntegrityError:

                    st.error(
                        "Số phòng đã tồn tại."
                    )


# ============================================================
# CHECK-IN / CHECK-OUT
# ============================================================

def booking_management():

    st.title(
        "📋 Check-in / Check-out"
    )

    st.caption(
        "Quản lý khách đến và khách trả phòng"
    )

    tab1, tab2 = st.tabs(
        [
            "🏨 Check-in",
            "📋 Danh sách booking",
        ]
    )

    # ========================================================
    # CHECK-IN
    # ========================================================

    with tab1:

        available_rooms = query_df(
            """
            SELECT *
            FROM rooms
            WHERE status = 'Trống'
            ORDER BY room_number
            """
        )

        if available_rooms.empty:

            st.warning(
                "Không có phòng trống."
            )

        else:

            room_options = {}

            for _, room in available_rooms.iterrows():

                label = (
                    f"Phòng {room['room_number']} | "
                    f"{room['room_type']} | "
                    f"{money(room['price'])}/đêm"
                )

                room_options[label] = room

            with st.form(
                "checkin_form"
            ):

                st.subheader(
                    "🛏️ Chọn phòng"
                )

                room_label = st.selectbox(
                    "Phòng *",
                    list(
                        room_options.keys()
                    )
                )

                selected_room = (
                    room_options[
                        room_label
                    ]
                )

                st.subheader(
                    "👤 Thông tin khách"
                )

                c1, c2, c3 = st.columns(3)

                with c1:

                    full_name = st.text_input(
                        "Họ và tên *"
                    )

                    gender = st.selectbox(
                        "Giới tính",
                        [
                            "Nam",
                            "Nữ",
                            "Khác"
                        ]
                    )

                    dob = st.date_input(
                        "Ngày sinh",
                        value=date(
                            1990,
                            1,
                            1
                        )
                    )

                with c2:

                    phone = st.text_input(
                        "Số điện thoại *"
                    )

                    email = st.text_input(
                        "Email"
                    )

                    id_number = st.text_input(
                        "CCCD / Passport *"
                    )

                with c3:

                    nationality = st.text_input(
                        "Quốc tịch",
                        value="Việt Nam"
                    )

                    company = st.text_input(
                        "Công ty"
                    )

                    address = st.text_input(
                        "Địa chỉ"
                    )

                guest_note = st.text_area(
                    "Ghi chú khách hàng"
                )

                st.subheader(
                    "📅 Thông tin lưu trú"
                )

                c1, c2, c3, c4 = st.columns(4)

                with c1:

                    check_in = st.date_input(
                        "Ngày check-in",
                        value=date.today()
                    )

                with c2:

                    check_out = st.date_input(
                        "Ngày check-out",
                        value=(
                            date.today()
                            + timedelta(days=1)
                        )
                    )

                with c3:

                    adults = st.number_input(
                        "Người lớn",
                        min_value=1,
                        max_value=20,
                        value=1
                    )

                with c4:

                    children = st.number_input(
                        "Trẻ em",
                        min_value=0,
                        max_value=20,
                        value=0
                    )

                note = st.text_area(
                    "Ghi chú booking"
                )

                nights = calculate_nights(
                    check_in,
                    check_out
                )

                estimated_total = (
                    nights
                    * float(
                        selected_room["price"]
                    )
                )

                st.info(
                    f"{nights} đêm × "
                    f"{money(selected_room['price'])}"
                    f" = "
                    f"**{money(estimated_total)}**"
                )

                submit = st.form_submit_button(
                    "🏨 XÁC NHẬN CHECK-IN",
                    type="primary",
                    use_container_width=True
                )

                if submit:

                    if not full_name.strip():

                        st.error(
                            "Vui lòng nhập họ tên."
                        )

                    elif not phone.strip():

                        st.error(
                            "Vui lòng nhập số điện thoại."
                        )

                    elif not id_number.strip():

                        st.error(
                            "Vui lòng nhập CCCD/Passport."
                        )

                    elif check_out <= check_in:

                        st.error(
                            "Ngày check-out phải "
                            "sau ngày check-in."
                        )

                    else:

                        # -----------------------------
                        # GUEST
                        # -----------------------------

                        guest_id = execute(
                            """
                            INSERT INTO guests
                            (
                                full_name,
                                gender,
                                date_of_birth,
                                phone,
                                email,
                                id_number,
                                nationality,
                                address,
                                company,
                                note,
                                created_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                full_name.strip(),
                                gender,
                                str(dob),
                                phone.strip(),
                                email.strip(),
                                id_number.strip(),
                                nationality.strip(),
                                address.strip(),
                                company.strip(),
                                guest_note.strip(),
                                now_string()
                            )
                        )

                        # -----------------------------
                        # BOOKING
                        # -----------------------------

                        booking_id = execute(
                            """
                            INSERT INTO bookings
                            (
                                room_id,
                                guest_id,
                                check_in,
                                check_out,
                                adults,
                                children,
                                price_per_night,
                                total_amount,
                                status,
                                note,
                                created_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                int(
                                    selected_room["id"]
                                ),
                                guest_id,
                                str(check_in),
                                str(check_out),
                                adults,
                                children,
                                float(
                                    selected_room["price"]
                                ),
                                estimated_total,
                                "Đang ở",
                                note.strip(),
                                now_string()
                            )
                        )

                        # -----------------------------
                        # ROOM
                        # -----------------------------

                        update_room_status(
                            int(
                                selected_room["id"]
                            ),
                            "Đang ở"
                        )

                        st.success(
                            f"Check-in thành công! "
                            f"Booking #{booking_id}"
                        )

    # ========================================================
    # BOOKING LIST
    # ========================================================

    with tab2:

        bookings = query_df(
            """
            SELECT
                b.id,
                r.room_number,
                g.full_name,
                g.phone,
                g.id_number,
                b.check_in,
                b.check_out,
                b.adults,
                b.children,
                b.price_per_night,
                b.total_amount,
                b.status,
                b.note
            FROM bookings b
            JOIN rooms r
                ON b.room_id = r.id
            JOIN guests g
                ON b.guest_id = g.id
            ORDER BY b.id DESC
            """
        )

        if bookings.empty:

            st.info(
                "Chưa có booking."
            )

        else:

            status_filter = st.selectbox(
                "Trạng thái",
                [
                    "Tất cả",
                    "Đang ở",
                    "Đã trả phòng",
                    "Đã hủy"
                ]
            )

            filtered = bookings.copy()

            if status_filter != "Tất cả":

                filtered = filtered[
                    filtered["status"]
                    == status_filter
                ]

            display = filtered.copy()

            display["price_per_night"] = (
                display["price_per_night"]
                .apply(money)
            )

            display["total_amount"] = (
                display["total_amount"]
                .apply(money)
            )

            display.columns = [
                "Booking",
                "Phòng",
                "Khách",
                "Điện thoại",
                "CCCD",
                "Check-in",
                "Check-out",
                "NL",
                "TE",
                "Giá/đêm",
                "Tổng tiền",
                "Trạng thái",
                "Ghi chú"
            ]

            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True
            )

            # ------------------------------------------------
            # CHECK OUT
            # ------------------------------------------------

            active = filtered[
                filtered["status"]
                == "Đang ở"
            ]

            if not active.empty:

                st.divider()

                st.subheader(
                    "🚪 Check-out"
                )

                booking_options = {}

                for _, row in active.iterrows():

                    label = (
                        f"#{row['id']} | "
                        f"Phòng {row['room_number']} | "
                        f"{row['full_name']}"
                    )

                    booking_options[label] = row

                selected_label = st.selectbox(
                    "Chọn khách",
                    list(
                        booking_options.keys()
                    )
                )

                booking = booking_options[
                    selected_label
                ]

                st.info(
                    f"Khách: **{booking['full_name']}**\n\n"
                    f"Phòng: **{booking['room_number']}**\n\n"
                    f"Tổng tiền: "
                    f"**{money(booking['total_amount'])}**"
                )

                if st.button(
                    "🚪 XÁC NHẬN CHECK-OUT",
                    type="primary",
                    use_container_width=True
                ):

                    execute(
                        """
                        UPDATE bookings
                        SET
                            status = 'Đã trả phòng',
                            check_out = ?
                        WHERE id = ?
                        """,
                        (
                            str(date.today()),
                            int(
                                booking["id"]
                            )
                        )
                    )

                    room_id = get_room_id(
                        booking["room_number"]
                    )

                    if room_id:

                        update_room_status(
                            room_id,
                            "Đang dọn"
                        )

                    st.success(
                        "Đã check-out."
                    )

                    st.rerun()


# ============================================================
# GUEST MANAGEMENT
# ============================================================

def guest_management():

    st.title(
        "👥 Khách hàng"
    )

    st.caption(
        "Hồ sơ và lịch sử lưu trú của khách"
    )

    guests = query_df(
        """
        SELECT
            g.*,
            COUNT(b.id) AS booking_count
        FROM guests g
        LEFT JOIN bookings b
            ON g.id = b.guest_id
        GROUP BY g.id
        ORDER BY g.id DESC
        """
    )

    # --------------------------------------------------------
    # KPI
    # --------------------------------------------------------

    total_guests = len(guests)

    current_df = query_df(
        """
        SELECT
            COUNT(
                DISTINCT guest_id
            ) AS total
        FROM bookings
        WHERE status = 'Đang ở'
        """
    )

    current_guests = int(
        current_df.iloc[0]["total"]
    )

    total_bookings = (
        int(
            guests["booking_count"].sum()
        )
        if not guests.empty
        else 0
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "👥 Tổng khách",
            total_guests
        )

    with c2:

        st.metric(
            "🏨 Đang lưu trú",
            current_guests
        )

    with c3:

        st.metric(
            "📋 Tổng booking",
            total_bookings
        )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    search = st.text_input(
        "🔎 Tìm khách",
        placeholder=(
            "Tên / điện thoại / CCCD / email"
        )
    )

    filtered = guests.copy()

    if search:

        mask = (
            filtered["full_name"]
            .astype(str)
            .str.contains(
                search,
                case=False,
                na=False
            )
            |
            filtered["phone"]
            .astype(str)
            .str.contains(
                search,
                case=False,
                na=False
            )
            |
            filtered["id_number"]
            .astype(str)
            .str.contains(
                search,
                case=False,
                na=False
            )
            |
            filtered["email"]
            .astype(str)
            .str.contains(
                search,
                case=False,
                na=False
            )
        )

        filtered = filtered[mask]

    # --------------------------------------------------------
    # TABLE
    # --------------------------------------------------------

    st.subheader(
        "📋 Danh sách khách"
    )

    if filtered.empty:

        st.info(
            "Không tìm thấy khách."
        )

    else:

        display = filtered[
            [
                "id",
                "full_name",
                "gender",
                "date_of_birth",
                "phone",
                "email",
                "id_number",
                "nationality",
                "address",
                "company",
                "booking_count"
            ]
        ].copy()

        display.columns = [
            "ID",
            "Họ tên",
            "Giới tính",
            "Ngày sinh",
            "Điện thoại",
            "Email",
            "CCCD/Passport",
            "Quốc tịch",
            "Địa chỉ",
            "Công ty",
            "Số booking"
        ]

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True
        )

    # --------------------------------------------------------
    # DETAIL
    # --------------------------------------------------------

    if not filtered.empty:

        st.divider()

        selected_id = st.selectbox(
            "👤 Chọn khách hàng",
            filtered["id"].tolist(),
            format_func=lambda x:
                filtered[
                    filtered["id"] == x
                ]["full_name"].iloc[0]
        )

        guest = filtered[
            filtered["id"] == selected_id
        ].iloc[0]

        st.subheader(
            f"👤 {guest['full_name']}"
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            st.write(
                f"**Giới tính:** "
                f"{guest['gender']}"
            )

            st.write(
                f"**Ngày sinh:** "
                f"{guest['date_of_birth']}"
            )

            st.write(
                f"**Quốc tịch:** "
                f"{guest['nationality']}"
            )

        with c2:

            st.write(
                f"**Điện thoại:** "
                f"{guest['phone']}"
            )

            st.write(
                f"**Email:** "
                f"{guest['email']}"
            )

            st.write(
                f"**CCCD/Passport:** "
                f"{guest['id_number']}"
            )

        with c3:

            st.write(
                f"**Địa chỉ:** "
                f"{guest['address']}"
            )

            st.write(
                f"**Công ty:** "
                f"{guest['company']}"
            )

            st.write(
                f"**Ghi chú:** "
                f"{guest['note']}"
            )

        # ----------------------------------------------------
        # EDIT
        # ----------------------------------------------------

        with st.expander(
            "✏️ Chỉnh sửa thông tin"
        ):

            with st.form(
                "edit_guest"
            ):

                c1, c2 = st.columns(2)

                with c1:

                    name = st.text_input(
                        "Họ tên",
                        value=str(
                            guest["full_name"]
                        )
                    )

                    phone = st.text_input(
                        "Điện thoại",
                        value=str(
                            guest["phone"] or ""
                        )
                    )

                    email = st.text_input(
                        "Email",
                        value=str(
                            guest["email"] or ""
                        )
                    )

                    id_number = st.text_input(
                        "CCCD / Passport",
                        value=str(
                            guest["id_number"] or ""
                        )
                    )

                with c2:

                    nationality = st.text_input(
                        "Quốc tịch",
                        value=str(
                            guest["nationality"]
                            or ""
                        )
                    )

                    address = st.text_input(
                        "Địa chỉ",
                        value=str(
                            guest["address"]
                            or ""
                        )
                    )

                    company = st.text_input(
                        "Công ty",
                        value=str(
                            guest["company"]
                            or ""
                        )
                    )

                    note = st.text_area(
                        "Ghi chú",
                        value=str(
                            guest["note"]
                            or ""
                        )
                    )

                save = st.form_submit_button(
                    "💾 Lưu",
                    type="primary",
                    use_container_width=True
                )

                if save:

                    execute(
                        """
                        UPDATE guests
                        SET
                            full_name = ?,
                            phone = ?,
                            email = ?,
                            id_number = ?,
                            nationality = ?,
                            address = ?,
                            company = ?,
                            note = ?
                        WHERE id = ?
                        """,
                        (
                            name.strip(),
                            phone.strip(),
                            email.strip(),
                            id_number.strip(),
                            nationality.strip(),
                            address.strip(),
                            company.strip(),
                            note.strip(),
                            int(selected_id)
                        )
                    )

                    st.success(
                        "Đã cập nhật."
                    )

                    st.rerun()

        # ----------------------------------------------------
        # HISTORY
        # ----------------------------------------------------

        st.subheader(
            "📜 Lịch sử lưu trú"
        )

        history = query_df(
            """
            SELECT
                b.id,
                r.room_number,
                b.check_in,
                b.check_out,
                b.adults,
                b.children,
                b.price_per_night,
                b.total_amount,
                b.status,
                b.note
            FROM bookings b
            JOIN rooms r
                ON b.room_id = r.id
            WHERE b.guest_id = ?
            ORDER BY b.id DESC
            """,
            (int(selected_id),)
        )

        if history.empty:

            st.info(
                "Chưa có lịch sử."
            )

        else:

            display = history.copy()

            display["price_per_night"] = (
                display["price_per_night"]
                .apply(money)
            )

            display["total_amount"] = (
                display["total_amount"]
                .apply(money)
            )

            display.columns = [
                "Booking",
                "Phòng",
                "Check-in",
                "Check-out",
                "Người lớn",
                "Trẻ em",
                "Giá/đêm",
                "Tổng tiền",
                "Trạng thái",
                "Ghi chú"
            ]

            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# PAYMENT
# ============================================================

def payment_management():

    st.title(
        "💰 Thanh toán"
    )

    st.caption(
        "Theo dõi tiền đã thu và công nợ"
    )

    bookings = query_df(
        """
        SELECT
            b.id,
            r.room_number,
            g.full_name,
            b.total_amount,
            COALESCE(
                SUM(p.amount),
                0
            ) AS paid
        FROM bookings b
        JOIN rooms r
            ON b.room_id = r.id
        JOIN guests g
            ON b.guest_id = g.id
        LEFT JOIN payments p
            ON b.id = p.booking_id
        GROUP BY b.id
        ORDER BY b.id DESC
        """
    )

    if bookings.empty:

        st.info(
            "Chưa có booking."
        )

        return

    total_booking = float(
        bookings["total_amount"].sum()
    )

    total_paid = float(
        bookings["paid"].sum()
    )

    debt = max(
        total_booking
        - total_paid,
        0
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "💰 Tổng booking",
            money(total_booking)
        )

    with c2:

        st.metric(
            "💵 Đã thu",
            money(total_paid)
        )

    with c3:

        st.metric(
            "⚠️ Công nợ",
            money(debt)
        )

    st.divider()

    # --------------------------------------------------------
    # SELECT BOOKING
    # --------------------------------------------------------

    options = {}

    for _, row in bookings.iterrows():

        remaining = max(
            float(row["total_amount"])
            - float(row["paid"]),
            0
        )

        label = (
            f"#{row['id']} | "
            f"Phòng {row['room_number']} | "
            f"{row['full_name']} | "
            f"Còn {money(remaining)}"
        )

        options[label] = row

    selected = st.selectbox(
        "Chọn booking",
        list(options.keys())
    )

    booking = options[selected]

    remaining = max(
        float(booking["total_amount"])
        - float(booking["paid"]),
        0
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Tổng tiền",
            money(
                booking["total_amount"]
            )
        )

    with c2:

        st.metric(
            "Đã trả",
            money(
                booking["paid"]
            )
        )

    with c3:

        st.metric(
            "Còn lại",
            money(remaining)
        )

    # --------------------------------------------------------
    # PAYMENT
    # --------------------------------------------------------

    if remaining > 0:

        with st.form(
            "payment_form"
        ):

            amount = st.number_input(
                "Số tiền",
                min_value=0.0,
                max_value=float(remaining),
                value=float(remaining),
                step=50000.0
            )

            method = st.selectbox(
                "Phương thức",
                [
                    "Tiền mặt",
                    "Chuyển khoản",
                    "Thẻ",
                    "Ví điện tử"
                ]
            )

            note = st.text_input(
                "Ghi chú"
            )

            submit = st.form_submit_button(
                "💵 XÁC NHẬN THANH TOÁN",
                type="primary",
                use_container_width=True
            )

            if submit:

                if amount <= 0:

                    st.error(
                        "Số tiền không hợp lệ."
                    )

                else:

                    execute(
                        """
                        INSERT INTO payments
                        (
                            booking_id,
                            amount,
                            payment_method,
                            paid_at,
                            note
                        )
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            int(
                                booking["id"]
                            ),
                            amount,
                            method,
                            now_string(),
                            note.strip()
                        )
                    )

                    st.success(
                        f"Đã thu "
                        f"{money(amount)}"
                    )

                    st.rerun()

    else:

        st.success(
            "Booking đã thanh toán đủ."
        )

    # --------------------------------------------------------
    # PAYMENT HISTORY
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "📋 Lịch sử thanh toán"
    )

    payments = query_df(
        """
        SELECT
            p.id,
            p.booking_id,
            r.room_number,
            g.full_name,
            p.amount,
            p.payment_method,
            p.paid_at,
            p.note
        FROM payments p
        JOIN bookings b
            ON p.booking_id = b.id
        JOIN rooms r
            ON b.room_id = r.id
        JOIN guests g
            ON b.guest_id = g.id
        ORDER BY p.id DESC
        """
    )

    if payments.empty:

        st.info(
            "Chưa có giao dịch."
        )

    else:

        display = payments.copy()

        display["amount"] = (
            display["amount"]
            .apply(money)
        )

        display.columns = [
            "ID",
            "Booking",
            "Phòng",
            "Khách",
            "Số tiền",
            "Phương thức",
            "Thời gian",
            "Ghi chú"
        ]

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True
        )

        csv = payments.to_csv(
            index=False
        ).encode(
            "utf-8-sig"
        )

        st.download_button(
            "📥 Xuất CSV",
            data=csv,
            file_name="thanh_toan.csv",
            mime="text/csv"
        )


# ============================================================
# REVENUE REPORT
# ============================================================

def revenue_report():

    st.title(
        "📈 Báo cáo doanh thu"
    )

    st.caption(
        "Theo dõi doanh thu khách sạn"
    )

    total_df = query_df(
        """
        SELECT
            COALESCE(
                SUM(amount),
                0
            ) AS total
        FROM payments
        """
    )

    total_revenue = float(
        total_df.iloc[0]["total"]
    )

    today_df = query_df(
        """
        SELECT
            COALESCE(
                SUM(amount),
                0
            ) AS total
        FROM payments
        WHERE DATE(paid_at)
            = DATE('now', 'localtime')
        """
    )

    today_revenue = float(
        today_df.iloc[0]["total"]
    )

    payment_count_df = query_df(
        """
        SELECT
            COUNT(*) AS total
        FROM payments
        """
    )

    payment_count = int(
        payment_count_df.iloc[0]["total"]
    )

    average_payment = (
        total_revenue
        / payment_count
        if payment_count > 0
        else 0
    )

    # --------------------------------------------------------
    # KPI
    # --------------------------------------------------------

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "💰 Tổng doanh thu",
            money(total_revenue)
        )

    with c2:

        st.metric(
            "📅 Hôm nay",
            money(today_revenue)
        )

    with c3:

        st.metric(
            "📊 TB giao dịch",
            money(average_payment)
        )

    st.divider()

    # --------------------------------------------------------
    # DAILY
    # --------------------------------------------------------

    st.subheader(
        "📊 Doanh thu theo ngày"
    )

    daily = query_df(
        """
        SELECT
            DATE(paid_at)
                AS payment_date,
            SUM(amount)
                AS revenue
        FROM payments
        GROUP BY DATE(paid_at)
        ORDER BY payment_date
        """
    )

    if daily.empty:

        st.info(
            "Chưa có dữ liệu."
        )

    else:

        daily["payment_date"] = (
            pd.to_datetime(
                daily["payment_date"]
            )
        )

        chart = daily.set_index(
            "payment_date"
        )

        st.line_chart(
            chart["revenue"],
            height=350
        )

        display = daily.copy()

        display["revenue"] = (
            display["revenue"]
            .apply(money)
        )

        display.columns = [
            "Ngày",
            "Doanh thu"
        ]

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True
        )

    # --------------------------------------------------------
    # PAYMENT METHOD
    # --------------------------------------------------------

    st.subheader(
        "💳 Doanh thu theo phương thức"
    )

    methods = query_df(
        """
        SELECT
            payment_method,
            SUM(amount) AS revenue
        FROM payments
        GROUP BY payment_method
        ORDER BY revenue DESC
        """
    )

    if methods.empty:

        st.info(
            "Chưa có dữ liệu."
        )

    else:

        display = methods.copy()

        display["revenue"] = (
            display["revenue"]
            .apply(money)
        )

        display.columns = [
            "Phương thức",
            "Doanh thu"
        ]

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True
        )

    # --------------------------------------------------------
    # EXPORT
    # --------------------------------------------------------

    if not daily.empty:

        csv = daily.to_csv(
            index=False
        ).encode(
            "utf-8-sig"
        )

        st.download_button(
            "📥 Xuất báo cáo CSV",
            data=csv,
            file_name="bao_cao_doanh_thu.csv",
            mime="text/csv"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    init_database()

    menu = sidebar()

    if menu == "📊 Tổng quan":

        dashboard()

    elif menu == "🛏️ Quản lý phòng":

        room_management()

    elif menu == "📋 Check-in / Check-out":

        booking_management()

    elif menu == "👥 Khách hàng":

        guest_management()

    elif menu == "💰 Thanh toán":

        payment_management()

    elif menu == "📈 Báo cáo doanh thu":

        revenue_report()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()

