
import json
import time
from pathlib import Path

import pandas as pd
from kafka import KafkaProducer

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "creditcard.csv"

TOPIC = "fraud-test-transactions"
KAFKA_SERVER = "localhost:9092"


def main():
    print("Loading transaction dataset...")
    data = pd.read_csv(DATA_PATH)

    # Three legitimate transactions and three known fraudulent ones.
    legitimate = data[data["Class"] == 0].head(3)
    fraudulent = data.loc[[541, 623, 4920]]

    sample = pd.concat([legitimate, fraudulent])

    producer = KafkaProducer(
        bootstrap_servers=KAFKA_SERVER,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )

    try:
        for index, row in sample.iterrows():
            transaction = {
                key: float(value)
                for key, value in row.to_dict().items()
            }

            transaction["transaction_id"] = int(index)

            producer.send(TOPIC, value=transaction).get(timeout=10)

            print(
                f"Sent transaction {index} "
                f"| actual_class={int(row['Class'])}"
            )

            time.sleep(1)

        producer.flush()
        print("Finished sending 6 transactions.")

    finally:
        producer.close()


if __name__ == "__main__":
    main()
