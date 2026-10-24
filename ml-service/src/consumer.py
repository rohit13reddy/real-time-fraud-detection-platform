
import json
import os

import psycopg
import requests
from kafka import KafkaConsumer

KAFKA_SERVER = "localhost:9092"
TOPIC = "fraud-test-transactions"
API_URL = "http://127.0.0.1:8000/predict"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://fraud_user:fraud_dev_password@localhost:5432/fraud_detection",
)

FEATURE_NAMES = [
    "Time",
    *[f"V{i}" for i in range(1, 29)],
    "Amount",
]


def save_prediction(conn, transaction_id, actual_class, result):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO transactions
                (transaction_id, actual_class, prediction, fraud_score, threshold)
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
    conn.commit()


def main():
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_SERVER,
        group_id="fraud-detection-db",
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )

    print("Waiting for transactions from Kafka...")

    try:
        with psycopg.connect(DATABASE_URL) as conn:
            for message in consumer:
                transaction = json.loads(message.value.decode("utf-8"))

                features = {
                    name: transaction[name]
                    for name in FEATURE_NAMES
                }

                response = requests.post(
                    API_URL,
                    json=features,
                    timeout=10,
                )
                response.raise_for_status()
                result = response.json()

                transaction_id = int(transaction["transaction_id"])
                actual_class = int(transaction["Class"])

                save_prediction(
                    conn,
                    transaction_id,
                    actual_class,
                    result,
                )

                # Commit the Kafka offset only after saving to PostgreSQL.
                consumer.commit()

                print("\nTransaction processed and saved")
                print(f"Transaction ID: {transaction_id}")
                print(f"Actual class:   {actual_class}")
                print(f"Prediction:     {result['prediction']}")
                print(f"Fraud score:    {result['fraud_score']}")
                print(f"Threshold:      {result['threshold']}")

    except KeyboardInterrupt:
        print("\nConsumer stopped.")

    finally:
        consumer.close()


if __name__ == "__main__":
    main()
