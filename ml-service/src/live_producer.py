import json
import random
import time

import pandas as pd
from kafka import KafkaProducer

DATA_PATH = "ml-service/data/creditcard.csv"
TOPIC = "live-transactions"
BOOTSTRAP_SERVERS = "localhost:9092"

def main():
    print("Loading transaction dataset...")
    data = pd.read_csv(DATA_PATH)

    legitimate = data[data["Class"] == 0]
    fraudulent = data[data["Class"] == 1]

    producer = KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
    )

    print(f"Connected to Kafka. Publishing to '{TOPIC}'.")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            # Use a demo-friendly mix so fraud detections are visible.
            # This deliberately oversamples fraud compared with real life.
            if random.random() < 0.30:
                row = fraudulent.sample(n=1).iloc[0]
            else:
                row = legitimate.sample(n=1).iloc[0]

            record = row.to_dict()
            actual_class = int(record.pop("Class"))

            message = {
                "transaction_id": time.time_ns(),
                "Class": actual_class,
                **{key: float(value) for key, value in record.items()},
            }

            producer.send(TOPIC, value=message)
            producer.flush()

            label = "FRAUD" if actual_class == 1 else "LEGITIMATE"
            print(
                f"Published transaction {message['transaction_id']} "
                f"| actual={label}"
            )

            time.sleep(2)

    except KeyboardInterrupt:
        print("\nStopping transaction producer...")
    finally:
        producer.close()

if __name__ == "__main__":
    main()
