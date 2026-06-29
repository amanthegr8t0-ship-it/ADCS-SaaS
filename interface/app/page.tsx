"use client";
export const dynamic = "force-dynamic";
import { useState, useEffect, useRef } from "react";

interface Drone {
  id: number;
  x: number;
  y: number;
  battery: number;
  status: string;
}
interface MissionLog {
  id: number;
  drone_id: number;
  customer_id: string;
  start_x: number;
  start_y: number;
  target_x: number;
  target_y: number;
  distance: number;
  battery_consumed: number;
  eta_seconds: number;
  status: string;
  created_at: string;
}

interface BillingRecord {
  id: number;
  customer_id: string;
  drone_id: number;
  mission_id: number;
  units_consumed: number;
  created_at: string;
}
export default function DroneMap() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [fleet, setFleet] = useState<Drone[]>([]);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [droneid, setDroneid] = useState("");
  const [targetx, setTargetx] = useState("");
  const [targety, setTargety] = useState("");
  const [trackStatus, setTrackStatus] = useState("");
  const [isReplayMode, setIsReplayMode] = useState(false);
  const [replayTimestamp, setReplayTimestamp] = useState(Date.now());
  const [activeReplayTime, setActiveReplayTime] = useState<number | null>(null);
  const [isMounted, setIsMounted] = useState(false);
  const [timeRange, setTimeRange] = useState({ min: 0, max: 0 });
  const [wsStatus, setWsStatus] = useState("Disconnected");
  const [congestionAlerts, setCongestionAlerts] = useState<{id1: number, id2: number, time: number}[]>([]);
  const [lastAlertFetch, setLastAlertFetch] = useState<string>("Never");
  const [missions, setMissions] = useState<MissionLog[]>([]);
  const [billing, setBilling] = useState<BillingRecord[]>([]);
  const [isDbLoading, setIsDbLoading] = useState(false);
  const [category, setCategory] = useState("Light Cargo (5kg)");
  const [quantity, setQuantity] = useState<number>(1);
  const [isSafe, setIsSafe] = useState(false);

  // Auto-fetch from Aurora when tabs are switched
  useEffect(() => {
    if (activeTab === "MissionHistory") {
      setIsDbLoading(true);
      fetch(`/api/missions`)
        .then(res => res.json())
        .then(data => setMissions(data))
        .catch(err => console.error("Mission fetch error:", err))
        .finally(() => setIsDbLoading(false));
    } else if (activeTab === "Billing") {
      setIsDbLoading(true);
      fetch(`/api/billing`)
        .then(res => res.json())
        .then(data => setBilling(data))
        .catch(err => console.error("Billing fetch error:", err))
        .finally(() => setIsDbLoading(false));
    }
  }, [activeTab]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, 800, 600);
    const scaleX = 800 / 200;
    const scaleY = 600 / 200;
    fleet.forEach((drone) => {
      ctx.beginPath();
      ctx.arc(drone.x * scaleX, drone.y * scaleY, 8, 0, Math.PI * 2);
      ctx.fillStyle = "lime";
      ctx.fill();
    });
  }, [fleet]);

useEffect(() => {
    let ws: WebSocket | null = null;

    try {
      if (!isReplayMode) {
        ws = new WebSocket(`ws://13.220.128.77:8000/ws`);
      } else {
        if (activeReplayTime) {
          ws = new WebSocket(`ws://13.220.128.77:8000/ws/replay?topic=drone-telemetry&start_time_ms=${activeReplayTime}`);
        }
      }
    } catch (e) {
      console.warn("WebSocket blocked (mixed content):", e);
      setWsStatus("WS unavailable (HTTPS)");
    }

    if (ws) {
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setFleet(data);
      };
      
      ws.onopen = () => setWsStatus(isReplayMode ? "Replaying ⏪" : "Live 🟢");
      
      ws.onclose = (event) => {
        setWsStatus(`Disconnected: ${event.reason || "Dropped"}`);
      };
      
      ws.onerror = (error) => {
        console.log("WebSocket error", error);
        setWsStatus("WS unavailable (HTTPS)");
      };
    }

    return () => {
      if (ws) ws.close();
    };
  }, [isReplayMode, activeReplayTime]);

  useEffect(() => { 
  setIsMounted(true);
  setIsSafe(true);
}, []);

  const maxTime = Date.now();
  const minTime = maxTime-5*60*1000;

  useEffect(() => {
  const fetchAlerts = async () => {
    try {
      const res = await fetch(`/api/predict-congestion`);
      const data = await res.json();
      setCongestionAlerts(Array.isArray(data) ? data : data.predictions ?? []);
      setLastAlertFetch(new Date().toLocaleTimeString());
    } catch (e) {
      console.error("Alert fetch failed", e);
    }
  };

  fetchAlerts();
  const interval = setInterval(fetchAlerts, 3000);
  return () => clearInterval(interval);
}, []);


  const AssignTask = async () => {
    try {
      if (!droneid || !targetx || !targety) {
    setTrackStatus("Please fill in all fields.");
    return;
}
      const response = await fetch(`/api/assign-mission`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          Droneid: parseInt(droneid),
          tarx: parseFloat(targetx),
          tary: parseFloat(targety),
        }),
      });
      if (response.ok) {
        const data = await response.json();
        setTrackStatus(typeof data === "string" ? data : data.detail || JSON.stringify(data));
        setDroneid("");
        setTargetx("");
        setTargety("");
      } else {
        const err = await response.json();
        setTrackStatus(`Failed: ${err.detail}`);
      }
    } catch (e) {
      console.error(e);
      setTrackStatus("Error connecting to server.");
    }
    ; // <-- These dependencies trigger the rebuild
  };

if (!isSafe) return null;

return (
  <div style={{ paddingBottom: "100px" }}>
      
      {/* NAVIGATION BAR */}
      <div className="flex justify-center gap-4 p-4 bg-zinc-900 border-b border-zinc-800 shadow-lg">
      <button
          onClick={() => setActiveTab("dashboard")}
          className={`px-6 py-2 rounded-full font-semibold transition-all ${activeTab === "dashboard" ? "bg-violet-600 text-white shadow-lg shadow-violet-500/30" : "bg-zinc-800 text-zinc-400 hover:text-white"}`}
        >
          📊 Dashboard
        </button>
        <button 
          onClick={() => setActiveTab("taskSetter")}
          className={`px-6 py-2 rounded-full font-semibold transition-all ${activeTab === "taskSetter" ? "bg-blue-600 text-white shadow-lg shadow-blue-500/30" : "bg-zinc-800 text-zinc-400 hover:text-white"}`}
        >
          🎯 Task Setter
        </button>
        <button 
          onClick={() => setActiveTab("Map")}
          className={`px-6 py-2 rounded-full font-semibold transition-all ${activeTab === "Map" ? "bg-emerald-600 text-white shadow-lg shadow-emerald-500/30" : "bg-zinc-800 text-zinc-400 hover:text-white"}`}
        >
          🗺️ Live Map
        </button>
        <button 
          onClick={() => setActiveTab("MissionHistory")}
          className={`px-6 py-2 rounded-full font-semibold transition-all ${activeTab === "MissionHistory" ? "bg-amber-600 text-white shadow-lg shadow-amber-500/30" : "bg-zinc-800 text-zinc-400 hover:text-white"}`}
        >
          📜 Mission History
        </button>
        <button 
          onClick={() => setActiveTab("Billing")}
          className={`px-6 py-2 rounded-full font-semibold transition-all ${activeTab === "Billing" ? "bg-rose-600 text-white shadow-lg shadow-rose-500/30" : "bg-zinc-800 text-zinc-400 hover:text-white"}`}
        >
          💳 Billing
        </button>
      </div>
      {activeTab === "dashboard" && (
  <div className="max-w-5xl mx-auto mt-8 px-4 flex flex-col gap-6">

    {/* KPI Cards */}
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
      {[
        {
          label: "Total Drones",
          value: fleet.length,
          color: "text-blue-400",
          bg: "bg-blue-500/10 border-blue-500/20",
        },
        {
          label: "On Air",
          value: fleet.filter(d => d.status === "On Air").length,
          color: "text-emerald-400",
          bg: "bg-emerald-500/10 border-emerald-500/20",
        },
        {
          label: "Landed",
          value: fleet.filter(d => d.status === "Landed" || d.status === "idle").length,
          color: "text-zinc-400",
          bg: "bg-zinc-500/10 border-zinc-500/20",
        },
        {
          label: "Low Battery",
          value: fleet.filter(d => d.battery < 20).length,
          color: "text-red-400",
          bg: "bg-red-500/10 border-red-500/20",
        },
      ].map(card => (
        <div key={card.label} className={`rounded-xl border p-5 ${card.bg} flex flex-col gap-1`}>
          <span className="text-zinc-500 text-xs uppercase tracking-widest font-semibold">{card.label}</span>
          <span className={`text-4xl font-bold ${card.color}`}>{card.value}</span>
        </div>
      ))}
    </div>

    {/* Collision Alerts */}
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-white font-bold text-lg">⚠️ Collision Alerts</h3>
        <span className="text-zinc-600 text-xs">Last checked: {lastAlertFetch}</span>
      </div>
      {congestionAlerts.length === 0 ? (
        <div className="text-emerald-400 font-semibold text-sm bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-4 py-3">
          ✅ All clear — no collision risks detected
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {congestionAlerts.map((alert, i) => (
            <div key={i} className="flex justify-between items-center bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3">
              <span className="text-red-400 font-bold">
                Drone {alert.id1} ↔ Drone {alert.id2}
              </span>
              <span className="text-zinc-400 text-xs font-mono">
                at t={alert.time}s
              </span>
            </div>
          ))}
        </div>
      )}
    </div>

    {/* Fleet Status Cards */}
    <div className="bg-zinc-900 rounded-xl border border-zinc-800 p-6">
      <h3 className="text-white font-bold text-lg mb-4">🛸 Fleet Status</h3>
      {fleet.length === 0 ? (
        <p className="text-zinc-500 text-sm">Waiting for telemetry...</p>
      ) : (
        <div className="flex flex-col gap-3">
          {fleet.map(drone => (
            <div key={drone.id} className="flex items-center justify-between p-4 bg-zinc-950 rounded-lg border border-zinc-800">
              <span className="font-bold text-white w-20">Drone {drone.id}</span>

              {/* Battery bar */}
              <div className="flex items-center gap-2 w-36">
                <div className="w-24 h-2 bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${drone.battery}%`,
                      backgroundColor: drone.battery > 50 ? "#10b981" : drone.battery > 20 ? "#f59e0b" : "#ef4444"
                    }}
                  />
                </div>
                <span className={`text-xs font-mono font-bold ${drone.battery > 50 ? "text-emerald-400" : drone.battery > 20 ? "text-yellow-400" : "text-red-400"}`}>
                  {drone.battery.toFixed(1)}%
                </span>
              </div>

              <span className="text-zinc-400 font-mono text-sm">
                ({drone.x.toFixed(1)}, {drone.y.toFixed(1)})
              </span>

              <span className={`text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full border ${
                drone.status === "On Air"
                  ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/30"
                  : "text-zinc-400 bg-zinc-800 border-zinc-700"
              }`}>
                {drone.status}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>

  </div>
)}
      {activeTab === "taskSetter" && (
        <div className="max-w-3xl mx-auto mt-10 p-8 bg-zinc-900 rounded-xl border border-zinc-800 shadow-2xl">
          <h2 className="text-2xl font-bold mb-6 text-white flex items-center gap-2">
            🚀 Mission Control
          </h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            <input className="px-4 py-3 bg-zinc-950 text-white rounded-lg border border-zinc-700 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all" value={droneid} onChange={(e) => setDroneid(e.target.value)} placeholder="Drone ID" type="number" />
            <input className="px-4 py-3 bg-zinc-950 text-white rounded-lg border border-zinc-700 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all" value={targetx} onChange={(e) => setTargetx(e.target.value)} placeholder="Target X" type="number" />
            <input className="px-4 py-3 bg-zinc-950 text-white rounded-lg border border-zinc-700 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all" value={targety} onChange={(e) => setTargety(e.target.value)} placeholder="Target Y" type="number" />
          </div>
          
          <button 
            className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg transition-all shadow-[0_0_20px_rgba(37,99,235,0.3)]"
            onClick={AssignTask}
          >
            Assign Coordinates
          </button>
          
          {trackStatus && (
            <div className="mt-4 p-4 bg-zinc-950 border border-blue-900/50 text-blue-400 rounded-lg text-center font-mono">
             {trackStatus}
            </div>
          )}

          <div className="mt-10 space-y-3">
            <h3 className="text-lg font-semibold text-zinc-400 border-b border-zinc-800 pb-2 mb-4">Active Fleet Status</h3>
            {fleet.map((drone) => (
              <div key={drone.id} className="flex justify-between items-center p-4 bg-zinc-950 rounded-lg border border-zinc-800 hover:border-zinc-700 transition-colors">
                <span className="font-bold text-white">Drone {drone.id}</span>
                <span className={`px-3 py-1 rounded-full text-xs font-bold ${drone.battery > 20 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
                  🔋 {drone.battery.toFixed(1)}%
                </span>
                <span className="text-zinc-400 font-mono text-sm bg-zinc-900 px-3 py-1 rounded">X: {drone.x.toFixed(1)} | Y: {drone.y.toFixed(1)}</span>
                <span className="text-blue-400 text-sm uppercase tracking-wider font-bold w-20 text-right">{drone.status}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "Map" && (
        <div className="max-w-4xl mx-auto mt-8">
          
          {/* Controls Panel */}
          <div className="bg-zinc-900 p-6 rounded-t-xl border-x border-t border-zinc-800 flex flex-col gap-4 shadow-xl">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-3">
                <span className="text-zinc-500 font-bold uppercase tracking-wider text-xs">Uplink Status</span>
                <span className={`px-4 py-1.5 rounded-full text-sm font-bold shadow-inner ${wsStatus.includes("Live") ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30" : wsStatus.includes("Replaying") ? "bg-purple-500/10 text-purple-400 border border-purple-500/30" : "bg-red-500/10 text-red-400 border border-red-500/30"}`}>
                  {wsStatus}
                </span>
              </div>
              
              <button 
                className={`px-6 py-2.5 rounded-lg font-bold transition-all shadow-lg ${isReplayMode ? "bg-zinc-800 hover:bg-zinc-700 text-white border border-zinc-700" : "bg-purple-600 hover:bg-purple-500 text-white shadow-purple-500/20"}`}
                onClick={() => {
                  const nextMode = !isReplayMode;
                  setIsReplayMode(nextMode);
                  if (nextMode) {
                    const now = Date.now();
                    setTimeRange({ min: now - 5 * 60 * 1000, max: now });
                    setReplayTimestamp(now - 60000); 
                  } else {
                    setActiveReplayTime(null); 
                  }
                }}
              >
                {isReplayMode ? "🔴 Return to Live Feed" : "⏪ Access Flight Logs"}
              </button>
            </div>

            {isMounted && isReplayMode && (
              <div className="bg-zinc-950 p-5 rounded-lg border border-purple-500/20 mt-2">
                <div className="flex justify-between text-zinc-500 text-xs font-bold uppercase tracking-wider mb-3">
                  <span>-5 Minutes</span>
                  <span className="text-purple-400 font-mono bg-purple-500/10 px-3 py-1 rounded">Target: {new Date(replayTimestamp).toLocaleTimeString()}</span>
                  <span>Present</span>
                </div>
                
                <input 
                  type="range" 
                  min={timeRange.min} 
                  max={timeRange.max} 
                  value={replayTimestamp}
                  onChange={(e) => setReplayTimestamp(parseInt(e.target.value))}
                  className="w-full accent-purple-500 cursor-pointer h-2 bg-zinc-800 rounded-lg appearance-none mb-5"
                />
                
                <button 
                  className="w-full py-2.5 bg-purple-600/20 hover:bg-purple-600/40 text-purple-300 font-bold rounded-lg border border-purple-500/30 transition-all flex justify-center items-center gap-2"
                  onClick={() => setActiveReplayTime(replayTimestamp)}
                >
                  ▶️ Stream from selected timestamp
                </button>
              </div>
            )}
          </div>

          {/* Canvas Wrapper */}
          <div className="bg-zinc-950 p-6 rounded-b-xl border border-zinc-800 shadow-2xl flex justify-center relative">
            <canvas 
              ref={canvasRef} 
              width={800} 
              height={600} 
              className="rounded-lg shadow-[0_0_50px_rgba(16,185,129,0.05)] border border-zinc-800/80 bg-black" 
            />
          </div>
        </div>
      )}
      {/* MISSION HISTORY TAB */}
      {activeTab === "MissionHistory" && (
        <div className="max-w-6xl mx-auto mt-8 px-4">
          <div className="bg-zinc-900 rounded-xl border border-zinc-800 shadow-2xl overflow-hidden">
            <div className="p-6 border-b border-zinc-800 flex justify-between items-center">
              <h2 className="text-xl font-bold text-white">📜 Mission Log (Aurora RDS)</h2>
              {isDbLoading && <span className="text-amber-400 text-sm font-mono animate-pulse">Syncing...</span>}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-zinc-400">
                <thead className="bg-zinc-950 text-xs uppercase text-zinc-500 border-b border-zinc-800">
                  <tr>
                    <th className="px-6 py-4 font-semibold">ID</th>
                    <th className="px-6 py-4 font-semibold">Drone</th>
                    <th className="px-6 py-4 font-semibold">Route (Start → Target)</th>
                    <th className="px-6 py-4 font-semibold">Distance</th>
                    <th className="px-6 py-4 font-semibold">ETA / Bat. Cost</th>
                    <th className="px-6 py-4 font-semibold">Status</th>
                    <th className="px-6 py-4 font-semibold">Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {missions.length === 0 && !isDbLoading ? (
                    <tr><td colSpan={7} className="text-center py-8">No missions logged yet.</td></tr>
                  ) : (
                    missions.map((m) => (
                      <tr key={m.id} className="border-b border-zinc-800/50 hover:bg-zinc-800/50 transition-colors">
                        <td className="px-6 py-4 font-mono text-white">#{m.id}</td>
                        <td className="px-6 py-4 font-bold text-blue-400">D-{m.drone_id}</td>
                        <td className="px-6 py-4 font-mono text-xs">
                          ({m.start_x}, {m.start_y}) → ({m.target_x}, {m.target_y})
                        </td>
                        <td className="px-6 py-4">{m.distance.toFixed(1)} m</td>
                        <td className="px-6 py-4">{m.eta_seconds}s / {m.battery_consumed.toFixed(1)}%</td>
                        <td className="px-6 py-4">
                          <span className="px-2 py-1 rounded-full text-[10px] uppercase font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">{m.status}</span>
                        </td>
                        <td className="px-6 py-4 text-xs">{new Date(m.created_at).toLocaleString()}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* BILLING TAB */}
      {activeTab === "Billing" && (
        <div className="max-w-5xl mx-auto mt-8 px-4">
          <div className="bg-zinc-900 rounded-xl border border-zinc-800 shadow-2xl overflow-hidden">
            <div className="p-6 border-b border-zinc-800 flex justify-between items-center">
              <h2 className="text-xl font-bold text-white">💳 Billing Ledger (Aurora RDS)</h2>
              {isDbLoading && <span className="text-rose-400 text-sm font-mono animate-pulse">Syncing...</span>}
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-zinc-400">
                <thead className="bg-zinc-950 text-xs uppercase text-zinc-500 border-b border-zinc-800">
                  <tr>
                    <th className="px-6 py-4 font-semibold">Bill ID</th>
                    <th className="px-6 py-4 font-semibold">Mission ID</th>
                    <th className="px-6 py-4 font-semibold">Drone</th>
                    <th className="px-6 py-4 font-semibold">Customer</th>
                    <th className="px-6 py-4 font-semibold">Units Consumed</th>
                    <th className="px-6 py-4 font-semibold">Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {billing.length === 0 && !isDbLoading ? (
                    <tr><td colSpan={6} className="text-center py-8">No billing records found.</td></tr>
                  ) : (
                    billing.map((b) => (
                      <tr key={b.id} className="border-b border-zinc-800/50 hover:bg-zinc-800/50 transition-colors">
                        <td className="px-6 py-4 font-mono text-white">#{b.id}</td>
                        <td className="px-6 py-4 font-mono text-zinc-500">#{b.mission_id}</td>
                        <td className="px-6 py-4 font-bold text-blue-400">D-{b.drone_id}</td>
                        <td className="px-6 py-4 font-mono text-xs">{b.customer_id}</td>
                        <td className="px-6 py-4 font-bold text-rose-400">{b.units_consumed.toFixed(4)}</td>
                        <td className="px-6 py-4 text-xs">{new Date(b.created_at).toLocaleString()}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}