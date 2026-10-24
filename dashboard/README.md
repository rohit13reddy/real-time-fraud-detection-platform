# Fraud Detection Dashboard

A React-based dashboard for monitoring the Real-Time Fraud Detection Platform.

## Features

- **Live transaction monitoring:** Displays recent transactions and their fraud predictions.
- **Fraud statistics:** Summarizes transaction volume, detected fraud, missed fraud, and false positives.
- **Automatic refresh:** Fetches updated data from the Dashboard API every five seconds.
- **Transaction history:** Displays prediction results, fraud scores, and processing timestamps.

## Tech Stack

- React
- Vite
- FastAPI
- REST API integration

## Run Locally

From the project root, start the full platform:

```bash
./start.sh
```

Open the dashboard in your browser:

http://localhost:5173/

The Dashboard API runs at `http://127.0.0.1:8001`, and its interactive API documentation is available at:

http://127.0.0.1:8001/docs

To stop the application processes:

```bash
./stop.sh
```

For full setup instructions, architecture, model evaluation results, and limitations, see the [main project README](../README.md).
