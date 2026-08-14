from pydantic import BaseModel


class RevenueBucket(BaseModel):
    period: str  # daily: "2026-08-14", monthly: "2026-08"
    orders_count: int
    revenue: int
    cost: int
    profit: int


class RevenueReportResponse(BaseModel):
    period_type: str
    from_date: str
    to_date: str
    buckets: list[RevenueBucket]
    total_orders: int
    total_revenue: int
    total_cost: int
    total_profit: int
