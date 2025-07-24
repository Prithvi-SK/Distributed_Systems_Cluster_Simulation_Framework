# ⚙️ Distributed Systems Cluster Simulation Framework

A lightweight simulation of a Kubernetes-like distributed cluster built with **Flask**, **Docker**, and **HTML**, designed to demonstrate key concepts like **node management**, **pod scheduling**, and **health monitoring**.


---

## 📌 Features

- 🔧 Add Nodes to the cluster (Docker container simulation).
- 🧠 Smart Pod Scheduling using First-Fit / Best-Fit / Worst-Fit.
- 💓 Node Health Monitoring via heartbeat signals.
- 🔄 Automatic Pod Rescheduling on Node Failure.
- 🌐 Web Interface to interact with the cluster.

---

## 🧱 System Architecture

- **Client Interface (HTML + Flask)**  
  Interacts with the cluster via simple web forms and dashboard.

- **API Server (Flask)**  
  Acts as the central controller with:
  - `Node Manager`: Registers and tracks node CPU/resource info.
  - `Pod Scheduler`: Assigns pods to optimal nodes.
  - `Health Monitor`: Detects node failures using heartbeat signals.

- **Nodes (Docker Containers)**  
  Simulated worker nodes that:
  - Maintain a list of pods.
  - Periodically send heartbeats to the API server.

---

## 🛠️ Tech Stack

| Component         | Technology         |
|------------------|--------------------|
| Web Server       | Flask              |
| Frontend         | HTML               |
| Node Simulation  | Docker             |
| Scheduling       | First-Fit, Best-Fit, Worst-Fit |
| Communication    | REST API           |

---

## 🚀 Team
- Prithvi S K
- Rishav Sinha
- Riya Shetty
- Pranay Saxena
