/**
 * Camera Stream & Frame Pipeline Controller
 * Manages live webcam capture, simulation demo mode, frame transmission to Flask,
 * and HUD visualizer rendering.
 */

class CameraStreamManager {
  constructor(videoElementId, overlayCanvasId, audioMonitor) {
    this.video = document.getElementById(videoElementId);
    this.canvas = document.getElementById(overlayCanvasId);
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    this.audioMonitor = audioMonitor;
    
    this.stream = null;
    this.isStreaming = false;
    this.isSimulationMode = false;
    this.simScenario = 'normal'; // 'normal', 'monologue_drop', 'interactive_peak', 'drowsiness'
    this.simStep = 0;
    
    this.processInterval = null;
    this.fps = 2; // Process 2-3 frames per second for lightweight real-time responsiveness
    this.isProcessing = false;
  }
  
  async startWebcam() {
    this.isSimulationMode = false;
    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        this.stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 640 }, height: { ideal: 480 } },
          audio: false
        });
        this.video.srcObject = this.stream;
        await this.video.play();
        this.isStreaming = true;
        
        this.startProcessingLoop();
        this.updateBadge('WEBCAM: LIVE', 'present');
      } else {
        throw new Error('getUserMedia not supported');
      }
    } catch (err) {
      console.warn('Cannot open webcam, falling back to simulated classroom feed:', err);
      this.startSimulation('normal');
    }
  }
  
  startSimulation(scenario = 'normal') {
    this.isSimulationMode = true;
    this.simScenario = scenario;
    this.isStreaming = true;
    
    // Hide webcam video element if no real feed
    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
      this.video.srcObject = null;
    }
    
    this.startProcessingLoop();
    this.updateBadge(`SIMULATION: ${scenario.toUpperCase().replace('_', ' ')}`, 'late');
  }
  
  stop() {
    this.isStreaming = false;
    if (this.processInterval) clearInterval(this.processInterval);
    if (this.stream) {
      this.stream.getTracks().forEach(t => t.stop());
    }
    this.updateBadge('SYSTEM: PAUSED', 'fleeting');
  }
  
  startProcessingLoop() {
    if (this.processInterval) clearInterval(this.processInterval);
    this.processInterval = setInterval(() => this.tick(), 1000 / this.fps);
  }
  
  async tick() {
    if (!this.isStreaming || this.isProcessing) return;
    this.isProcessing = true;
    
    try {
      const audioMetrics = this.audioMonitor ? this.audioMonitor.getMetrics() : { volume: 0.2, rms: 0.15, speech_ratio: 0.3 };
      
      if (this.isSimulationMode) {
        this.simStep += 1;
        const res = await fetch('/api/simulation/step', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            scenario: this.simScenario,
            step: this.simStep
          })
        });
        const data = await res.json();
        this.renderSimulationCanvas(data.detections);
        this.handleServerResponse(data);
      } else {
        // Real webcam frame capture
        if (this.video.readyState >= 2) {
          const offCanvas = document.createElement('canvas');
          offCanvas.width = this.video.videoWidth || 640;
          offCanvas.height = this.video.videoHeight || 480;
          const offCtx = offCanvas.getContext('2d');
          
          // Mirror frame if needed
          offCtx.translate(offCanvas.width, 0);
          offCtx.scale(-1, 1);
          offCtx.drawImage(this.video, 0, 0, offCanvas.width, offCanvas.height);
          
          const frameB64 = offCanvas.toDataURL('image/jpeg', 0.65);
          
          const res = await fetch('/api/process_frame', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              image: frameB64,
              audio_volume: audioMetrics.volume,
              audio_rms: audioMetrics.rms,
              speech_ratio: audioMetrics.speech_ratio
            })
          });
          
          const data = await res.json();
          if (data.annotated_image && this.ctx) {
            // Draw annotated image returned from OpenCV
            const img = new Image();
            img.onload = () => {
              this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
              this.ctx.drawImage(img, 0, 0, this.canvas.width, this.canvas.height);
            };
            img.src = data.annotated_image;
          }
          this.handleServerResponse(data);
        }
      }
    } catch (err) {
      console.error('Frame processing tick error:', err);
    } finally {
      this.isProcessing = false;
    }
  }
  
  renderSimulationCanvas(detections) {
    if (!this.ctx || !this.canvas) return;
    const w = this.canvas.width;
    const h = this.canvas.height;
    
    // Draw stylish classroom floor grid background
    this.ctx.fillStyle = '#080c14';
    this.ctx.fillRect(0, 0, w, h);
    
    // Subtle perspective grid
    this.ctx.strokeStyle = 'rgba(99, 102, 241, 0.08)';
    this.ctx.lineWidth = 1;
    for (let x = 0; x < w; x += 40) {
      this.ctx.beginPath();
      this.ctx.moveTo(x, 0);
      this.ctx.lineTo(x, h);
      this.ctx.stroke();
    }
    for (let y = 0; y < h; y += 30) {
      this.ctx.beginPath();
      this.ctx.moveTo(0, y);
      this.ctx.lineTo(w, y);
      this.ctx.stroke();
    }
    
    // Draw lecture board banner at top
    this.ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
    this.ctx.fillRect(40, 15, w - 80, 36);
    this.ctx.strokeStyle = 'rgba(56, 189, 248, 0.3)';
    this.ctx.strokeRect(40, 15, w - 80, 36);
    this.ctx.fillStyle = '#38bdf8';
    this.ctx.font = '600 13px Outfit, sans-serif';
    this.ctx.fillText("LECTURE HALL 402 • MULTIMODAL AUDIENCE TRACKING", 55, 38);
    
    // Draw simulated student avatars & HUD brackets
    if (!detections) return;
    detections.forEach((d, idx) => {
      const [bx, by, bw, bh] = d.bbox;
      // Scale coordinates to current canvas
      const sx = (bx / 640) * w;
      const sy = (by / 480) * h;
      const sw = (bw / 640) * w;
      const sh = (bh / 480) * h;
      
      const isDrowsy = d.is_drowsy;
      const eng = d.visual_engagement;
      const color = isDrowsy ? '#ef4444' : (eng >= 0.70 ? '#10b981' : (eng >= 0.45 ? '#38bdf8' : '#f59e0b'));
      
      // Avatar placeholder
      this.ctx.fillStyle = 'rgba(30, 41, 59, 0.8)';
      this.ctx.beginPath();
      this.ctx.arc(sx + sw/2, sy + sh/2, sw/2.2, 0, Math.PI * 2);
      this.ctx.fill();
      
      // Face circle outline
      this.ctx.strokeStyle = color;
      this.ctx.lineWidth = 2;
      this.ctx.stroke();
      
      // Head orientation indicator
      this.ctx.fillStyle = color;
      const gazeOffset = (d.gaze_score - 0.5) * 10;
      this.ctx.beginPath();
      this.ctx.arc(sx + sw/2 + gazeOffset, sy + sh/2 - (isDrowsy ? -4 : 4), 3, 0, Math.PI * 2);
      this.ctx.fill();
      
      // HUD brackets
      const len = sw * 0.25;
      this.ctx.strokeStyle = color;
      this.ctx.lineWidth = 2;
      // Top-left
      this.ctx.beginPath();
      this.ctx.moveTo(sx, sy + len);
      this.ctx.lineTo(sx, sy);
      this.ctx.lineTo(sx + len, sy);
      this.ctx.stroke();
      // Top-right
      this.ctx.beginPath();
      this.ctx.moveTo(sx + sw - len, sy);
      this.ctx.lineTo(sx + sw, sy);
      this.ctx.lineTo(sx + sw, sy + len);
      this.ctx.stroke();
      // Bottom-left
      this.ctx.beginPath();
      this.ctx.moveTo(sx, sy + sh - len);
      this.ctx.lineTo(sx, sy + sh);
      this.ctx.lineTo(sx + len, sy + sh);
      this.ctx.stroke();
      // Bottom-right
      this.ctx.beginPath();
      this.ctx.moveTo(sx + sw - len, sy + sh);
      this.ctx.lineTo(sx + sw, sy + sh);
      this.ctx.lineTo(sx + sw, sy + sh - len);
      this.ctx.stroke();
      
      // Badge label
      const badgeText = isDrowsy ? `DROWSY` : `${Math.round(eng * 100)}% Engaged`;
      this.ctx.font = '600 10px JetBrains Mono, monospace';
      const tw = this.ctx.measureText(badgeText).width;
      
      this.ctx.fillStyle = 'rgba(10, 15, 25, 0.9)';
      this.ctx.fillRect(sx, sy - 18, tw + 10, 15);
      this.ctx.strokeStyle = color;
      this.ctx.lineWidth = 1;
      this.ctx.strokeRect(sx, sy - 18, tw + 10, 15);
      
      this.ctx.fillStyle = '#ffffff';
      this.ctx.fillText(badgeText, sx + 5, sy - 6);
    });
  }
  
  handleServerResponse(data) {
    if (!data) return;
    
    // Update live metrics on dashboard
    const fusion = data.fusion || {};
    const snap = fusion.snapshot || {};
    const rosterSum = fusion.roster_summary || {};
    
    // 1. Update Circular Gauge
    const compScore = snap.composite_engagement || 70;
    const gaugeEl = document.getElementById('liveEngagementVal');
    const gaugeCircle = document.getElementById('gaugeProgressCircle');
    if (gaugeEl) gaugeEl.textContent = Math.round(compScore);
    if (gaugeCircle) {
      // Circumference = 2 * PI * 65 ≈ 408
      const offset = 408 - (408 * (compScore / 100));
      gaugeCircle.style.strokeDashoffset = offset;
    }
    
    // 2. Update Metric Stat Cards
    const faceCntEl = document.getElementById('activeFacesCount');
    if (faceCntEl) faceCntEl.textContent = snap.active_faces || 0;
    
    const gazeScoreEl = document.getElementById('avgGazeVal');
    if (gazeScoreEl) gazeScoreEl.textContent = `${Math.round(snap.gaze_attention || 75)}%`;
    
    const poseScoreEl = document.getElementById('avgPoseVal');
    if (poseScoreEl) poseScoreEl.textContent = `${Math.round(snap.head_pose_alignment || 80)}%`;
    
    const interactEl = document.getElementById('interactionIndexVal');
    if (interactEl) interactEl.textContent = `${Math.round(snap.interaction_index || 30)}%`;
    
    const drowsinessEl = document.getElementById('drowsinessCountVal');
    if (drowsinessEl) drowsinessEl.textContent = snap.drowsiness_count || 0;
    
    // 3. Update Attendance Counter
    const presCntEl = document.getElementById('presentCountBadge');
    if (presCntEl) presCntEl.textContent = `${rosterSum.present_count || 0} / ${rosterSum.total_enrolled || 14}`;
    
    const sustainedRateEl = document.getElementById('sustainedRateBadge');
    if (sustainedRateEl) sustainedRateEl.textContent = `${rosterSum.sustained_presence_rate || 0}%`;
    
    // 4. Append any new AI suggestions to the feed
    if (data.new_suggestions && data.new_suggestions.length > 0 && window.AiAgentManager) {
      data.new_suggestions.forEach(s => window.AiAgentManager.addSuggestion(s));
    }
    
    // 5. Update timeline chart
    if (window.TimelineChart && snap.timestamp) {
      window.TimelineChart.addDataPoint(snap);
    }
  }
  
  updateBadge(text, className) {
    const badge = document.getElementById('cameraStatusBadge');
    if (badge) {
      badge.textContent = text;
      badge.className = `status-tag ${className}`;
    }
  }
}

window.CameraStreamManager = CameraStreamManager;
