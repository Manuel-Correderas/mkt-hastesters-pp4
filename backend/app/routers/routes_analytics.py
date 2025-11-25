# backend/app/routers/routes_analytics.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, date as date_type
from typing import Optional, List, Dict, Any

from ..deps import get_db, get_current_user
from ..models.models import Order, OrderItem, Product, User

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ==========================================================
# HELPERS
# ==========================================================
def parse_date(s: str) -> date_type:
    try:
        return datetime.fromisoformat(s).date()
    except Exception:
        raise HTTPException(status_code=400, detail=f"Fecha inválida: {s}")


def to_dt_start(d: date_type) -> datetime:
    return datetime.combine(d, datetime.min.time())


def to_dt_end(d: date_type) -> datetime:
    return datetime.combine(d, datetime.max.time())


def date_range(months: int = 3):
    end = datetime.now()
    start = end - timedelta(days=30 * months)
    return start, end


def month_expr(db: Session, dt_col):
    """
    Expresión SQL para agrupar por mes (YYYY-MM),
    compatible con sqlite y mysql/mariadb.
    """
    dialect = db.bind.dialect.name
    if dialect == "sqlite":
        return func.strftime("%Y-%m", dt_col)
    return func.date_format(dt_col, "%Y-%m")


def seller_filter(db: Session, current_user: User):
    """
    Filtro robusto vendedor:
    - si OrderItem tiene seller_id cargado -> usar eso
    - si no, usar snapshot 'seller' comparando nombre/email
    """
    seller_id = str(current_user.id)
    seller_key = (current_user.nombre or "").strip().lower()
    seller_email = (current_user.email or "").strip().lower()

    has_seller_id_attr = hasattr(OrderItem, "seller_id")

    if has_seller_id_attr:
        return (OrderItem.seller_id == seller_id) | (
            func.lower(func.coalesce(OrderItem.seller, "")) == seller_key
        ) | (
            func.lower(func.coalesce(OrderItem.seller, "")) == seller_email
        )

    return (
        func.lower(func.coalesce(OrderItem.seller, "")) == seller_key
    ) | (
        func.lower(func.coalesce(OrderItem.seller, "")) == seller_email
    )


def buyer_filter(current_user: User):
    """Filtro comprador (Order.user_id)."""
    return Order.user_id == str(current_user.id)


def normalize_currency(val: float, currency: str):
    # Si más adelante querés convertir, enchufás acá.
    return val


# ==========================================================
# 0) GLOBAL METRICS  (para Dashboard_Global.py)
# ==========================================================
@router.get("/global")
def global_metrics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Usuarios / productos
    total_users = db.query(User).count()
    total_products = db.query(Product).count()

    # Estos campos pueden variar en tu modelo Product
    products_out_of_stock = 0
    products_with_image = 0

    if hasattr(Product, "stock"):
        products_out_of_stock = (
            db.query(Product).filter(Product.stock <= 0).count()
        )
    if hasattr(Product, "image_url"):
        products_with_image = (
            db.query(Product).filter(Product.image_url.isnot(None)).count()
        )
    elif hasattr(Product, "image"):
        products_with_image = (
            db.query(Product).filter(Product.image.isnot(None)).count()
        )

    # Top categorías (si existe Product.category)
    top_categories: List[str] = []
    if hasattr(Product, "category"):
        rows = (
            db.query(Product.category, func.count(Product.id).label("cnt"))
            .group_by(Product.category)
            .order_by(func.count(Product.id).desc())
            .limit(5)
            .all()
        )
        top_categories = [c for c, _ in rows if c]

    return {
        "total_users": int(total_users),
        "total_products": int(total_products),
        "products_out_of_stock": int(products_out_of_stock),
        "products_with_image": int(products_with_image),
        "top_categories": top_categories,
    }


# ==========================================================
# 0b) ORDERS BETWEEN DATES (para Dashboard_Global.py)
# ==========================================================
@router.get("/orders")
def orders_between(
    # el front manda params "from" y "to"
    from_date: date_type = Query(..., alias="from"),
    to_date: date_type = Query(..., alias="to"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    start_dt = to_dt_start(from_date)
    end_dt = to_dt_end(to_date)

    # Traemos items con su orden
    rows = (
        db.query(OrderItem, Order)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.created_at >= start_dt)
        .filter(Order.created_at <= end_dt)
        .all()
    )

    out: List[Dict[str, Any]] = []
    for it, o in rows:
        out.append({
            "order_date": o.created_at.isoformat() if o.created_at else None,
            "seller_name": getattr(it, "seller", None) or getattr(o, "seller_name", None) or "Sin vendedor",
            "product_name": getattr(it, "product_name", None) or "Producto",
            "qty": int(getattr(it, "quantity", 0) or 0),
            "total_paid": float((getattr(it, "unit_price", 0) or 0) * (getattr(it, "quantity", 0) or 0)),
            "payment_method": getattr(o, "payment_method", None) or "N/D",
            "status": getattr(o, "status", None) or "unknown",
        })

    return out


# ==========================================================
# 1) SALES SUMMARY (para Finanzas.py)
# ==========================================================
@router.get("/sales-summary")
def sales_summary(
    start: str,
    end: str,
    currency: str = "ARS",
    channels: str = "tienda",
    seller_id: Optional[str] = None,   # opcional, por si querés forzar
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    start_d = parse_date(start)
    end_d = parse_date(end)
    start_dt = to_dt_start(start_d)
    end_dt = to_dt_end(end_d)

    # Si pasan seller_id explícito, usamos ese (mismo filtro robusto)
    if seller_id:
        sf = seller_filter(db, user)
        items = (
            db.query(OrderItem)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(Order.created_at >= start_dt)
            .filter(Order.created_at <= end_dt)
            .filter(sf)
            .all()
        )
        total_sales = sum((i.unit_price or 0) * (i.quantity or 0) for i in items)
        orders_count = len({i.order_id for i in items})
    else:
        # Por defecto: vendedor ve sus ventas, comprador sus compras
        sf = seller_filter(db, user)
        items_seller = (
            db.query(OrderItem)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(Order.created_at >= start_dt)
            .filter(Order.created_at <= end_dt)
            .filter(sf)
            .all()
        )

        if items_seller:
            total_sales = sum((i.unit_price or 0) * (i.quantity or 0) for i in items_seller)
            orders_count = len({i.order_id for i in items_seller})
        else:
            orders_buyer = (
                db.query(Order)
                .filter(Order.created_at >= start_dt)
                .filter(Order.created_at <= end_dt)
                .filter(buyer_filter(user))
                .all()
            )
            total_sales = sum(o.total_amount or 0 for o in orders_buyer)
            orders_count = len(orders_buyer)

    total_sales = normalize_currency(float(total_sales), currency)
    total_margin = total_sales * 0.30  # margen simple dummy
    ticket_avg = (total_sales / orders_count) if orders_count else 0

    return {
        "total_sales": total_sales,
        "total_margin": total_margin,
        "ticket_avg": ticket_avg,
        "returns": 0,
    }


# ==========================================================
# 2) DAILY SALES (para Finanzas.py)
# ==========================================================
@router.get("/sales-daily")
def sales_daily(
    start: str,
    end: str,
    currency: str = "ARS",
    channels: str = "tienda",
    seller_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    start_d = parse_date(start)
    end_d = parse_date(end)
    start_dt = to_dt_start(start_d)
    end_dt = to_dt_end(end_d)

    sf = seller_filter(db, user)

    q = (
        db.query(
            func.date(Order.created_at).label("d"),
            func.sum(OrderItem.unit_price * OrderItem.quantity).label("total")
        )
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(Order.created_at >= start_dt)
        .filter(Order.created_at <= end_dt)
    )

    # ✅ FIX: antes tenías "seller_id or True"
    if seller_id:
        q = q.filter(sf)
    else:
        # si no pasan seller_id, elegimos por rol implícito
        # si tiene ventas como vendedor, filtra seller; si no, buyer.
        items_seller = (
            db.query(OrderItem.id)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(Order.created_at >= start_dt)
            .filter(Order.created_at <= end_dt)
            .filter(sf)
            .limit(1)
            .all()
        )
        if items_seller:
            q = q.filter(sf)
        else:
            q = q.filter(buyer_filter(user))

    rows = q.group_by("d").order_by("d").all()
    out = [{"date": str(d), "total": float(t or 0)} for d, t in rows]
    return out


# ==========================================================
# 3) CATEGORY MARGINS (para Finanzas.py)
# ==========================================================
@router.get("/category-margins")
def category_margins(
    start: str,
    end: str,
    currency: str = "ARS",
    channels: str = "tienda",
    seller_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    start_d = parse_date(start)
    end_d = parse_date(end)
    start_dt = to_dt_start(start_d)
    end_dt = to_dt_end(end_d)

    sf = seller_filter(db, user)

    items = (
        db.query(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.created_at >= start_dt)
        .filter(Order.created_at <= end_dt)
        .filter(sf)
        .all()
    )

    rows: Dict[str, float] = {}
    for i in items:
        cat = i.category or "Sin categoría"
        rows.setdefault(cat, 0.0)
        rows[cat] += float((i.unit_price or 0) * (i.quantity or 0))

    return [{"category": c, "margin": t * 0.30} for c, t in rows.items()]


# ==========================================================
# 4) TOP PRODUCTS (para Finanzas.py)
# ==========================================================
@router.get("/top-products")
def top_products(
    start: str,
    end: str,
    top: int = 8,
    currency: str = "ARS",
    channels: str = "tienda",
    seller_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    start_d = parse_date(start)
    end_d = parse_date(end)
    start_dt = to_dt_start(start_d)
    end_dt = to_dt_end(end_d)

    sf = seller_filter(db, user)

    items = (
        db.query(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.created_at >= start_dt)
        .filter(Order.created_at <= end_dt)
        .filter(sf)
        .all()
    )

    rows: Dict[str, float] = {}
    for i in items:
        name = i.product_name or "Producto"
        rows.setdefault(name, 0.0)
        rows[name] += float((i.unit_price or 0) * (i.quantity or 0))

    out = [{"product": p, "sales": t} for p, t in rows.items()]
    out.sort(key=lambda x: x["sales"], reverse=True)
    return out[:top]


# ==========================================================
# 5) OPERATIONS DETAIL (para Finanzas.py)
# ==========================================================
@router.get("/operations")
def operations(
    start: str,
    end: str,
    currency: str = "ARS",
    channels: str = "tienda",
    seller_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    start_d = parse_date(start)
    end_d = parse_date(end)
    start_dt = to_dt_start(start_d)
    end_dt = to_dt_end(end_d)

    sf = seller_filter(db, user)

    items = (
        db.query(OrderItem, Order)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.created_at >= start_dt)
        .filter(Order.created_at <= end_dt)
        .filter(sf)
        .all()
    )

    return [
        {
            "date": o.created_at.isoformat() if o.created_at else None,
            "order_id": it.order_id,
            "product": it.product_name,
            "qty": it.quantity,
            "unit_price": it.unit_price,
            "total": (it.quantity or 0) * (it.unit_price or 0),
        }
        for it, o in items
    ]


# ==========================================================
# DASHBOARD VENDEDOR (para Dashboard_Local.py)
# ==========================================================
@router.get("/seller/dashboard")
def seller_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sf = seller_filter(db, current_user)

    # 1) KPIs
    total_sales = (
        db.query(func.sum(OrderItem.unit_price * OrderItem.quantity))
        .join(Order, OrderItem.order_id == Order.id)
        .filter(sf)
        .scalar()
        or 0
    )

    orders_count = (
        db.query(func.count(func.distinct(Order.id)))
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(sf)
        .scalar()
        or 0
    )

    avg_rating = 0
    if hasattr(Product, "rating"):
        avg_rating = (
            db.query(func.avg(Product.rating))
            .filter(Product.seller_id == str(current_user.id))
            .scalar()
            or 0
        )

    returns = (
        db.query(func.count(Order.id))
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(sf, func.lower(Order.status) == "returned")
        .scalar()
        or 0
    )

    # 2) Ventas mensuales
    start, _ = date_range(4)
    mexpr = month_expr(db, Order.created_at)

    monthly = (
        db.query(
            mexpr.label("period"),
            func.sum(OrderItem.unit_price * OrderItem.quantity).label("total"),
        )
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(sf, Order.created_at >= start)
        .group_by("period")
        .order_by("period")
        .all()
    )

    # 3) Pedidos por categoría
    category_sales = (
        db.query(
            func.coalesce(OrderItem.category, "Sin categoría").label("category"),
            func.sum(OrderItem.quantity).label("orders"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .filter(sf)
        .group_by("category")
        .order_by(func.sum(OrderItem.quantity).desc())
        .all()
    )

    # 4) Top productos
    top_products = (
        db.query(
            OrderItem.product_name.label("name"),
            func.avg(OrderItem.unit_price).label("price"),
            func.sum(OrderItem.quantity).label("sold"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .filter(sf)
        .group_by(OrderItem.product_id, OrderItem.product_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(3)
        .all()
    )

    # 5) Últimos pedidos
    recent_orders = (
        db.query(
            Order.id,
            Order.status,
            Order.created_at,
            OrderItem.product_name,
            (OrderItem.unit_price * OrderItem.quantity).label("total"),
            Order.user_name.label("client_name"),
        )
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(sf)
        .order_by(Order.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "kpis": {
            "total_sales": float(total_sales),
            "orders_count": int(orders_count),
            "rating": float(avg_rating),
            "returns": int(returns),
        },
        "series": {
            "monthly_sales": [{"period": p, "total": float(t or 0)} for p, t in monthly],
            "orders_by_category": [
                {"category": c, "orders": int(o or 0)} for c, o in category_sales
            ],
        },
        "lists": {
            "top_products": [
                {"name": n, "price": float(pr or 0), "sold": int(s or 0), "rating": None}
                for n, pr, s in top_products
            ],
            "recent_orders": [
                {
                    "id": oid,
                    "status": st,
                    "date": dt.isoformat() if dt else None,
                    "product_name": pname,
                    "total": float(tot or 0),
                    "client_name": cname,
                }
                for oid, st, dt, pname, tot, cname in recent_orders
            ],
        },
    }


# ==========================================================
# DASHBOARD COMPRADOR (para Dashboard_Local.py)
# ==========================================================
@router.get("/buyer/dashboard")
def buyer_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    buyer_id = str(current_user.id)

    total_spent = (
        db.query(func.sum(OrderItem.unit_price * OrderItem.quantity))
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.user_id == buyer_id)
        .scalar()
        or 0
    )

    orders_count = (
        db.query(func.count(Order.id))
        .filter(Order.user_id == buyer_id)
        .scalar()
        or 0
    )

    # Compras mensuales
    start, _ = date_range(4)
    mexpr = month_expr(db, Order.created_at)

    monthly = (
        db.query(
            mexpr.label("period"),
            func.sum(OrderItem.unit_price * OrderItem.quantity).label("amount"),
        )
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(Order.user_id == buyer_id, Order.created_at >= start)
        .group_by("period")
        .order_by("period")
        .all()
    )

    recent_purchases = (
        db.query(
            Order.id,
            Order.status,
            Order.created_at,
            OrderItem.product_name,
            (OrderItem.unit_price * OrderItem.quantity).label("total"),
        )
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(Order.user_id == buyer_id)
        .order_by(Order.created_at.desc())
        .limit(5)
        .all()
    )

    top_brands = (
        db.query(
            func.coalesce(OrderItem.company, OrderItem.seller, "Sin marca").label("name"),
            func.count(func.distinct(Order.id)).label("orders"),
            func.sum(OrderItem.unit_price * OrderItem.quantity).label("spent"),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .filter(Order.user_id == buyer_id)
        .group_by("name")
        .order_by(func.count(func.distinct(Order.id)).desc())
        .limit(3)
        .all()
    )

    return {
        "kpis": {
            "total_spent": float(total_spent),
            "orders_count": int(orders_count),
        },
        "series": {
            "monthly_purchases": [
                {"period": p, "amount": float(a or 0)} for p, a in monthly
            ]
        },
        "lists": {
            "recent_purchases": [
                {
                    "id": oid,
                    "status": st,
                    "date": dt.isoformat() if dt else None,
                    "product_name": pname,
                    "total": float(tot or 0),
                }
                for oid, st, dt, pname, tot in recent_purchases
            ],
            "top_brands": [
                {
                    "name": n,
                    "orders": int(o or 0),
                    "spent": float(s or 0),
                    "rating": None,
                }
                for n, o, s in top_brands
            ],
        },
    }
