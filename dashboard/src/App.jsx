
import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8001";

function App() {
  const [stats, setStats] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [statsResponse, transactionsResponse] = await Promise.all([
          fetch(`${API_URL}/stats`),
          fetch(`${API_URL}/transactions?limit=100`),
        ]);

        if (!statsResponse.ok || !transactionsResponse.ok) {
          throw new Error("The dashboard API returned an error.");
        }

        const statsData = await statsResponse.json();
        const transactionsData = await transactionsResponse.json();

        setStats(statsData);
        setTransactions(transactionsData.transactions ?? transactionsData);
        setError("");
      } catch (err) {
        console.error("Dashboard loading error:", err);
        setError(`Dashboard error: ${err.message}`);
      }
    }

    loadDashboard();
    const interval = setInterval(loadDashboard, 5000);

    return () => clearInterval(interval);
  }, []);

  const cards = stats
    ? [
      { label: "Total Transactions", value: stats.total_transactions },
      { label: "Frauds Detected", value: stats.detected_frauds },
      { label: "Missed Frauds", value: stats.missed_frauds },
      { label: "False Positives", value: stats.false_positives },
    ]
    : [];

  return (
    <main className="dashboard">
      <header className="topbar">
        <div>
          <p className="eyebrow">REAL-TIME MONITORING</p>
          <h1>Fraud Detection Platform</h1>
          <p className="subtitle">
            Monitor transaction activity and machine-learning predictions.
          </p>
        </div>
        <div className="live-status">
          <span className="status-dot" />
          API Dashboard
        </div>
      </header>

      {error && <div className="error-message">{error}</div>}

      <section className="stats-grid">
        {cards.map((card) => (
          <article className="stat-card" key={card.label}>
            <p>{card.label}</p>
            <h2>{card.value ?? "—"}</h2>
          </article>
        ))}
      </section>

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>Recent Transactions</h2>
            <p>Latest predictions recorded in the database</p>
          </div>
          <span className="record-count">
            {transactions.length} records
          </span>
        </div>

        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Transaction ID</th>
                <th>Actual Class</th>
                <th>Prediction</th>
                <th>Fraud Score</th>
                <th>Threshold</th>
                <th>Processed At</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((transaction) => (
                <tr key={transaction.id}>
                  <td>#{transaction.transaction_id}</td>
                  <td>
                    {transaction.actual_class === null
                      ? "Unknown"
                      : transaction.actual_class === 1
                        ? "Fraud"
                        : "Legitimate"}
                  </td>
                  <td>
                    <span
                      className={`badge ${transaction.prediction === "fraud"
                          ? "badge-fraud"
                          : "badge-legitimate"
                        }`}
                    >
                      {transaction.prediction}
                    </span>
                  </td>
                  <td>
                    {(transaction.fraud_score * 100).toFixed(2)}%
                  </td>
                  <td>
                    {(transaction.threshold * 100).toFixed(0)}%
                  </td>
                  <td>
                    {transaction.processed_at
                      ? new Date(transaction.processed_at).toLocaleString()
                      : "—"}
                  </td>
                </tr>
              ))}

              {transactions.length === 0 && !error && (
                <tr>
                  <td colSpan="6" className="empty-state">
                    No transactions found in the database.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <footer>
        Fraud Detection Platform · Machine Learning + Kafka + PostgreSQL
      </footer>
    </main>
  );
}

export default App;
