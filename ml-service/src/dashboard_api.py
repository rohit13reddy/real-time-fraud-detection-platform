
import os

import psycopg
from psycopg.rows import dict_row
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Query

app = FastAPI(title="Fraud Detection Dashboard API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://fraud_user:fraud_dev_password@localhost:5432/fraud_detection",
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/transactions")
def get_transactions(limit: int = Query(default=100, ge=1, le=1000)):
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, transaction_id, actual_class, prediction,
                       fraud_score, threshold, processed_at
                FROM transactions
                ORDER BY id DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()

    return {"transactions": rows}


@app.get("/stats")
def get_stats():
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    COUNT(*) AS total_transactions,
                    COUNT(*) FILTER (
                        WHERE prediction = 'fraud'
                    ) AS flagged_transactions,
                    COUNT(*) FILTER (
                        WHERE actual_class = 1
                    ) AS actual_frauds,
                    COUNT(*) FILTER (
                        WHERE actual_class = 1 AND prediction = 'fraud'
                    ) AS detected_frauds,
                    COUNT(*) FILTER (
                        WHERE actual_class = 1 AND prediction != 'fraud'
                    ) AS missed_frauds,
                    COUNT(*) FILTER (
                        WHERE actual_class = 0 AND prediction = 'fraud'
                    ) AS false_positives
                FROM transactions
                """
            )
            stats = cur.fetchone()

    return stats

