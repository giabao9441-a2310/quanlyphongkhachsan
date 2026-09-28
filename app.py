import sqlite3
from datetime import datetime, date
from pathlib import Path

import pandas as pd
import streamlit as st


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Hotel Manager",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_FILE = Path("hotel.db")


# =========================================================
# DATABASE
# =========================================================

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT UNIQUE NOT NULL,
            room_type TEXT NOT NULL,
            floor INTEGER DEFAULT 1,
            price REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Trống'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            id_number TEXT,
            created_at TEXT NOT NULL
        )
    """)

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

    # Tạo dữ liệu phòng mẫu nếu database còn trống
    count = cur.execute("SELECT COUNT(*) FROM rooms").fetchone()[0]

    if count == 0:
        sample_rooms = [
            ("101", "Standard", 1, 500000),
            ("102", "Standard", 1, 500000),
            ("103", "Standard", 1, 550000),
            ("201", "Deluxe", 2, 800000),
            ("202", "Deluxe", 2, 800000),
            ("203", "Deluxe", 2, 850000),
            ("301", "Suite", 3, 1200000),
            ("302", "Suite", 3, 1500000),
        ]

        cur.executemany("""
            INSERT INTO rooms
            (room_number, room_type, floor, price, status)
            VALUES (?, ?, ?, ?, 'Trống')
        """, sample_rooms)

        conn.commit()

    conn.close()


# =========================================================
# HELPERS
# =========================================================

def query_df(sql, params=()):
    conn = get_connection()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


def execute(sql, params=()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id


def money(value):
    return f"{value:,.0f} ₫"


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate_nights(check_in, check_out):
    nights = (check_out - check_in).days
    return max(nights, 1)


def get_room(room_id):
    df = query_df("SELECT * FROM rooms WHERE id = ?", (room_id,))
    return None if df.empty else df.iloc[0]


def update_room_status(room_id, status):
    execute(
        "UPDATE rooms SET status = ? WHERE id = ?",
        (status, room_id)
    )


# =========================================================
# CSS
# =========================================================

def inject_css():
    st.markdown("""
    <style>
        .main {
            background-color: #f7f8fa;
        }

        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }

        .hotel-title {
            font-size: 30px;
            font-weight: 700;
            color: #172033;
            margin-bottom: 5px;
        }

        .hotel-subtitle {
            color: #667085;
            margin-bottom: 25px;
        }

        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 14px;
            border: 1px solid #eaecf0;
            box-shadow: 0 2px 8px rgba(16, 24, 40, 0.04);
        }

        .room-card {
            background: white;
            padding: 18px;
            border-radius: 14px;
            border: 1px solid #eaecf0;
            margin-bottom: 10px;
        }

        .status-empty {
            color: #039855;
            font-weight: 600;
        }

        .status-occupied {
            color: #d92d20;
            font-weight: 600;
        }

        .status-cleaning {
            color: #b54708;
            font-weight: 600;
        }

        .status-maintenance {
            color: #6941c6;
            font-weight: 600;
        }

        div[data-testid="stMetric"] {
            background: white;
            border: 1px solid #eaecf0;
            padding: 15px;
            border-radius: 12px;
        }

        .small-text {
            color: #667085;
            font-size: 13px;
        }
    </style>
    """, unsafe_allow_html=True)


# =========================================================
# SIDEBAR
# =========================================================

def sidebar():
    st.sidebar.markdown("## 🏨 Hotel Manager")
    st.sidebar.caption("Hệ thống quản lý khách sạn")

    st.sidebar.divider()

    menu = st.sidebar.radio(
        "MENU",
        [
            "📊 Tổng quan",
            "🛏️ Quản lý phòng",
            "📋 Đặt phòng",
            "👤 Khách hàng",
            "💰 Thanh toán",
        ]
    )

    st.sidebar.divider()

    st.sidebar.caption("Database")
    st.sidebar.code(str(DB_FILE))

    return menu


# =========================================================
# DASHBOARD
# =========================================================

def dashboard():
    st.markdown('<div class="hotel-title">📊 Tổng quan khách sạn</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hotel-subtitle">Theo dõi tình trạng phòng và hoạt động kinh doanh</div>',
        unsafe_allow_html=True
    )

    rooms = query_df("SELECT * FROM rooms")

    total_rooms = len(rooms)
    empty_rooms = len(rooms[rooms["status"] == "Trống"])
    occupied_rooms = len(rooms[rooms["status"] == "Đang ở"])
    cleaning_rooms = len(rooms[rooms["status"] == "Đang dọn"])
    maintenance_rooms = len(rooms[rooms["status"] == "Bảo trì"])

    revenue_df = query_df("""
        SELECT COALESCE(SUM(amount), 0) AS revenue
        FROM payments
        WHERE date(paid_at) = date('now', 'localtime')
    """)

    today_revenue = float(revenue_df.iloc[0]["revenue"])

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Tổng phòng", total_rooms)
    col2.metric("Phòng trống", empty_rooms)
    col3.metric("Đang ở", occupied_rooms)
    col4.metric("Đang dọn", cleaning_rooms)
    col5.metric("Doanh thu hôm nay", money(today_revenue))

    st.divider()

    left, right = st.columns([2, 1])

    with left:
        st.subheader("🛏️ Tình trạng phòng")

        if rooms.empty:
            st.info("Chưa có phòng.")
        else:
            display_rooms = rooms[
                ["room_number", "room_type", "floor", "price", "status"]
            ].copy()

            display_rooms.columns = [
                "Phòng",
                "Loại phòng",
                "Tầng",
                "Giá/đêm",
                "Trạng thái",
            ]

            display_rooms["Giá/đêm"] = display_rooms["Giá/đêm"].apply(money)

            st.dataframe(
                display_rooms,
                use_container_width=True,
                hide_index=True
            )

    with right:
        st.subheader("📌 Thống kê")

        status_data = pd.DataFrame({
            "Trạng thái": [
                "Trống",
                "Đang ở",
                "Đang dọn",
                "Bảo trì"
            ],
            "Số phòng": [
                empty_rooms,
                occupied_rooms,
                cleaning_rooms,
                maintenance_rooms
            ]
        })

        st.bar_chart(
            status_data.set_index("Trạng thái")
        )

    st.divider()

    st.subheader("📅 Khách đang lưu trú")

    active = query_df("""
        SELECT
            b.id AS booking_id,
            r.room_number,
            g.full_name,
            g.phone,
            b.check_in,
            b.adults,
            b.children,
            b.price_per_night,
            b.note
        FROM bookings b
        JOIN rooms r ON b.room_id = r.id
        JOIN guests g ON b.guest_id = g.id
        WHERE b.status = 'Đang ở'
        ORDER BY b.check_in DESC
    """)

    if active.empty:
        st.info("Hiện không có khách đang lưu trú.")
    else:
        active_display = active.copy()
        active_display.columns = [
            "Mã booking",
            "Phòng",
            "Khách",
            "Điện thoại",
            "Check-in",
            "Người lớn",
            "Trẻ em",
            "Giá/đêm",
            "Ghi chú",
        ]
        active_display["Giá/đêm"] = active_display["Giá/đêm"].apply(money)

        st.dataframe(
            active_display,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# ROOM MANAGEMENT
# =========================================================

def room_management():
    st.markdown('<div class="hotel-title">🛏️ Quản lý phòng</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hotel-subtitle">Thêm, sửa và cập nhật trạng thái phòng</div>',
        unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs(["Danh sách phòng", "Thêm phòng"])

    with tab1:
        rooms = query_df("SELECT * FROM rooms ORDER BY floor, room_number")

        if rooms.empty:
            st.info("Chưa có phòng.")
            return

        col1, col2 = st.columns(2)

        with col1:
            status_filter = st.selectbox(
                "Lọc trạng thái",
                ["Tất cả", "Trống", "Đang ở", "Đang dọn", "Bảo trì"]
            )

        with col2:
            search = st.text_input(
                "Tìm phòng",
                placeholder="Ví dụ: 101"
            )

        filtered = rooms.copy()

        if status_filter != "Tất cả":
            filtered = filtered[
                filtered["status"] == status_filter
            ]

        if search:
            filtered = filtered[
                filtered["room_number"].astype(str)
                .str.contains(search, case=False)
            ]

        st.write(f"Hiển thị **{len(filtered)}** phòng")

        for _, room in filtered.iterrows():
            col1, col2, col3, col4, col5 = st.columns(
                [1, 2, 1, 1, 1]
            )

            with col1:
                st.markdown(f"### {room['room_number']}")

            with col2:
                st.write(
                    f"**{room['room_type']}** · Tầng {room['floor']}"
                )

            with col3:
                st.write(money(room["price"]))

            with col4:
                st.write(room["status"])

            with col5:
                new_status = st.selectbox(
                    "Trạng thái",
                    ["Trống", "Đang ở", "Đang dọn", "Bảo trì"],
                    index=[
                        "Trống",
                        "Đang ở",
                        "Đang dọn",
                        "Bảo trì"
                    ].index(room["status"]),
                    key=f"status_{room['id']}",
                    label_visibility="collapsed"
                )

                if new_status != room["status"]:
                    update_room_status(room["id"], new_status)
                    st.rerun()

            st.divider()

    with tab2:
        st.subheader("➕ Thêm phòng mới")

        with st.form("add_room_form"):
            col1, col2 = st.columns(2)

            with col1:
                room_number = st.text_input("Số phòng *")
                room_type = st.selectbox(
                    "Loại phòng",
                    ["Standard", "Deluxe", "Suite", "Family", "VIP"]
                )

            with col2:
                floor = st.number_input(
                    "Tầng",
                    min_value=1,
                    max_value=100,
                    value=1
                )

                price = st.number_input(
                    "Giá phòng / đêm",
                    min_value=0,
                    value=500000,
                    step=50000
                )

            submitted = st.form_submit_button(
                "💾 Thêm phòng",
                use_container_width=True,
                type="primary"
            )

            if submitted:
                if not room_number.strip():
                    st.error("Vui lòng nhập số phòng.")
                else:
                    try:
                        execute("""
                            INSERT INTO rooms
                            (room_number, room_type, floor, price, status)
                            VALUES (?, ?, ?, ?, 'Trống')
                        """, (
                            room_number.strip(),
                            room_type,
                            floor,
                            price
                        ))

                        st.success(
                            f"Đã thêm phòng {room_number}."
                        )
                        st.rerun()

                    except sqlite3.IntegrityError:
                        st.error(
                            "Số phòng này đã tồn tại."
                        )


# =========================================================
# BOOKING / CHECK-IN
# =========================================================

def booking_management():
    st.markdown('<div class="hotel-title">📋 Đặt phòng & Check-in</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hotel-subtitle">Tạo booking và quản lý khách đang lưu trú</div>',
        unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs([
        "➕ Check-in",
        "📋 Danh sách booking"
    ])

    with tab1:
        rooms = query_df("""
            SELECT * FROM rooms
            WHERE status = 'Trống'
            ORDER BY room_number
        """)

        if rooms.empty:
            st.warning("Hiện không có phòng trống.")
        else:
            room_options = {
                f"{row['room_number']} - {row['room_type']} - {money(row['price'])}/đêm":
                row
                for _, row in rooms.iterrows()
            }

            with st.form("checkin_form"):
                st.subheader("Thông tin lưu trú")

                selected_room_label = st.selectbox(
                    "Chọn phòng *",
                    list(room_options.keys())
                )

                selected_room = room_options[selected_room_label]

                col1, col2 = st.columns(2)

                with col1:
                    full_name = st.text_input("Họ tên khách *")
                    phone = st.text_input("Số điện thoại")
                    id_number = st.text_input("CCCD / Passport")

                with col2:
                    email = st.text_input("Email")
                    adults = st.number_input(
                        "Số người lớn",
                        min_value=1,
                        value=1
                    )
                    children = st.number_input(
                        "Số trẻ em",
                        min_value=0,
                        value=0
                    )

                col3, col4 = st.columns(2)

                with col3:
                    check_in = st.date_input(
                        "Ngày check-in",
                        value=date.today()
                    )

                with col4:
                    check_out = st.date_input(
                        "Ngày check-out dự kiến",
                        value=date.today()
                    )

                note = st.text_area("Ghi chú")

                submitted = st.form_submit_button(
                    "🏨 Xác nhận Check-in",
                    use_container_width=True,
                    type="primary"
                )

                if submitted:
                    if not full_name.strip():
                        st.error("Vui lòng nhập tên khách.")
                    elif check_out < check_in:
                        st.error(
                            "Ngày check-out không được trước ngày check-in."
                        )
                    else:
                        # Tạo khách
                        guest_id = execute("""
                            INSERT INTO guests
                            (full_name, phone, email, id_number, created_at)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            full_name.strip(),
                            phone.strip(),
                            email.strip(),
                            id_number.strip(),
                            now_str()
                        ))

                        nights = calculate_nights(
                            check_in,
                            check_out
                        )

                        total = nights * float(
                            selected_room["price"]
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
                            int(selected_room["id"]),
                            guest_id,
                            str(check_in),
                            str(check_out),
                            adults,
                            children,
                            float(selected_room["price"]),
                            total,
                            "Đang ở",
                            note,
                            now_str()
                        ))

                        update_room_status(
                            int(selected_room["id"]),
                            "Đang ở"
                        )

                        st.success(
                            f"Check-in thành công! Mã booking: #{booking_id}"
                        )
                        st.info(
                            f"Tạm tính {nights} đêm: {money(total)}"
                        )

    with tab2:
        bookings = query_df("""
            SELECT
                b.id,
                r.room_number,
                g.full_name,
                g.phone,
                b.check_in,
                b.check_out,
                b.adults,
                b.children,
                b.price_per_night,
                b.total_amount,
                b.status,
                b.note
            FROM bookings b
            JOIN rooms r ON b.room_id = r.id
            JOIN guests g ON b.guest_id = g.id
            ORDER BY b.id DESC
        """)

        if bookings.empty:
            st.info("Chưa có booking.")
        else:
            status_filter = st.selectbox(
                "Lọc booking",
                ["Tất cả", "Đang ở", "Đã trả phòng", "Đã hủy"]
            )

            display = bookings.copy()

            if status_filter != "Tất cả":
                display = display[
                    display["status"] == status_filter
                ]

            display_view = display.copy()

            display_view.columns = [
                "Booking",
                "Phòng",
                "Khách",
                "Điện thoại",
                "Check-in",
                "Check-out",
                "NL",
                "TE",
                "Giá/đêm",
                "Tổng tiền",
                "Trạng thái",
                "Ghi chú",
            ]

            display_view["Giá/đêm"] = (
                display_view["Giá/đêm"].apply(money)
            )

            display_view["Tổng tiền"] = (
                display_view["Tổng tiền"].apply(money)
            )

            st.dataframe(
                display_view,
                use_container_width=True,
                hide_index=True
            )

            active_bookings = display[
                display["status"] == "Đang ở"
            ]

            if not active_bookings.empty:
                st.divider()
                st.subheader("🚪 Check-out")

                booking_options = {
                    f"#{row['id']} - Phòng {row['room_number']} - {row['full_name']}":
                    row
                    for _, row in active_bookings.iterrows()
                }

                selected = st.selectbox(
                    "Chọn booking cần check-out",
                    list(booking_options.keys())
                )

                booking = booking_options[selected]

                st.info(
                    f"Khách: **{booking['full_name']}** | "
                    f"Phòng: **{booking['room_number']}** | "
                    f"Tổng tiền dự kiến: **{money(booking['total_amount'])}**"
                )

                if st.button(
                    "🚪 Xác nhận Check-out",
                    type="primary"
                ):
                    execute("""
                        UPDATE bookings
                        SET status = 'Đã trả phòng',
                            check_out = ?
                        WHERE id = ?
                    """, (
                        str(date.today()),
                        int(booking["id"])
                    ))

                    room_df = query_df("""
                        SELECT id FROM rooms
                        WHERE room_number = ?
                    """, (booking["room_number"],))

                    if not room_df.empty:
                        update_room_status(
                            int(room_df.iloc[0]["id"]),
                            "Đang dọn"
                        )

                    st.success(
                        f"Đã check-out phòng {booking['room_number']}."
                    )
                    st.rerun()


# =========================================================
# GUEST MANAGEMENT
# =========================================================

def guest_management():
    st.markdown('<div class="hotel-title">👤 Khách hàng</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hotel-subtitle">Danh sách và lịch sử khách lưu trú</div>',
        unsafe_allow_html=True
    )

    guests = query_df("""
        SELECT
            g.id,
            g.full_name,
            g.phone,
            g.email,
            g.id_number,
            g.created_at,
            COUNT(b.id) AS total_bookings
        FROM guests g
        LEFT JOIN bookings b ON g.id = b.guest_id
        GROUP BY g.id
        ORDER BY g.id DESC
    """)

    if guests.empty:
        st.info("Chưa có dữ liệu khách hàng.")
        return

    search = st.text_input(
        "🔎 Tìm khách hàng",
        placeholder="Tên, số điện thoại hoặc CCCD..."
    )

    if search:
        mask = (
            guests["full_name"].astype(str).str.contains(
                search, case=False, na=False
            )
            |
            guests["phone"].astype(str).str.contains(
                search, case=False, na=False
            )
            |
            guests["id_number"].astype(str).str.contains(
                search, case=False, na=False
            )
        )

        guests = guests[mask]

    st.write(f"Tìm thấy **{len(guests)}** khách hàng")

    display = guests.copy()

    display.columns = [
        "ID",
        "Họ tên",
        "Điện thoại",
        "Email",
        "CCCD/Passport",
        "Ngày tạo",
        "Số booking",
    ]

    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    if not guests.empty:
        guest_id = st.selectbox(
            "Xem lịch sử khách",
            guests["id"].tolist()
        )

        history = query_df("""
            SELECT
                b.id AS booking_id,
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
            JOIN rooms r ON b.room_id = r.id
            WHERE b.guest_id = ?
            ORDER BY b.id DESC
        """, (int(guest_id),))

        st.subheader("📜 Lịch sử lưu trú")

        if history.empty:
            st.info("Khách chưa có lịch sử booking.")
        else:
            history_display = history.copy()
            history_display["price_per_night"] = (
                history_display["price_per_night"].apply(money)
            )
            history_display["total_amount"] = (
                history_display["total_amount"].apply(money)
            )

            history_display.columns = [
                "Booking",
                "Phòng",
                "Check-in",
                "Check-out",
                "NL",
                "TE",
                "Giá/đêm",
                "Tổng tiền",
                "Trạng thái",
                "Ghi chú",
            ]

            st.dataframe(
                history_display,
                use_container_width=True,
                hide_index=True
            )


# =========================================================
# PAYMENT
# =========================================================

def payment_management():
    st.markdown('<div class="hotel-title">💰 Thanh toán</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hotel-subtitle">Thu tiền và theo dõi doanh thu</div>',
        unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs([
        "➕ Thu tiền",
        "📊 Lịch sử thanh toán"
    ])

    with tab1:
        bookings = query_df("""
            SELECT
                b.id,
                r.room_number,
                g.full_name,
                b.total_amount,
                COALESCE(SUM(p.amount), 0) AS paid
            FROM bookings b
            JOIN rooms r ON b.room_id = r.id
            JOIN guests g ON b.guest_id = g.id
            LEFT JOIN payments p ON b.id = p.booking_id
            WHERE b.status != 'Đã hủy'
            GROUP BY b.id
            ORDER BY b.id DESC
        """)

        if bookings.empty:
            st.info("Chưa có booking.")
        else:
            booking_options = {}

            for _, row in bookings.iterrows():
                remaining = max(
                    float(row["total_amount"]) - float(row["paid"]),
                    0
                )

                booking_options[
                    f"#{row['id']} - Phòng {row['room_number']} - "
                    f"{row['full_name']} - Còn {money(remaining)}"
                ] = row

            selected = st.selectbox(
                "Chọn booking",
                list(booking_options.keys())
            )

            booking = booking_options[selected]

            total = float(booking["total_amount"])
            paid = float(booking["paid"])
            remaining = max(total - paid, 0)

            col1, col2, col3 = st.columns(3)

            col1.metric("Tổng tiền", money(total))
            col2.metric("Đã thanh toán", money(paid))
            col3.metric("Còn lại", money(remaining))

            if remaining <= 0:
                st.success("Booking này đã thanh toán đủ.")
            else:
                with st.form("payment_form"):
                    amount = st.number_input(
                        "Số tiền thu",
                        min_value=0.0,
                        max_value=remaining,
                        value=remaining,
                        step=50000.0
                    )

                    payment_method = st.selectbox(
                        "Phương thức",
                        [
                            "Tiền mặt",
                            "Chuyển khoản",
                            "Thẻ",
                            "Ví điện tử"
                        ]
                    )

                    note = st.text_input("Ghi chú")

                    submitted = st.form_submit_button(
                        "💵 Xác nhận thu tiền",
                        type="primary",
                        use_container_width=True
                    )

                    if submitted:
                        if amount <= 0:
                            st.error(
                                "Số tiền phải lớn hơn 0."
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
                                int(booking["id"]),
                                amount,
                                payment_method,
                                now_str(),
                                note
                            ))

                            st.success(
                                f"Đã thu {money(amount)}."
                            )
                            st.rerun()

    with tab2:
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
            JOIN bookings b ON p.booking_id = b.id
            JOIN rooms r ON b.room_id = r.id
            JOIN guests g ON b.guest_id = g.id
            ORDER BY p.id DESC
        """)

        if payments.empty:
            st.info("Chưa có giao dịch.")
        else:
            display = payments.copy()

            total_revenue = float(
                display["amount"].sum()
            )

            st.metric(
                "Tổng doanh thu",
                money(total_revenue)
            )

            display["amount"] = (
                display["amount"].apply(money)
            )

            display.columns = [
                "ID",
                "Booking",
                "Phòng",
                "Khách",
                "Số tiền",
                "Phương thức",
                "Thời gian",
                "Ghi chú",
            ]

            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True
            )

            csv = payments.to_csv(
                index=False
            ).encode("utf-8-sig")

            st.download_button(
                "⬇️ Tải lịch sử thanh toán CSV",
                data=csv,
                file_name="lich_su_thanh_toan.csv",
                mime="text/csv"
            )


# =========================================================
# MAIN
# =========================================================

def main():
    init_db()
    inject_css()

    menu = sidebar()

    if menu == "📊 Tổng quan":
        dashboard()

    elif menu == "🛏️ Quản lý phòng":
        room_management()

    elif menu == "📋 Đặt phòng":
        booking_management()

    elif menu == "👤 Khách hàng":
        guest_management()

    elif menu == "💰 Thanh toán":
        payment_management()


if __name__ == "__main__":
    main()
