# 🛸 Autonomous Drone Control System

A cloud-native autonomous drone coordination platform where simulated drones make local decisions, coordinate with each other, optimize routes using AI, stream telemetry in real time , operate under intermittent connectivity, and record critical actions on a blockchain for trust and verification.

> Built as a learning project by a first-year BS Data Science student at IIT Madras — documenting the journey of building production-grade distributed systems from scratch.

---

## 🚀 What This System Does

| Capability | Description |
|---|---|
| 🤖 Autonomous decision-making | Each drone makes local decisions independently |
| 🔗 Multi-drone coordination | Drones communicate and coordinate as a swarm |
| 🧠 AI route optimization | Intelligent pathfinding and mission planning |
| 📡 Real-time telemetry | Live fleet data streamed via WebSocket |
| 🌐 Intermittent connectivity | Operates gracefully under network disruptions |
| ⛓️ Blockchain logging | Critical actions recorded for trust and audit |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   Next.js Frontend                   │
│         (HTML Canvas · TypeScript · WebSocket)       │
└─────────────────────┬───────────────────────────────┘
                      │ WebSocket + REST
┌─────────────────────▼───────────────────────────────┐
│                  FastAPI Backend                      │
│           (Python · AsyncIO · WebSocket)             │
├─────────────────────────────────────────────────────┤
│   Simulation Engine  │  Telemetry  │  Coordination  │
└─────────────────────────────────────────────────────┘
```

---

## 📦 Tech Stack

**Backend**
- Python
- FastAPI
- AsyncIO
- WebSocket

**Frontend**
- Next.js
- TypeScript
- HTML Canvas

---

## 📍 Build Phases & Progress

```
Phase 0 — Engineering Foundation         ✅ COMPLETE
Phase 1 — Single Drone Simulation        ✅ COMPLETE
  ├── Drone dataclass model
  ├── Simulation engine (movement + battery drain)
  ├── REST telemetry endpoint  GET /drone/{drone_id}
  ├── WebSocket live fleet stream         /ws
  └── Next.js canvas frontend (live positions)

Phase 2 — Multi-Drone Coordination       🔄 UPCOMING
Phase 3 — AI Route Optimization          🔄 UPCOMING
Phase 4 — Intermittent Connectivity      🔄 UPCOMING
Phase 5 — Blockchain Audit Logging       🔄 UPCOMING
```

---

## ⚡ Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend
```bash
git clone https://github.com/amanthegr8t0-ship-it/autonomous-drone-control
cd autonomous-drone-control/backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the live drone canvas.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/drone/{drone_id}` | Get telemetry for a specific drone |
| WebSocket | `/ws` | Live fleet JSON stream (every 2s) |

---

## 🎯 Why I Built This

Space systems fascinate me — specifically how spacecraft software handles autonomous decision-making, real-time telemetry, and fault-tolerant communication under unreliable conditions.

This project is my way of learning those concepts hands-on. Every phase maps to a real challenge in distributed aerospace systems:
- **Swarm coordination** → satellite constellation management
- **Intermittent connectivity** → deep space communication windows
- **Blockchain logging** → tamper-proof mission audit trails

---

## 📈 Project Status

Actively in development. Follow along as new phases are added.

---

## 👤 Author

**Your Aman Sharma**
BS Data Science — IIT Madras
[LinkedIn](https://linkedin.com/in/aman-sharma-418a34388) · [GitHub](https://github.com/amanthegr8t0-ship-it)
