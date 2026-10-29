/**
 * AI Pedagogical Agent & Offline Copilot Controller
 * Manages live suggestions feed, alert acknowledgments, and interactive
 * pedagogical decision-support chat.
 */

class AIAgentManager {
  constructor() {
    this.feedEl = document.getElementById('suggestionsFeed');
    this.badgeEl = document.getElementById('suggestionsCountBadge');
    this.suggestionsCount = 0;
    this.seenTitles = new Set();
    
    this.initCopilotChat();
  }
  
  addSuggestion(sug) {
    if (!this.feedEl || !sug) return;
    
    // De-duplicate recent alerts
    const key = `${sug.category}-${sug.title}`;
    if (this.seenTitles.has(key)) return;
    this.seenTitles.add(key);
    
    this.suggestionsCount += 1;
    if (this.badgeEl) this.badgeEl.textContent = `${this.suggestionsCount} New`;
    
    const card = document.createElement('div');
    card.className = `suggestion-card ${sug.severity || 'info'}`;
    
    const timeStr = new Date(sug.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    card.innerHTML = `
      <div class="sug-header">
        <span class="sug-title">${sug.title}</span>
        <span class="sug-time">${timeStr}</span>
      </div>
      <div class="sug-msg">${sug.message}</div>
      <div class="sug-action-box">
        <strong>Action:</strong> ${sug.pedagogical_action}
      </div>
    `;
    
    // Prepend to top of feed
    this.feedEl.insertBefore(card, this.feedEl.firstChild);
    
    // Trigger desktop toast notification if attention drop or monologue warning
    if (sug.severity === 'critical' || sug.severity === 'warning') {
      this.showToast(sug.title, sug.pedagogical_action);
    }
  }
  
  showToast(title, action) {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
      <div style="font-size: 1.2rem;">💡</div>
      <div style="flex: 1;">
        <div style="font-weight: 700; font-size: 0.85rem; color: #f8fafc; margin-bottom: 2px;">${title}</div>
        <div style="font-size: 0.78rem; color: #94a3b8;">${action}</div>
      </div>
    `;
    toastContainer.appendChild(toast);
    
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 6000);
  }
  
  initCopilotChat() {
    const input = document.getElementById('copilotInput');
    const sendBtn = document.getElementById('copilotSendBtn');
    const messagesBox = document.getElementById('copilotMessages');
    
    if (!input || !sendBtn || !messagesBox) return;
    
    const send = async () => {
      const text = input.value.trim();
      if (!text) return;
      
      // Add User Message
      this.appendMessage('user', text);
      input.value = '';
      
      // Loading Indicator
      const loadingBubble = this.appendMessage('assistant', '<span class="status-dot"></span> <em>Reasoning over session telemetry...</em>');
      
      try {
        const res = await fetch('/api/copilot/query', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: text })
        });
        const data = await res.json();
        
        // Format response markdown-like formatting to HTML
        let formatted = data.response
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/\*(.*?)\*/g, '<em>$1</em>')
          .replace(/\n\n/g, '<br><br>')
          .replace(/\n/g, '<br>');
          
        loadingBubble.innerHTML = formatted;
        messagesBox.scrollTop = messagesBox.scrollHeight;
      } catch (err) {
        loadingBubble.innerHTML = `<span style="color: #ef4444;">Error communicating with AI reasoning agent.</span>`;
      }
    };
    
    sendBtn.addEventListener('click', send);
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') send();
    });
    
    // Quick Prompt Chips
    document.querySelectorAll('.chip[data-prompt]').forEach(chip => {
      chip.addEventListener('click', () => {
        input.value = chip.getAttribute('data-prompt');
        send();
      });
    });
  }
  
  appendMessage(role, html) {
    const messagesBox = document.getElementById('copilotMessages');
    if (!messagesBox) return null;
    
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${role}`;
    bubble.innerHTML = html;
    messagesBox.appendChild(bubble);
    messagesBox.scrollTop = messagesBox.scrollHeight;
    return bubble;
  }
}

window.AiAgentManager = new AIAgentManager();
