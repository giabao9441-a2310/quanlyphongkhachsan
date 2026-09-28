import sqlite3
from pathlib import Path
from datetime import datetime, date, timedelta

import pandas as pd
import streamlit as st


# ============================================================
# CẤU HÌNH
# ============================================================

st.set_page_config(
    page_title="Hotel Management System",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = Path("hotel.db")


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

    /* ===== GLOBAL ===== */

    .stApp {
        background: #f5f7fb;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }

    /* ===== SIDEBAR ===== */

    section[data-testid="stSidebar"] {
        background: #111827;
    }

    section[data-testid="stSidebar"] * {
        color: white !important;
    }

    /* ===== HEADER ===== */

    .main-title {
        font-size: 34px;
        font-weight: 800;
        color: #111827;
        margin-bottom: 0;
    }

    .subtitle {
        color: #6b7280;
        font-size: 15px;
        margin-top: 3px;
        margin-bottom: 20px;
    }

    /* ===== HERO ===== */

    .hero {
        height: 260px;
        border-radius: 20px;
        overflow: hidden;
        background-image:
            linear-gradient(
                90deg,
                rgba(15, 23, 42, 0.88),
                rgba(15, 23, 42, 0.35)
            ),
            url("https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1800&q=85");
        background-size: cover;
        background-position: center;
        display: flex;
        align-items: center;
        padding: 40px;
        margin-bottom: 25px;
        box-shadow: 0 8px 25px rgba(0,0,0,.12);
    }

    .hero-content {
        color: white;
        max-width: 650px;
    }

    .hero-title {
        font-size: 38px;
        font-weight: 800;
        margin-bottom: 10px;
    }

    .hero-text {
        font-size: 16px;
        opacity: .92;
    }

    /* ===== KPI ===== */

    .kpi {
        background: white;
        border-radius: 16px;
        padding: 20px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 15px rgba(0,0,0,.04);
        min-height: 125px;
    }

    .kpi-title {
        color: #6b7280;
        font-size: 14px;
        margin-bottom: 10px;
    }

    .kpi-value {
        font-size: 27px;
        font-weight: 800;
        color: #111827;
    }

    .kpi-icon {
        font-size: 25px;
        float: right;
    }

    /* ===== ROOM CARD ===== */

    .room-card {
        background: white;
        border-radius: 14px;
        padding: 17px;
        border: 1px solid #e5e7eb;
        margin-bottom: 10px;
        box-shadow: 0 3px 10px rgba(0,0,0,.03);
    }

    .room-number {
        font-size: 22px;
        font-weight: 800;
        color: #111827;
    }

    .room-type {
        color: #6b7280;
        font-size: 13px;
    }

    .status {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
    }

    .status-empty {
        color: #027a48;
        background: #ecfdf3;
    }

    .status-occupied {
        color: #b42318;
        background: #fef3f2;
    }

    .status-cleaning {
        color: #b54708;
        background: #fffaeb;
    }

    .status-maintenance {
        color: #6941c6;
        background: #f4f3ff;
    }

    /* ===== SECTION ===== */

    .section-title {
        font-size: 21px;
        font-weight: 750;
        color: #111827;
        margin-top: 25px;
        margin-bottom: 15px;
    }

    /* ===== BUTTON ===== */

    .stButton > button {
        border-radius: 9px;
        font-weight: 600;
    }

</style>
""", unsafe_allow_html=True)


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def execute(sql, params=()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    result = cur.lastrowid
    conn.close()
    return result


def query_df(sql, params=()):
    conn = get_connection()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


def init_database():

    conn = get_connection()
    cur = conn.cursor()

    # ---------------- ROOMS ----------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT UNIQUE NOT NULL,
            room_type TEXT NOT NULL,
            floor INTEGER NOT NULL,
            price REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Trống'
        )
    """)

    # ---------------- GUESTS ----------------

    cur.execute("""
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
    """)

    # ---------------- BOOKINGS ----------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            room_id INTEGER NOT NULL,
            guest_id INTEGER NOT NULL,

            check_in TEXT NOT NULL,
            check_out TEXT,

            adults INTEGER DEFAULT 1,
            children INTEGER DEFAULT 0,

            price_per_night REAL NOT NULL,
            total_amount REAL DEFAULT 0,

            status TEXT NOT NULL DEFAULT 'Đang ở',

            note TEXT,

            created_at TEXT NOT NULL,

            FOREIGN KEY(room_id) REFERENCES rooms(id),
            FOREIGN KEY(guest_id) REFERENCES guests(id)
        )
    """)

    # ---------------- PAYMENTS ----------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            booking_id INTEGER NOT NULL,

            amount REAL NOT NULL,

            payment_method TEXT DEFAULT 'Tiền mặt',

            paid_at TEXT NOT NULL,

            note TEXT,

            FOREIGN KEY(booking_id) REFERENCES bookings(id)
        )
    """)

    conn.commit()

    # ========================================================
    # TẠO PHÒNG MẪU
    # ========================================================

    count = cur.execute(
        "SELECT COUNT(*) FROM rooms"
    ).fetchone()[0]

    if count == 0:

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

        cur.executemany("""
            INSERT INTO rooms
            (room_number, room_type, floor, price, status)
            VALUES (?, ?, ?, ?, 'Trống')
        """, rooms)

        conn.commit()

    conn.close()


# ============================================================
# HELPER
# ============================================================

def money(value):
    return f"{float(value):,.0f} ₫"


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def status_class(status):

    mapping = {
        "Trống": "status-empty",
        "Đang ở": "status-occupied",
        "Đang dọn": "status-cleaning",
        "Bảo trì": "status-maintenance"
    }

    return mapping.get(status, "status-empty")


def calculate_nights(check_in, check_out):

    nights = (check_out - check_in).days

    return max(nights, 1)


def update_room_status(room_id, status):

    execute("""
        UPDATE rooms
        SET status = ?
        WHERE id = ?
    """, (status, room_id))


# ============================================================
# SIDEBAR
# ============================================================

def sidebar():

    st.sidebar.markdown(
        """
        <div style="
            text-align:center;
            padding:10px 0 20px 0;
        ">
            <div style="font-size:42px;">🏨</div>
            <div style="
                font-size:20px;
                font-weight:800;
            ">
                HOTEL MANAGER
            </div>
            <div style="
                font-size:12px;
                opacity:.7;
            ">
                Hotel Management System
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.sidebar.divider()

    menu = st.sidebar.radio(
        "QUẢN LÝ",
        [
            "📊 Tổng quan",
            "🛏️ Sơ đồ phòng",
            "📋 Đặt phòng / Check-in",
            "👥 Khách hàng",
            "💰 Thanh toán",
            "📈 Báo cáo doanh thu",
        ]
    )

    st.sidebar.divider()

    st.sidebar.markdown(
        """
        **Trạng thái hệ thống**

        🟢 Phòng trống  
        🔴 Đang ở  
        🟠 Đang dọn  
        🟣 Bảo trì
        """
    )

    return menu


# ============================================================
# DASHBOARD
# ============================================================

def dashboard():

    st.markdown(
        '<div class="main-title">Tổng quan khách sạn</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Theo dõi hoạt động khách sạn theo thời gian thực</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # HERO
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="hero">
            <div class="hero-content">
                <div class="hero-title">
                    🏨 Welcome to Paradise Hotel
                </div>

                <div class="hero-text">
                    Hệ thống quản lý phòng, khách hàng,
                    đặt phòng và doanh thu trong một giao diện.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # DATA
    # --------------------------------------------------------

    rooms = query_df("""
        SELECT * FROM rooms
    """)

    total_rooms = len(rooms)

    empty_rooms = len(
        rooms[rooms["status"] == "Trống"]
    )

    occupied_rooms = len(
        rooms[rooms["status"] == "Đang ở"]
    )

    cleaning_rooms = len(
        rooms[rooms["status"] == "Đang dọn"]
    )

    maintenance_rooms = len(
        rooms[rooms["status"] == "Bảo trì"]
    )

    revenue = query_df("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM payments
    """)

    total_revenue = float(
        revenue.iloc[0]["total"]
    )

    today_revenue = query_df("""
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM payments
        WHERE DATE(paid_at) = DATE('now', 'localtime')
    """)

    today_revenue = float(
        today_revenue.iloc[0]["total"]
    )

    # --------------------------------------------------------
    # KPI
    # --------------------------------------------------------

    cols = st.columns(6)

    kpis = [
        ("🏨", "Tổng số phòng", total_rooms),
        ("🟢", "Phòng trống", empty_rooms),
        ("🔴", "Đang ở", occupied_rooms),
        ("🧹", "Đang dọn", cleaning_rooms),
        ("🔧", "Bảo trì", maintenance_rooms),
        ("💰", "Tổng doanh thu", money(total_revenue)),
    ]

    for col, (icon, title, value) in zip(cols, kpis):

        with col:

            st.markdown(
                f"""
                <div class="kpi">

                    <div class="kpi-icon">
                        {icon}
                    </div>

                    <div class="kpi-title">
                        {title}
                    </div>

                    <div class="kpi-value">
                        {value}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

    # --------------------------------------------------------
    # TODAY REVENUE
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">💰 Doanh thu hôm nay</div>',
        unsafe_allow_html=True
    )

    st.success(
        f"Doanh thu hôm nay: **{money(today_revenue)}**"
    )

    # --------------------------------------------------------
    # ROOM MAP
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">🛏️ Sơ đồ phòng</div>',
        unsafe_allow_html=True
    )

    floors = sorted(
        rooms["floor"].unique()
    )

    for floor in floors:

        st.markdown(
            f"### Tầng {floor}"
        )

        floor_rooms = rooms[
            rooms["floor"] == floor
        ]

        room_cols = st.columns(4)

        for col, (_, room) in zip(
            room_cols,
            floor_rooms.iterrows()
        ):

            with col:

                css_class = status_class(
                    room["status"]
                )

                st.markdown(
                    f"""
                    <div class="room-card">

                        <div class="room-number">
                            {room['room_number']}
                        </div>

                        <div class="room-type">
                            {room['room_type']}
                        </div>

                        <br>

                        <span class="status {css_class}">
                            {room['status']}
                        </span>

                        <br><br>

                        <b>{money(room['price'])}</b>
                        <span class="room-type">
                            / đêm
                        </span>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # --------------------------------------------------------
    # CURRENT GUESTS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">👥 Khách đang lưu trú</div>',
        unsafe_allow_html=True
    )

    current = query_df("""
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
        ORDER BY b.check_in DESC
    """)

    if current.empty:

        st.info(
            "Hiện chưa có khách đang lưu trú."
        )

    else:

        display = current.copy()

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
            "Tổng tiền"
        ]

        display["Tổng tiền"] = (
            display["Tổng tiền"].apply(money)
        )

        st.dataframe(
            display,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# ROOM MAP
# ============================================================

def room_management():

    st.markdown(
        '<div class="main-title">🛏️ Sơ đồ phòng</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Quản lý trạng thái từng phòng</div>',
        unsafe_allow_html=True
    )

    rooms = query_df("""
        SELECT *
        FROM rooms
        ORDER BY floor, room_number
    """)

    # Filter

    col1, col2 = st.columns(2)

    with col1:

        floor_filter = st.selectbox(
            "Tầng",
            ["Tất cả"] +
            [str(x) for x in sorted(
                rooms["floor"].unique()
            )]
        )

    with col2:

        status_filter = st.selectbox(
            "Trạng thái",
            [
                "Tất cả",
                "Trống",
                "Đang ở",
                "Đang dọn",
                "Bảo trì"
            ]
        )

    filtered = rooms.copy()

    if floor_filter != "Tất cả":

        filtered = filtered[
            filtered["floor"] ==
            int(floor_filter)
        ]

    if status_filter != "Tất cả":

        filtered = filtered[
            filtered["status"] ==
            status_filter
        ]

    st.write(
        f"Hiển thị **{len(filtered)}** phòng"
    )

    for floor in sorted(
        filtered["floor"].unique()
    ):

        st.markdown(
            f"### 🏢 Tầng {floor}"
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

                css_class = status_class(
                    room["status"]
                )

                st.markdown(
                    f"""
                    <div class="room-card">

                        <div class="room-number">
                            Phòng {room['room_number']}
                        </div>

                        <div class="room-type">
                            {room['room_type']}
                        </div>

                        <br>

                        <span class="status {css_class}">
                            {room['status']}
                        </span>

                        <br><br>

                        Giá:
                        <b>{money(room['price'])}</b>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

                new_status = st.selectbox(
                    "Trạng thái",
                    [
                        "Trống",
                        "Đang ở",
                        "Đang dọn",
                        "Bảo trì"
                    ],
                    index=[
                        "Trống",
                        "Đang ở",
                        "Đang dọn",
                        "Bảo trì"
                    ].index(room["status"]),
                    key=f"room_status_{room['id']}",
                    label_visibility="collapsed"
                )

                if new_status != room["status"]:

                    update_room_status(
                        room["id"],
                        new_status
                    )

                    st.rerun()

    st.divider()

    # ADD ROOM

    st.subheader("➕ Thêm phòng")

    with st.form("new_room"):

        c1, c2, c3, c4 = st.columns(4)

        with c1:
            room_number = st.text_input(
                "Số phòng"
            )

        with c2:
            room_type = st.selectbox(
                "Loại phòng",
                [
                    "Standard",
                    "Deluxe",
                    "Suite",
                    "Family",
                    "VIP"
                ]
            )

        with c3:
            floor = st.number_input(
                "Tầng",
                min_value=1,
                value=1
            )

        with c4:
            price = st.number_input(
                "Giá / đêm",
                min_value=0,
                value=500000,
                step=50000
            )

        submit = st.form_submit_button(
            "💾 Thêm phòng",
            type="primary"
        )

        if submit:

            if not room_number:

                st.error(
                    "Vui lòng nhập số phòng."
                )

            else:

                try:

                    execute("""
                        INSERT INTO rooms
                        (
                            room_number,
                            room_type,
                            floor,
                            price,
                            status
                        )
                        VALUES (?, ?, ?, ?, 'Trống')
                    """, (
                        room_number,
                        room_type,
                        floor,
                        price
                    ))

                    st.success(
                        "Đã thêm phòng."
                    )

                    st.rerun()

                except sqlite3.IntegrityError:

                    st.error(
                        "Số phòng đã tồn tại."
                    )


# ============================================================
# CHECK-IN
# ============================================================

def booking_management():

    st.markdown(
        '<div class="main-title">📋 Đặt phòng / Check-in</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Tạo booking và quản lý khách đang lưu trú</div>',
        unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs([
        "➕ Check-in khách",
        "📋 Danh sách booking"
    ])

    # ========================================================
    # CHECK IN
    # ========================================================

    with tab1:

        rooms = query_df("""
            SELECT *
            FROM rooms
            WHERE status = 'Trống'
            ORDER BY room_number
        """)

        if rooms.empty:

            st.warning(
                "Không còn phòng trống."
            )

        else:

            room_options = {}

            for _, room in rooms.iterrows():

                label = (
                    f"Phòng {room['room_number']} | "
                    f"{room['room_type']} | "
                    f"{money(room['price'])}/đêm"
                )

                room_options[label] = room

            with st.form("checkin"):

                st.subheader(
                    "Thông tin phòng"
                )

                selected_label = st.selectbox(
                    "Chọn phòng",
                    list(room_options.keys())
                )

                selected_room = room_options[
                    selected_label
                ]

                st.subheader(
                    "👤 Thông tin khách hàng"
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

                    date_of_birth = st.date_input(
                        "Ngày sinh",
                        value=date(
                            1990, 1, 1
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
                        "Công ty / Đơn vị"
                    )

                    address = st.text_input(
                        "Địa chỉ"
                    )

                note_guest = st.text_area(
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
                        value=date.today() +
                        timedelta(days=1)
                    )

                with c3:

                    adults = st.number_input(
                        "Người lớn",
                        min_value=1,
                        value=1
                    )

                with c4:

                    children = st.number_input(
                        "Trẻ em",
                        min_value=0,
                        value=0
                    )

                note_booking = st.text_area(
                    "Ghi chú booking"
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

                    elif check_out < check_in:

                        st.error(
                            "Ngày check-out không hợp lệ."
                        )

                    else:

                        # Guest

                        guest_id = execute("""
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
                        """, (
                            full_name,
                            gender,
                            str(date_of_birth),
                            phone,
                            email,
                            id_number,
                            nationality,
                            address,
                            company,
                            note_guest,
                            now()
                        ))

                        nights = calculate_nights(
                            check_in,
                            check_out
                        )

                        total = (
                            nights *
                            float(selected_room["price"])
                        )

                        booking_id = execute("""
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
                        """, (
                            selected_room["id"],
                            guest_id,
                            str(check_in),
                            str(check_out),
                            adults,
                            children,
                            selected_room["price"],
                            total,
                            "Đang ở",
                            note_booking,
                            now()
                        ))

                        update_room_status(
                            selected_room["id"],
                            "Đang ở"
                        )

                        st.success(
                            f"Check-in thành công! "
                            f"Mã booking: #{booking_id}"
                        )

                        st.info(
                            f"{nights} đêm × "
                            f"{money(selected_room['price'])} "
                            f"= **{money(total)}**"
                        )

    # ========================================================
    # BOOKING LIST
    # ========================================================

    with tab2:

        bookings = query_df("""
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
        """)

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

            display = bookings.copy()

            if status_filter != "Tất cả":

                display = display[
                    display["status"] ==
                    status_filter
                ]

            show = display.copy()

            show["price_per_night"] = (
                show["price_per_night"]
                .apply(money)
            )

            show["total_amount"] = (
                show["total_amount"]
                .apply(money)
            )

            show.columns = [
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
                show,
                use_container_width=True,
                hide_index=True
            )

            # CHECKOUT

            active = display[
                display["status"] ==
                "Đang ở"
            ]

            if not active.empty:

                st.divider()

                st.subheader(
                    "🚪 Check-out"
                )

                options = {}

                for _, row in active.iterrows():

                    label = (
                        f"#{row['id']} | "
                        f"Phòng {row['room_number']} | "
                        f"{row['full_name']}"
                    )

                    options[label] = row

                selected = st.selectbox(
                    "Chọn khách check-out",
                    list(options.keys())
                )

                booking = options[selected]

                st.info(
                    f"Khách **{booking['full_name']}** | "
                    f"Phòng **{booking['room_number']}** | "
                    f"Tổng: **{money(booking['total_amount'])}**"
                )

                if st.button(
                    "🚪 XÁC NHẬN CHECK-OUT",
                    type="primary"
                ):

                    execute("""
                        UPDATE bookings
                        SET
                            status = 'Đã trả phòng',
                            check_out = ?
                        WHERE id = ?
                    """, (
                        str(date.today()),
                        booking["id"]
                    ))

                    update_room_status(
                        int(
                            rooms_id(
                                booking["room_number"]
                            )
                        ),
                        "Đang dọn"
                    )

                    st.success(
                        "Check-out thành công."
                    )

                    st.rerun()


def rooms_id(room_number):

    df = query_df("""
        SELECT id
        FROM rooms
        WHERE room_number = ?
    """, (room_number,))

    return int(df.iloc[0]["id"])


# ============================================================
# CUSTOMER MANAGEMENT
# ============================================================

def guest_management():

    st.markdown(
        '<div class="main-title">👥 Quản lý khách hàng</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Hồ sơ khách hàng và lịch sử lưu trú</div>',
        unsafe_allow_html=True
    )

    guests = query_df("""
        SELECT
            g.*,
            COUNT(b.id) AS booking_count
        FROM guests g
        LEFT JOIN bookings b
            ON g.id = b.guest_id
        GROUP BY g.id
        ORDER BY g.id DESC
    """)

    # ========================================================
    # KPI
    # ========================================================

    total_guests = len(guests)

    current_guests = query_df("""
        SELECT COUNT(DISTINCT guest_id) AS total
        FROM bookings
        WHERE status = 'Đang ở'
    """)

    current_guests = int(
        current_guests.iloc[0]["total"]
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "👥 Tổng khách hàng",
        total_guests
    )

    c2.metric(
        "🏨 Khách đang ở",
        current_guests
    )

    c3.metric(
        "📋 Tổng booking",
        int(guests["booking_count"].sum())
        if not guests.empty else 0
    )

    st.divider()

    # ========================================================
    # SEARCH
    # ========================================================

    search = st.text_input(
        "🔎 Tìm kiếm khách hàng",
        placeholder="Tên, điện thoại, CCCD, email..."
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

    # ========================================================
    # CUSTOMER TABLE
    # ========================================================

    st.subheader("📋 Danh sách khách hàng")

    if filtered.empty:

        st.info(
            "Chưa có khách hàng."
        )

    else:

        show = filtered[
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

        show.columns = [
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
            show,
            use_container_width=True,
            hide_index=True
        )

    # ========================================================
    # DETAIL
    # ========================================================

    if not filtered.empty:

        st.divider()

        guest_id = st.selectbox(
            "Xem hồ sơ khách hàng",
            filtered["id"].tolist(),
            format_func=lambda x:
                filtered.loc[
                    filtered["id"] == x,
                    "full_name"
                ].iloc[0]
        )

        guest = filtered[
            filtered["id"] == guest_id
        ].iloc[0]

        st.subheader(
            f"👤 Hồ sơ: {guest['full_name']}"
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            st.write(
                f"**Họ tên:** {guest['full_name']}"
            )

            st.write(
                f"**Giới tính:** {guest['gender']}"
            )

            st.write(
                f"**Ngày sinh:** {guest['date_of_birth']}"
            )

            st.write(
                f"**Quốc tịch:** {guest['nationality']}"
            )

        with c2:

            st.write(
                f"**Điện thoại:** {guest['phone']}"
            )

            st.write(
                f"**Email:** {guest['email']}"
            )

            st.write(
                f"**CCCD/Passport:** {guest['id_number']}"
            )

        with c3:

            st.write(
                f"**Địa chỉ:** {guest['address']}"
            )

            st.write(
                f"**Công ty:** {guest['company']}"
            )

            st.write(
                f"**Ghi chú:** {guest['note']}"
            )

        # HISTORY

        history = query_df("""
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
        """, (guest_id,))

        st.subheader(
            "📜 Lịch sử lưu trú"
        )

        if history.empty:

            st.info(
                "Chưa có lịch sử lưu trú."
            )

        else:

            show_history = history.copy()

            show_history["price_per_night"] = (
                show_history[
                    "price_per_night"
                ].apply(money)
            )

            show_history["total_amount"] = (
                show_history[
                    "total_amount"
                ].apply(money)
            )

            show_history.columns = [
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
                show_history,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# PAYMENT
# ============================================================

def payment_management():

    st.markdown(
        '<div class="main-title">💰 Thanh toán</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Thu tiền và quản lý công nợ</div>',
        unsafe_allow_html=True
    )

    bookings = query_df("""
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
    """)

    if bookings.empty:

        st.info(
            "Chưa có booking."
        )

        return

    # --------------------------------------------------------
    # TOTAL
    # --------------------------------------------------------

    total_amount = bookings[
        "total_amount"
    ].sum()

    total_paid = bookings[
        "paid"
    ].sum()

    total_debt = max(
        total_amount - total_paid,
        0
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "💰 Tổng tiền booking",
        money(total_amount)
    )

    c2.metric(
        "💵 Đã thu",
        money(total_paid)
    )

    c3.metric(
        "⚠️ Còn phải thu",
        money(total_debt)
    )

    st.divider()

    # --------------------------------------------------------
    # PAYMENT FORM
    # --------------------------------------------------------

    options = {}

    for _, row in bookings.iterrows():

        remaining = max(
            float(row["total_amount"]) -
            float(row["paid"]),
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
        "Chọn booking thu tiền",
        list(options.keys())
    )

    booking = options[selected]

    remaining = max(
        float(booking["total_amount"]) -
        float(booking["paid"]),
        0
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Tổng tiền",
        money(booking["total_amount"])
    )

    c2.metric(
        "Đã trả",
        money(booking["paid"])
    )

    c3.metric(
        "Còn lại",
        money(remaining)
    )

    if remaining > 0:

        with st.form("payment"):

            amount = st.number_input(
                "Số tiền thanh toán",
                min_value=0.0,
                max_value=float(remaining),
                value=float(remaining),
                step=50000.0
            )

            method = st.selectbox(
                "Phương thức thanh toán",
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
                type="primary"
            )

            if submit:

                if amount <= 0:

                    st.error(
                        "Số tiền không hợp lệ."
                    )

                else:

                    execute("""
                        INSERT INTO payments
                        (
                            booking_id,
                            amount,
                            payment_method,
                            paid_at,
                            note
                        )
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        booking["id"],
                        amount,
                        method,
                        now(),
                        note
                    ))

                    st.success(
                        f"Đã thu {money(amount)}."
                    )

                    st.rerun()

    else:

        st.success(
            "Booking này đã thanh toán đủ."
        )

    # --------------------------------------------------------
    # HISTORY
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "📋 Lịch sử giao dịch"
    )

    payments = query_df("""
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
    """)

    if payments.empty:

        st.info(
            "Chưa có giao dịch."
        )

    else:

        show = payments.copy()

        show["amount"] = (
            show["amount"].apply(money)
        )

        show.columns = [
            "ID",
            "Booking",
            "Phòng",
            "Khách hàng",
            "Số tiền",
            "Phương thức",
            "Thời gian",
            "Ghi chú"
        ]

        st.dataframe(
            show,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# REVENUE REPORT
# ============================================================

def revenue_report():

    st.markdown(
        '<div class="main-title">📈 Báo cáo doanh thu</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">Theo dõi doanh thu và hiệu quả kinh doanh</div>',
        unsafe_allow_html=True
    )

    payments = query_df("""
        SELECT
            DATE(paid_at) AS payment_date,
            SUM(amount) AS revenue
        FROM payments
        GROUP BY DATE(paid_at)
        ORDER BY payment_date
    """)

    total_revenue = (
        payments["revenue"].sum()
        if not payments.empty
        else 0
    )

    # --------------------------------------------------------
    # KPI
    # --------------------------------------------------------

    bookings = query_df("""
        SELECT
            COUNT(*) AS total
        FROM bookings
    """)

    total_bookings = int(
        bookings.iloc[0]["total"]
    )

    avg_booking = (
        total_revenue / total_bookings
        if total_bookings > 0
        else 0
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "💰 Tổng doanh thu",
        money(total_revenue)
    )

    c2.metric(
        "📋 Tổng booking",
        total_bookings
    )

    c3.metric(
        "📊 Doanh thu TB / booking",
        money(avg_booking)
    )

    st.divider()

    # --------------------------------------------------------
    # CHART
    # --------------------------------------------------------

    st.subheader(
        "📊 Doanh thu theo ngày"
    )

    if payments.empty:

        st.info(
            "Chưa có dữ liệu doanh thu."
        )

    else:

        chart = payments.copy()

        chart["payment_date"] = pd.to_datetime(
            chart["payment_date"]
        )

        chart = chart.set_index(
            "payment_date"
        )

        st.line_chart(
            chart["revenue"],
            height=350
        )

    # --------------------------------------------------------
    # PAYMENT METHOD
    # --------------------------------------------------------

    st.subheader(
        "💳 Doanh thu theo phương thức thanh toán"
    )

    method_df = query_df("""
        SELECT
            payment_method,
            SUM(amount) AS revenue
        FROM payments
        GROUP BY payment_method
        ORDER BY revenue DESC
    """)

    if not method_df.empty:

        method_display = method_df.copy()

        method_display["revenue"] = (
            method_display["revenue"]
            .apply(money)
        )

        method_display.columns = [
            "Phương thức",
            "Doanh thu"
        ]

        st.dataframe(
            method_display,
            use_container_width=True,
            hide_index=True
        )

    # --------------------------------------------------------
    # EXPORT
    # --------------------------------------------------------

    if not payments.empty:

        csv = payments.to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            "⬇️ Xuất báo cáo doanh thu CSV",
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

    elif menu == "🛏️ Sơ đồ phòng":

        room_management()

    elif menu == "📋 Đặt phòng / Check-in":

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
