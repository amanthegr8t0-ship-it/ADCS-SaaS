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
}, []);

useEffect(() => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.clearRect(0, 0, 800, 600);
        fleet.forEach((drone) => {
            ctx.beginPath();
            ctx.arc(drone.x * 4, drone.y * 4, 8, 0, Math.PI * 2);
            ctx.fillStyle = "lime";
            ctx.fill();
});
    },
 [fleet]);
  
return(
  <canvas ref={canvasRef} width={800} height={600} />
)
}