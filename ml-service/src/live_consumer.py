import json
import os

import psycopg
import requests
from kafka import KafkaConsumer
from psycopg.rows import dict_row

TOPIC = "live-transactions"
BOOTSTRAP_SERVERS = "localhost:9092"
PREDICTION_URL = "http://127.0.0.1:8000/predict"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://fraud_user:fraud_dev_password@localhost:5432/fraud_detection",
)

FEATURES = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]


def main():
    print(f"Connecting to Kafka topic: {TOPIC}")

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id="fraud-live-consumer",
        auto_offset_reset="latest",
        enable_auto_commit=False,
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )

    try:
        with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
            print("Connected to PostgreSQL.")
            print("Waiting for live transactions. Press Ctrl+C to stop.\n")

            for message in consumer:
                transaction = message.value
                transaction_id = transaction["transaction_id"]
                actual_class = transaction.get("Class")

                features = {
                    feature: float(transaction[feature])
                    for feature in FEATURES
                }

                try:
                    response = requests.post(
                        PREDICTION_URL,
                        json=features,
                        timeout=10,
                    )
                    response.raise_for_status()
                    result = response.json()

                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO transactions
                                (transaction_id, actual_class, prediction,
                                 fraud_score, threshold)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (
                                transaction_id,
                                actual_class,
                                result["prediction"],
                                result["fraud_score"],
                                result["threshold"],
                            ),
                        )

                    # Save the database row before acknowledging the Kafka message.
                    conn.commit()
                    consumer.commit()

                    print(
                        f"Processed {transaction_id} | "
                        f"prediction={result['prediction']} | "
                        f"fraud_score={result['fraud_score']:.4f}"
                    )

                except Exception as exc:
                    conn.rollback()
                    print(
                        f"Failed to process transaction {transaction_id}: {exc}"
                    )
                    # Do not commit this message; it can be retried after restart.

    except KeyboardInterrupt:
        print("\nStopping live consumer...")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
