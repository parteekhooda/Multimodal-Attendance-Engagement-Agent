/**
 * Chart.js Controller for Classroom Engagement & Session Dynamics
 * Renders real-time dynamic timeline, attention drops, interaction peaks,
 * and seating zone engagement charts.
 */

class TimelineChartManager {
  constructor(canvasId) {
    this.canvasId = canvasId;
    this.chart = null;
    this.maxDataPoints = 35;
    this.initChart();
  }
  
  initChart() {
    const ctx = document.getElementById(this.canvasId);
    if (!ctx) return;
    
    // Check if Chart is available globally
    if (typeof Chart === 'undefined') {
      console.warn('Chart.js not loaded yet');
      return;
    }
    
    // Initial demo dataset
    const labels = ['0m', '2m', '4m', '6m', '8m', '10m', '12m', '14m', '16m', '18m', '20m', '22m', '24m'];
    const engagementData = [72, 78, 81, 84, 76, 71, 64, 52, 42, 44, 75, 86, 82];
    const audioData = [30, 45, 60, 78, 40, 35, 25, 20, 18, 20, 70, 88, 75];
    
    this.chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Composite Engagement',
            data: engagementData,
            borderColor: '#38bdf8',
            backgroundColor: 'rgba(56, 189, 248, 0.12)',
            borderWidth: 2.5,
            fill: true,
            tension: 0.35,
            pointRadius: (ctx) => {
              const val = ctx.raw;
              return val <= 45 ? 6 : (val >= 85 ? 6 : 3);
            },
            pointBackgroundColor: (ctx) => {
              const val = ctx.raw;
              return val <= 45 ? '#ef4444' : (val >= 85 ? '#10b981' : '#38bdf8');
            },
            pointBorderColor: '#0a0d14',
            pointBorderWidth: 2
          },
          {
            label: 'Interaction Index',
            data: audioData,
            borderColor: '#818cf8',
            borderDash: [5, 5],
            borderWidth: 1.8,
            fill: false,
            tension: 0.25,
            pointRadius: 0
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 600 },
        scales: {
          x: {
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#94a3b8', font: { family: 'JetBrains Mono', size: 11 } }
          },
          y: {
            min: 0,
            max: 100,
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: {
              color: '#94a3b8',
              font: { family: 'JetBrains Mono', size: 11 },
              callback: (val) => `${val}%`
            }
          }
        },
        plugins: {
          legend: {
            labels: {
              color: '#f8fafc',
              font: { family: 'Outfit', size: 12 },
              usePointStyle: true,
              boxWidth: 8
            }
          },
          tooltip: {
            backgroundColor: 'rgba(15, 21, 35, 0.95)',
            titleColor: '#38bdf8',
            titleFont: { family: 'Outfit', weight: 'bold' },
            bodyColor: '#f8fafc',
            bodyFont: { family: 'JetBrains Mono' },
            borderColor: 'rgba(99, 102, 241, 0.4)',
            borderWidth: 1,
            padding: 10,
            callbacks: {
              afterLabel: (context) => {
                const val = context.raw;
                if (val <= 45) return '⚠️ Attention Drop Flag';
                if (val >= 85) return '🔥 High Interaction Peak';
                return '';
              }
            }
          }
        }
      }
    });
  }
  
  addDataPoint(snapshot) {
    if (!this.chart) return;
    
    const now = new Date();
    const timeLabel = `${now.getHours()}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
    
    this.chart.data.labels.push(timeLabel);
    this.chart.data.datasets[0].data.push(Math.round(snapshot.composite_engagement));
    this.chart.data.datasets[1].data.push(Math.round(snapshot.interaction_index));
    
    if (this.chart.data.labels.length > this.maxDataPoints) {
      this.chart.data.labels.shift();
      this.chart.data.datasets[0].data.shift();
      this.chart.data.datasets[1].data.shift();
    }
    
    this.chart.update('none');
  }
}

// Zone Comparison Bar Chart
function initZoneChart(canvasId, zones) {
  const ctx = document.getElementById(canvasId);
  if (!ctx || typeof Chart === 'undefined') return;
  
  const labels = zones.map(z => z.zone_name);
  const data = zones.map(z => z.avg_engagement);
  
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Zone Engagement (%)',
        data: data,
        backgroundColor: [
          'rgba(16, 185, 129, 0.75)', // Front Row (High)
          'rgba(56, 189, 248, 0.75)', // Middle Row (Normal)
          'rgba(244, 63, 94, 0.75)'   // Back Row (Disengaged)
        ],
        borderRadius: 8,
        borderWidth: 1,
        borderColor: 'rgba(255, 255, 255, 0.1)'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#f8fafc', font: { family: 'Outfit', size: 12 } }
        },
        y: {
          min: 0,
          max: 100,
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: {
            color: '#94a3b8',
            font: { family: 'JetBrains Mono' },
            callback: v => `${v}%`
          }
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}

window.TimelineChartManager = TimelineChartManager;
window.initZoneChart = initZoneChart;
