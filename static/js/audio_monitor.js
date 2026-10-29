/**
 * Multimodal Audio Signal Processor & Waveform Visualizer
 * Analyzes microphone input, calculates RMS energy, speech frequency envelope,
 * and renders animated waveform oscilloscope on canvas.
 */

class AudioMonitor {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
    
    this.audioCtx = null;
    this.analyser = null;
    this.source = null;
    this.stream = null;
    this.animationId = null;
    
    this.isRunning = false;
    this.isMicActive = false;
    
    // Telemetry state
    this.volume = 0.15;
    this.rms = 0.12;
    this.speechRatio = 0.25;
    this.simulatedTime = 0;
  }
  
  async start() {
    this.isRunning = true;
    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        this.stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
        this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        this.analyser = this.audioCtx.createAnalyser();
        this.analyser.fftSize = 512;
        this.analyser.smoothingTimeConstant = 0.8;
        
        this.source = this.audioCtx.createMediaStreamSource(this.stream);
        this.source.connect(this.analyser);
        this.isMicActive = true;
        
        const badge = document.getElementById('micStatusBadge');
        if (badge) {
          badge.textContent = 'MIC: LIVE';
          badge.className = 'status-tag present';
        }
      } else {
        throw new Error('Web Audio not available');
      }
    } catch (err) {
      console.warn('Microphone permission not granted or device not found. Using simulated audio processor.', err);
      this.isMicActive = false;
      const badge = document.getElementById('micStatusBadge');
      if (badge) {
        badge.textContent = 'MIC: SIMULATED';
        badge.className = 'status-tag late';
      }
    }
    
    this.renderWaveform();
  }
  
  stop() {
    this.isRunning = false;
    if (this.animationId) cancelAnimationFrame(this.animationId);
    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
    }
    if (this.audioCtx && this.audioCtx.state !== 'closed') {
      this.audioCtx.close();
    }
  }
  
  getMetrics() {
    if (this.isMicActive && this.analyser) {
      const buffer = new Float32Array(this.analyser.fftSize);
      this.analyser.getFloatTimeDomainData(buffer);
      
      // Calculate RMS
      let sum = 0;
      for (let i = 0; i < buffer.length; i++) {
        sum += buffer[i] * buffer[i];
      }
      this.rms = Math.min(1.0, Math.sqrt(sum / buffer.length) * 3.5);
      this.volume = this.rms;
      this.speechRatio = this.rms > 0.15 ? 0.8 : 0.1;
    } else {
      // Smooth realistic synthesized audio fluctuations
      this.simulatedTime += 0.05;
      const wave = (Math.sin(this.simulatedTime) + Math.cos(this.simulatedTime * 2.3) + 2) / 4;
      this.rms = Math.max(0.08, Math.min(0.85, wave * 0.5 + (Math.random() * 0.1)));
      this.volume = this.rms;
      this.speechRatio = this.rms > 0.20 ? 0.75 : 0.15;
    }
    
    return {
      volume: parseFloat(this.volume.toFixed(3)),
      rms: parseFloat(this.rms.toFixed(3)),
      speech_ratio: parseFloat(this.speechRatio.toFixed(3))
    };
  }
  
  renderWaveform() {
    if (!this.isRunning || !this.ctx || !this.canvas) return;
    
    const width = this.canvas.width;
    const height = this.canvas.height;
    
    this.ctx.fillStyle = 'rgba(10, 13, 20, 0.4)';
    this.ctx.fillRect(0, 0, width, height);
    
    this.ctx.lineWidth = 2;
    this.ctx.strokeStyle = '#38bdf8';
    this.ctx.beginPath();
    
    if (this.isMicActive && this.analyser) {
      const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
      this.analyser.getByteTimeDomainData(dataArray);
      
      const sliceWidth = width * 1.0 / dataArray.length;
      let x = 0;
      
      for (let i = 0; i < dataArray.length; i++) {
        const v = dataArray[i] / 128.0;
        const y = v * height / 2;
        if (i === 0) {
          this.ctx.moveTo(x, y);
        } else {
          this.ctx.lineTo(x, y);
        }
        x += sliceWidth;
      }
    } else {
      // Synthetic cyber audio waveform
      const points = 60;
      const sliceWidth = width / points;
      const t = performance.now() / 400;
      
      for (let i = 0; i <= points; i++) {
        const x = i * sliceWidth;
        const amp = (height / 2) * this.rms;
        const y = (height / 2) + Math.sin(i * 0.3 + t) * Math.cos(i * 0.15 - t) * amp;
        if (i === 0) {
          this.ctx.moveTo(x, y);
        } else {
          this.ctx.lineTo(x, y);
        }
      }
    }
    
    this.ctx.stroke();
    
    // Update metric indicators on UI
    const metrics = this.getMetrics();
    const rmsEl = document.getElementById('audioRmsVal');
    const stateEl = document.getElementById('audioStateVal');
    if (rmsEl) rmsEl.textContent = `${Math.round(metrics.rms * 100)}%`;
    if (stateEl) {
      if (metrics.rms < 0.14) {
        stateEl.textContent = 'Silence / Passive';
        stateEl.style.color = '#94a3b8';
      } else if (metrics.rms > 0.55) {
        stateEl.textContent = 'Lively Discussion';
        stateEl.style.color = '#10b981';
      } else {
        stateEl.textContent = 'Instructor Speech';
        stateEl.style.color = '#38bdf8';
      }
    }
    
    this.animationId = requestAnimationFrame(() => this.renderWaveform());
  }
}

window.AudioMonitor = AudioMonitor;
