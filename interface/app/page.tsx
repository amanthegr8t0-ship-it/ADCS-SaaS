"use client";
import { useState, useEffect, useRef } from "react";

interface Drone {
  id: number;
  x: number;
  y: number;
  battery: number;
  status: string;
}

export default function DroneMap() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [fleet, setFleet] = useState<Drone[]>([]);
  const [activeTab, setActiveTab] = useState("taskSetter");
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

    if (!isReplayMode) {
      // LIVE MODE
      ws = new WebSocket("ws://localhost:8000/ws");
    } else {
      // REPLAY MODE: Only connect if they actually locked in a time
      if (activeReplayTime) {
        ws = new WebSocket(`ws://localhost:8000/ws/replay?topic=drone-telemetry&start_time_ms=${activeReplayTime}`);
      }
    }

    if (ws) {
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setFleet(data);
      };
      
      ws.onopen = () => console.log(isReplayMode ? "Replay WS Connected" : "Live WS Connected");
      ws.onerror = (error) => console.log("WebSocket error", error);
      ws.onopen = () => setWsStatus(isReplayMode ? "Replaying ⏪" : "Live 🟢");
      
      ws.onclose = (event) => {
        setWsStatus(`Disconnected: ${event.reason || "Dropped"}`);
      };
      
      ws.onerror = (error) => {
        console.log("WebSocket error", error);
        setWsStatus("WebSocket Error!");
      };
    }
    
    
    // Proper cleanup that always runs
    return () => {
      if (ws) ws.close();
    };
  }, [isReplayMode, activeReplayTime]);

  useEffect(() => { setIsMounted(true); }, []);

  const maxTime = Date.now();
  const minTime = maxTime-5*60*1000;


  const AssignTask = async () => {
    try {
      if (!droneid || !targetx || !targety) {
    setTrackStatus("Please fill in all fields.");
    return;
}
      const response = await fetch("http://localhost:8000/assign-mission", {
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
        setTrackStatus(data);
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

  return (
    <div style={{ paddingBottom: "100px" }}>
      
      {/* NAVIGATION BAR */}
      <div className="flex justify-center gap-4 p-4 bg-zinc-900 border-b border-zinc-800 shadow-lg">
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
      </div>

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
    </div>
  );
}