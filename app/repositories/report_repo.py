from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from ..models.booking import BookingStatus, PaymentStatus

_ALLOWED_BOOKING_STATUS = (BookingStatus.CHECKED_OUT,)
_ALLOWED_PAYMENT_STATUS = (PaymentStatus.PAID,)


async def get_summary(session: AsyncSession, start_date: date, end_date: date):
    query = text(
        """
        WITH filtered_bookings AS (
            SELECT b.id, b.primary_guest_id AS guest_key
            FROM bookings b
            WHERE b.status = ANY(:allowed_booking_status)
              AND b.payment_status = ANY(:allowed_payment_status)
              AND ((b.checkout AT TIME ZONE :tz)::date 
                    BETWEEN CAST(:start AS date) AND CAST(:end AS date))
        ),
        room_rev AS (
            SELECT COALESCE(SUM(d.amount), 0) AS amount
            FROM booking_details d
            JOIN filtered_bookings fb ON fb.id = d.booking_id
            WHERE d.type = 'Room'
        ),
        svc_rev AS (
            SELECT COALESCE(SUM(d.amount), 0) AS amount
            FROM booking_details d
            JOIN filtered_bookings fb ON fb.id = d.booking_id
            WHERE d.type = 'Service'
              AND ((d.issued_at AT TIME ZONE :tz)::date 
                    BETWEEN CAST(:start AS date) AND CAST(:end AS date))
        ),
        guests AS (
            SELECT COUNT(DISTINCT fb.guest_key) AS c 
            FROM filtered_bookings fb
            WHERE fb.guest_key IS NOT NULL
        )
        SELECT
            (SELECT amount FROM room_rev)  AS room_amount,
            (SELECT amount FROM svc_rev)   AS svc_amount,
            (SELECT c FROM guests)         AS guest_count;
    """
    )
    res = await session.execute(
        query,
        {
            "tz": "Asia/Ho_Chi_Minh",
            "start": start_date,
            "end": end_date,
            "allowed_booking_status": [s.value for s in _ALLOWED_BOOKING_STATUS],
            "allowed_payment_status": [s.value for s in _ALLOWED_PAYMENT_STATUS],
        },
    )
    row = res.fetchone()
    room_amount = float(row.room_amount or 0)
    svc_amount = float(row.svc_amount or 0)
    return {
        "room_amount": room_amount,
        "svc_amount": svc_amount,
        "guest_count": int(row.guest_count or 0),
        "total_revenue": room_amount + svc_amount,
    }


async def get_roomtype_revenue(session: AsyncSession, start_date: date, end_date: date):
    query = text(
        """
        SELECT rt.name AS room_type, COALESCE(SUM(d.amount), 0) AS revenue
        FROM booking_details d
        JOIN bookings b ON b.id = d.booking_id
        JOIN room_types rt ON rt.id = b.room_type_id
        WHERE b.status = ANY(:allowed_booking_status)
          AND b.payment_status = ANY(:allowed_payment_status)
          AND ((b.checkout AT TIME ZONE :tz)::date 
                BETWEEN CAST(:start AS date) AND CAST(:end AS date))
          AND d.type = 'Room'
        GROUP BY rt.name
        ORDER BY revenue DESC;
    """
    )
    res = await session.execute(
        query,
        {
            "tz": "Asia/Ho_Chi_Minh",
            "start": start_date,
            "end": end_date,
            "allowed_booking_status": [s.value for s in _ALLOWED_BOOKING_STATUS],
            "allowed_payment_status": [s.value for s in _ALLOWED_PAYMENT_STATUS],
        },
    )
    rows = res.fetchall()
    return [{"room_type": r.room_type, "revenue": float(r.revenue)} for r in rows]


async def get_service_revenue(session: AsyncSession, start_date: date, end_date: date):
    query = text(
        """
        SELECT s.name AS service_name, COALESCE(SUM(d.amount), 0) AS revenue
        FROM booking_details d
        JOIN bookings b ON b.id = d.booking_id
        JOIN services s ON s.id = d.service_id
        WHERE b.status = ANY(:allowed_booking_status)
          AND b.payment_status = ANY(:allowed_payment_status)
          AND ((d.issued_at AT TIME ZONE :tz)::date 
                BETWEEN CAST(:start AS date) AND CAST(:end AS date))
          AND d.type = 'Service'
        GROUP BY s.name
        ORDER BY revenue DESC;
    """
    )
    res = await session.execute(
        query,
        {
            "tz": "Asia/Ho_Chi_Minh",
            "start": start_date,
            "end": end_date,
            "allowed_booking_status": [s.value for s in _ALLOWED_BOOKING_STATUS],
            "allowed_payment_status": [s.value for s in _ALLOWED_PAYMENT_STATUS],
        },
    )
    rows = res.fetchall()
    return [{"service_name": r.service_name, "revenue": float(r.revenue)} for r in rows]


async def get_payment_method_revenue(
    session: AsyncSession, start_date: date, end_date: date
):
    query = text(
        """
        SELECT p.payment_method, COALESCE(SUM(p.amount), 0) AS revenue
        FROM payments p
        JOIN bookings b ON b.id = p.booking_id
        WHERE b.status = ANY(:allowed_booking_status)
          AND b.payment_status = ANY(:allowed_payment_status)
          AND ((p.paid_at AT TIME ZONE :tz)::date 
                BETWEEN CAST(:start AS date) AND CAST(:end AS date))
        GROUP BY p.payment_method
        ORDER BY revenue DESC;
    """
    )
    res = await session.execute(
        query,
        {
            "tz": "Asia/Ho_Chi_Minh",
            "start": start_date,
            "end": end_date,
            "allowed_booking_status": [s.value for s in _ALLOWED_BOOKING_STATUS],
            "allowed_payment_status": [s.value for s in _ALLOWED_PAYMENT_STATUS],
        },
    )
    rows = res.fetchall()
    return [
        {"payment_method": r.payment_method, "revenue": float(r.revenue)} for r in rows
    ]


async def get_bookings_per_day(session: AsyncSession, start_date: date, end_date: date):
    query = text(
        """
        SELECT 
            ((b.checkout AT TIME ZONE :tz)::date) AS day,
            COUNT(*) AS booking_count
        FROM bookings b
        WHERE b.status = ANY(:allowed_booking_status)
          AND b.payment_status = ANY(:allowed_payment_status)
          AND ((b.checkout AT TIME ZONE :tz)::date 
                BETWEEN CAST(:start AS date) AND CAST(:end AS date))
        GROUP BY day
        ORDER BY day ASC;
    """
    )
    res = await session.execute(
        query,
        {
            "tz": "Asia/Ho_Chi_Minh",
            "start": start_date,
            "end": end_date,
            "allowed_booking_status": [s.value for s in _ALLOWED_BOOKING_STATUS],
            "allowed_payment_status": [s.value for s in _ALLOWED_PAYMENT_STATUS],
        },
    )
    rows = res.fetchall()
    return [{"date": str(r.day), "booking_count": int(r.booking_count)} for r in rows]


async def get_customer_distribution(
    session: AsyncSession, start_date: date, end_date: date
):
    query = text(
        """
        WITH qualified AS (
            SELECT 
                b.id,
                b.primary_guest_id AS guest_key,
                ((b.checkout AT TIME ZONE :tz)::date) AS d
            FROM bookings b
            WHERE b.status = ANY(:allowed_booking_status)
              AND b.payment_status = ANY(:allowed_payment_status)
              AND b.primary_guest_id IS NOT NULL
        ),
        guest_first AS (
            SELECT guest_key, MIN(d) AS first_date
            FROM qualified
            GROUP BY guest_key
        ),
        in_range AS (
            SELECT DISTINCT guest_key
            FROM qualified
            WHERE d BETWEEN CAST(:start AS date) AND CAST(:end AS date)
        )
        SELECT
          SUM(CASE WHEN gf.first_date BETWEEN CAST(:start AS date) AND CAST(:end AS date) THEN 1 ELSE 0 END) AS new_customers,
          SUM(CASE WHEN gf.first_date < CAST(:start AS date) THEN 1 ELSE 0 END) AS returning_customers
        FROM in_range ir
        JOIN guest_first gf ON gf.guest_key = ir.guest_key;
    """
    )
    res = await session.execute(
        query,
        {
            "tz": "Asia/Ho_Chi_Minh",
            "start": start_date,
            "end": end_date,
            "allowed_booking_status": [s.value for s in _ALLOWED_BOOKING_STATUS],
            "allowed_payment_status": [s.value for s in _ALLOWED_PAYMENT_STATUS],
        },
    )
    row = res.fetchone()
    new_cus = int(row.new_customers or 0)
    returning_cus = int(row.returning_customers or 0)
    total = new_cus + returning_cus
    percent_new = round((new_cus / total) * 100, 2) if total else 0.0
    percent_returning = round((returning_cus / total) * 100, 2) if total else 0.0
    return {
        "new_customers": new_cus,
        "returning_customers": returning_cus,
        "percent_new": percent_new,
        "percent_returning": percent_returning,
        "total_in_range_customers": total,
    }
