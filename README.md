# Multimodal Attendance & Engagement Agent
### AI-Powered, Privacy-Preserving Classroom Intelligence System

An offline, edge-deployable multimodal intelligence agent for educational institutions and professional training environments. The system integrates **Computer Vision**, **Audio Signal Processing**, and **Agent-Based Pedagogical Reasoning** to automatically track attendance through sustained presence, evaluate classroom engagement dynamics, and provide real-time decision-support teaching suggestions.

---

## 🚀 Key Architectural Pillars & Scenarios

### 1. Scenario 1: Automated Attendance Tracking via Sustained Presence
- **Continuous Multi-Participant Tracking**: Detects and tracks participants across temporal intervals using OpenCV spatial centroid trackers.
- **Sustained Presence Thresholding**: Rather than marking attendance on a single transient frame, participants must meet a configurable sustained presence threshold ($\ge 60\%-70\%$ of lecture intervals).
- **False-Positive Elimination**: Fleeting appearances (e.g. corridor walkers, visitors opening the door for $< 25\%$ of intervals) are categorized as `FLEETING` rather than recorded as enrolled attendees.
- **Timestamped Audit Logs**: Automatically captures first seen, last seen, detection counts, and exports to CSV / printable PDF reports.

### 2. Scenario 2: Multimodal Engagement & Session Dynamics Analysis
- **Computer Vision Behavioral Signals**:
  - **Head Pose Estimation**: Yaw, pitch, and roll approximation to gauge attention towards the presentation vs downward phone/notebook glances.
  - **Visual Gaze Alignment**: Direct facial and eye orientation tracking.
  - **Drowsiness & Inactivity Analyzer**: Flags continuous downward slump coupled with micro-inactivity.
- **Audio Signal Processing**:
  - **RMS Energy & Envelope**: Live acoustic amplitude and volume levels via Web Audio API.
  - **Interaction Classifier**: Distinguishes instructor monologues from collaborative student debates / Q&A bursts.
  - **Monologue Pacing Timer**: Flags uninterrupted speech when an instructor speaks for $> 12$ minutes without pause.
- **Multimodal Signal Fusion**:
  $$E(t) = 0.35 \cdot \text{Gaze}(t) + 0.25 \cdot \text{HeadPose}(t) + 0.25 \cdot \text{Interaction}(t) - 0.15 \cdot \text{InactivityPenalty}(t)$$
- **Anomaly Detection**: Flags specific timestamps where attention drops ($< 45\%$) or interaction peaks occur ($> 75\%$).
- **Seating Zone Breakdown**: Compares Front Row vs Middle Row vs Back Row engagement levels.

### 3. Scenario 3: AI-Driven Teaching Suggestions (Assistive Decision-Support)
- **Pedagogical Rule & Context Reasoning Engine**:
  - *Monologue Warning*: Prompts a 90-second "Think-Pair-Share" when lecture monologue exceeds 12 minutes.
  - *Attention Drop Alert*: Recommends an immediate formative conceptual check question.
  - *Interaction Peak Synergy*: Advises maintaining discussion flow for 2 minutes before synthesizing on the board.
  - *Seating Zone Disparity*: Alerts when rear rows show lower attention and suggests walking down the aisle.
- **Interactive Offline AI Teaching Copilot**:
  - Assists the educator on-demand with session pacing evaluations, 3 formative check questions, and struggling learner identification.

### 4. 🛡️ 100% Offline & Ethical Deployment Guarantee
- Zero external cloud APIs or data transmission.
- Local feature extraction only; raw video feeds are never permanently stored.
- Built-in Privacy Face Blurring toggle for participant anonymization.

---

## 🛠️ Technology Stack
- **Backend**: Python 3.13, Flask 3.1, OpenCV 5.0 (Haar & Spatial Centroid Tracking), NumPy
- **Frontend**: Vanilla HTML5, CSS3 Glassmorphism with Cyber-Academic Dark Palette, JavaScript ES6
- **Audio & Visual**: HTML5 Canvas, Web Audio API, Chart.js (Bundled locally for 100% offline usage)
- **Storage**: SQLite local database (`classroom_intelligence.db`)

---

## ⚡ Quick Start & Running Locally

1. **Activate Environment and Run**:
```powershell
python app.py
```
2. **Access Dashboard**:
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```
3. **Interactive Features**:
- **Live Console**: Toggle between your physical Webcam or the built-in multi-student classroom simulation demo.
- **Attendance Roster**: View sustained presence calculations, search students, filter by status, and export CSV.
- **Engagement Dynamics**: View the full 50-minute timeline with marked drops and peaks.
- **AI Teaching Suggestions**: Interact with the offline Pedagogical Copilot and review generated real-time interventions.
