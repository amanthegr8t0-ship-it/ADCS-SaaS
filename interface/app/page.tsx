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

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws");
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setFleet(data);
    };
    ws.onopen = () => console.log("WebSocket connected");
    ws.onerror = (error) => console.log("WebSocket error", error);
    ws.onclose = (event) => console.log("WebSocket closed", event.code, event.reason);
  }, []);

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
  };

  return (
    <div>
      <div>
        <button onClick={() => setActiveTab("taskSetter")}>Task Setter</button>
        <button onClick={() => setActiveTab("Map")}>Map</button>
      </div>

      {activeTab === "taskSetter" && (
        <div>
          <input value={droneid} onChange={(e) => setDroneid(e.target.value)} placeholder="Enter Drone ID" />
          <input value={targetx} onChange={(e) => setTargetx(e.target.value)} placeholder="Enter target X" />
          <input value={targety} onChange={(e) => setTargety(e.target.value)} placeholder="Enter target Y" />
          <button onClick={AssignTask}>Assign Mission</button>
          {trackStatus && <p>{trackStatus}</p>}
          <div>
            {fleet.map((drone) => (
              <div key={drone.id}>
                Drone {drone.id} | Battery: {drone.battery.toFixed(1)}% | X: {drone.x.toFixed(1)} | Y: {drone.y.toFixed(1)} | {drone.status}
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "Map" && (
        <canvas ref={canvasRef} width={800} height={600} />
      )}
    </div>
  );
}