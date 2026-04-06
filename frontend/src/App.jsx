import { useEffect, useMemo, useState } from "react";
import {
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import "./index.css";

const API_BASE = "http://127.0.0.1:5000";

function App() {
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState({
    total_logs: 0,
    recent_allow: 0,
    recent_block: 0,
    recent_alert: 0,
    avg_ai_score: 0,
    ai_threshold: 0.7,
    top_suspicious: null,
  });
  const [autoMode, setAutoMode] = useState(true);
  const [thresholdValue, setThresholdValue] = useState(0.7);

  const fetchData = async () => {
    try {
      const [logsRes, statsRes] = await Promise.all([
        fetch(`${API_BASE}/logs`),
        fetch(`${API_BASE}/stats`),
      ]);

      const logsData = await logsRes.json();
      const statsData = await statsRes.json();

      setLogs(logsData);
      setStats(statsData);
      setThresholdValue(statsData.ai_threshold ?? 0.7);
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 1000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!autoMode) return;

    const interval = setInterval(async () => {
      try {
        const endpoint = Math.random() < 0.75 ? "/inject-normal" : "/inject-attack";
        await fetch(`${API_BASE}${endpoint}`, { method: "POST" });
      } catch (error) {
        console.error("Auto inject failed:", error);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [autoMode]);

  const injectNormal = async () => {
    await fetch(`${API_BASE}/inject-normal`, { method: "POST" });
    fetchData();
  };

  const injectAttack = async () => {
    await fetch(`${API_BASE}/inject-attack`, { method: "POST" });
    fetchData();
  };

  const resetLogs = async () => {
    await fetch(`${API_BASE}/reset-logs`, { method: "POST" });
    fetchData();
  };

  const updateThreshold = async (value) => {
    const num = Number(value);
    setThresholdValue(num);
    await fetch(`${API_BASE}/threshold`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ threshold: num }),
    });
    fetchData();
  };

  const pieData = [
    { name: "ALLOW", value: stats.recent_allow },
    { name: "BLOCK", value: stats.recent_block },
    { name: "ALERT", value: stats.recent_alert },
  ];

  const lineData = logs.map((log, index) => ({
    idx: index + 1,
    ai_score: log.ai_score,
  }));

  const deviceCounts = useMemo(() => {
    const counts = {};
    for (const log of logs) {
      counts[log.device_type] = (counts[log.device_type] || 0) + 1;
    }
    return Object.entries(counts).map(([device, count]) => ({
      device,
      count,
    }));
  }, [logs]);

  return (
    <div className="app">
      <header className="hero">
        <div>
          <h1>SentinelEdge</h1>
          <p>
            Real-time smart-home simulation with threshold tuning, live anomaly
            scoring, and suspicious-event inspection.
          </p>
        </div>
        <div className="hero-actions">
          <button className="btn success" onClick={injectNormal}>Inject Normal</button>
          <button className="btn danger" onClick={injectAttack}>Inject Attack</button>
          <button className="btn dark" onClick={() => setAutoMode((v) => !v)}>
            {autoMode ? "Pause Auto" : "Resume Auto"}
          </button>
          <button className="btn soft" onClick={resetLogs}>Reset Logs</button>
        </div>
      </header>

      <section className="cards">
        <div className="card">
          <h3>Total Events</h3>
          <div className="big">{stats.total_logs}</div>
        </div>
        <div className="card">
          <h3>Recent BLOCK</h3>
          <div className="big danger">{stats.recent_block}</div>
        </div>
        <div className="card">
          <h3>Recent ALERT</h3>
          <div className="big warn">{stats.recent_alert}</div>
        </div>
        <div className="card">
          <h3>Avg AI Score</h3>
          <div className="big">{stats.avg_ai_score}</div>
          <p className="help-text">Average anomaly probability over recent live traffic.</p>
        </div>
      </section>

      <section className="grid">
        <div className="panel">
          <h2>Gateway Decisions</h2>
          <div className="chart">
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" outerRadius={95}>
                  <Cell fill="#22c55e" />
                  <Cell fill="#ef4444" />
                  <Cell fill="#f59e0b" />
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel">
          <h2>AI Score Trend</h2>
          <div className="chart">
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={lineData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="idx" />
                <YAxis domain={[0, 1]} />
                <Tooltip />
                <Line type="monotone" dataKey="ai_score" stroke="#2563eb" strokeWidth={3} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel">
          <h2>Device Activity</h2>
          <div className="chart">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={deviceCounts}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="device" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#6366f1" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel">
          <h2>Threshold Tuning</h2>
          <div className="threshold-box">
            <div className="threshold-value">{thresholdValue.toFixed(2)}</div>
            <input
              type="range"
              min="0.3"
              max="0.95"
              step="0.01"
              value={thresholdValue}
              onChange={(e) => setThresholdValue(Number(e.target.value))}
              onMouseUp={(e) => updateThreshold(e.target.value)}
              onTouchEnd={(e) => updateThreshold(e.target.value)}
            />
            <p className="help-text">
              Lower threshold = more sensitive AI. Higher threshold = fewer alerts.
            </p>
          </div>
        </div>

        <div className="panel full">
          <h2>Top Suspicious Event</h2>
          {stats.top_suspicious ? (
            <div className="top-event">
              <div><strong>Device:</strong> {stats.top_suspicious.device_id}</div>
              <div><strong>Type:</strong> {stats.top_suspicious.device_type}</div>
              <div><strong>Action:</strong> {stats.top_suspicious.action}</div>
              <div><strong>AI Score:</strong> {stats.top_suspicious.ai_score}</div>
              <div><strong>Reason:</strong> {stats.top_suspicious.reasons?.join(", ") || "-"}</div>
            </div>
          ) : (
            <p>No events yet.</p>
          )}
        </div>

        <div className="panel full">
          <h2>Live Security Log</h2>
          <div className="log-table">
            <table>
              <thead>
                <tr>
                  <th>Device</th>
                  <th>Type</th>
                  <th>Action</th>
                  <th>AI</th>
                  <th>Reason</th>
                </tr>
              </thead>
              <tbody>
                {logs.slice().reverse().map((log, index) => (
                  <tr key={`${log.timestamp}-${index}`}>
                    <td>{log.device_id}</td>
                    <td>{log.device_type}</td>
                    <td>
                      <span className={`pill ${log.action.toLowerCase()}`}>{log.action}</span>
                    </td>
                    <td>{log.ai_score}</td>
                    <td>{log.reasons?.join(", ") || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  );
}

export default App;