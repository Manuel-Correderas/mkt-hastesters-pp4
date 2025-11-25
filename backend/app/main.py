# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routers import auth


from .db import init_db

from .routers import (
    routes_analytics,
    routes_products,
    routes_order_items,
    routes_users,
    routes_roles,
    routes_product_comments,
    routes_orders,
    routes_comments,   
    routes_auth,
    routes_cart,  
    routes_admin,
    routes_sales,
    routes_premium,
)

app = FastAPI(title="Ecom MKT Lab API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


@app.on_event("startup")
def on_startup():
    init_db()


# Routers
app.include_router(routes_roles.router)
app.include_router(routes_users.router)
app.include_router(routes_products.router)
app.include_router(routes_product_comments.router)
app.include_router(routes_orders.router)
app.include_router(routes_comments.router)  
app.include_router(routes_auth.router)     
app.include_router(routes_cart.router)  
app.include_router(routes_admin.router)  # 👈 NUEVO

app.include_router(routes_sales.router)

app.include_router(routes_order_items.router)

app.include_router(routes_analytics.router)
app.include_router(routes_premium.router)


app.include_router(auth.router) 