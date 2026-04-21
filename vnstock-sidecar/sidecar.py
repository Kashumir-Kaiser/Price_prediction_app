"""VNStock sidecar — exposes vnstock3 via a minimal HTTP API."""
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List
import vnstock3

app = FastAPI(title="VNStock Sidecar")


class OHLCV(BaseModel):
    ts: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@app.get("/ohlcv", response_model=List[OHLCV])
def get_ohlcv(
    symbol: str = Query(..., description="VN stock symbol, e.g. VCB"),
    start: str = Query(..., description="Start date YYYY-MM-DD"),
    end: str = Query(..., description="End date YYYY-MM-DD"),
):
    """Fetch daily OHLCV from vnstock3."""
    stock = vnstock3.Vnstock().stock(symbol=symbol, source="TCB")
    df = stock.quote.history(start=start, end=end, interval="1D")
    records = []
    for _, row in df.iterrows():
        records.append(
            OHLCV(
                ts=str(row["time"]),
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
            )
        )
    return records
