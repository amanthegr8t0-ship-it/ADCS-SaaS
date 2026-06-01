"use client";
import { useState, useEffect, useRef, } from "react";

interface Drone {
  id: number;
  x: number;
  y: number;
  battery: number;
  status: string;
}

export default function DroneMap() {

const canvasRef = useRef<HTMLCanvasElement>(null);
const [fleet, setFleet] = useState<Drone[]>([])

useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws");
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data);
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
    },
 [fleet]);
  
return(
  <canvas ref={canvasRef} width={800} height={600} />
)
}