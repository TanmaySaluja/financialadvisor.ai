// DOM Elements
const chatContainer = document.getElementById("chat-container");
const chatMessagesEl = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatSendBtn = document.getElementById("chat-send-btn");
const chatTip = document.getElementById("chat-tip");
const newChatBtn = document.getElementById("new-chat-btn");
const savedChatsList = document.getElementById("saved-chats-list");

// State variables
let activeSessionId = null;
let clientProfile = {};
let chatHistory = [];
let finalPlan = null;
let metrics = null;

// Helpers
function formatCurrency(amount) {
  const abs = Math.abs(amount);
  const formatted = abs.toLocaleString("en-IN");
  return amount < 0 ? `-₹${formatted}` : `₹${formatted}`;
}

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

// LocalStorage Persistence
function getSavedSessions() {
  const data = localStorage.getItem("lunetra_advisory_sessions");
  return data ? JSON.parse(data) : [];
}

function saveSessionToStorage(session) {
  const sessions = getSavedSessions();
  const index = sessions.findIndex(s => s.id === session.id);
  if (index !== -1) {
    sessions[index] = session;
  } else {
    sessions.push(session);
  }
  localStorage.setItem("lunetra_advisory_sessions", JSON.stringify(sessions));
  renderSavedSessionsList();
}

function deleteSessionFromStorage(id) {
  let sessions = getSavedSessions();
  sessions = sessions.filter(s => s.id !== id);
  localStorage.setItem("lunetra_advisory_sessions", JSON.stringify(sessions));
  if (activeSessionId === id) {
    initiateNewChat();
  } else {
    renderSavedSessionsList();
  }
}

// Render Sidebar Saved Sessions
function renderSavedSessionsList() {
  const sessions = getSavedSessions();
  savedChatsList.innerHTML = "";
  
  if (sessions.length === 0) {
    savedChatsList.innerHTML = `<div style="font-size: 0.78rem; color: var(--muted); padding: 12px; font-style: italic;">No saved sessions</div>`;
    return;
  }

  sessions.forEach(session => {
    const item = document.createElement("div");
    item.className = `saved-chat-item ${session.id === activeSessionId ? 'active' : ''}`;
    item.dataset.id = session.id;

    const info = document.createElement("div");
    info.style.overflow = "hidden";
    info.style.textOverflow = "ellipsis";
    info.style.whiteSpace = "nowrap";
    info.style.flex = "1";

    const name = session.clientProfile.client_name || "New Client";
    const dateStr = new Date(session.id).toLocaleDateString(undefined, { month: "short", day: "numeric" });
    
    info.innerHTML = `
      <div>${name} (${session.clientProfile.age})</div>
      <div class="saved-chat-meta">${dateStr} · ${session.metrics ? session.metrics.expert_path : 'Intake'}</div>
    `;

    const deleteBtn = document.createElement("button");
    deleteBtn.className = "chat-delete-btn";
    deleteBtn.innerHTML = "×";
    deleteBtn.title = "Delete consultation";
    deleteBtn.style.padding = "2px 8px";
    deleteBtn.style.fontSize = "1.2rem";
    deleteBtn.style.background = "none";
    deleteBtn.style.boxShadow = "none";
    deleteBtn.style.color = "var(--muted)";
    deleteBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      deleteSessionFromStorage(session.id);
    });

    item.appendChild(info);
    item.appendChild(deleteBtn);

    item.addEventListener("click", () => {
      loadSession(session.id);
    });

    savedChatsList.appendChild(item);
  });
}

// Load a saved session
function loadSession(id) {
  const sessions = getSavedSessions();
  const session = sessions.find(s => s.id === id);
  if (!session) return;

  activeSessionId = id;
  clientProfile = session.clientProfile;
  chatHistory = session.chatHistory;
  finalPlan = session.finalPlan;
  metrics = session.metrics;

  renderSavedSessionsList();
  chatMessagesEl.innerHTML = "";

  // Render chat turns
  chatHistory.forEach(msg => {
    appendMessage(msg.role === "user" ? "client" : "advisor", msg.content);
  });

  // Render plan if completed
  if (finalPlan && metrics) {
    renderPlanBubble(metrics, finalPlan);
    chatForm.style.display = "none";
    chatTip.style.display = "none";
  } else {
    chatForm.style.display = "flex";
    chatTip.style.display = "inline";
  }
}

// Initiate Onboarding Form inside the Chatbox
function initiateNewChat() {
  activeSessionId = null;
  clientProfile = {};
  chatHistory = [];
  finalPlan = null;
  metrics = null;

  renderSavedSessionsList();
  chatMessagesEl.innerHTML = "";
  chatForm.style.display = "none";
  chatTip.style.display = "none";

  const onboardingBubble = document.createElement("div");
  onboardingBubble.className = "onboarding-card";
  onboardingBubble.innerHTML = `
    <div class="onboarding-info">
      <div class="onboarding-logo">
        <svg viewBox="0 0 24 24" width="40" height="40" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 3v18M3 12h18M7.75 7.75l8.5 8.5M7.75 16.25l8.5-8.5" />
        </svg>
      </div>
      <h3>Bit By Bit Wealth</h3>
      <p>An autonomous, cognitive wealth and budget routing model engineered on LangGraph backend.</p>
      
      <div class="onboarding-stats">
        <div class="onboarding-stat-row">
          <span class="pulse-dot"></span>
          <span class="stat-lbl">Model Node:</span>
          <span class="stat-val">Llama-3.3-70B</span>
        </div>
        <div class="onboarding-stat-row">
          <span class="pulse-dot"></span>
          <span class="stat-lbl">Network Status:</span>
          <span class="stat-val">Secure Node Online</span>
        </div>
        <div class="onboarding-stat-row">
          <span class="pulse-dot"></span>
          <span class="stat-lbl">Database Link:</span>
          <span class="stat-val">CRM Connected</span>
        </div>
      </div>
    </div>
    
    <div class="onboarding-form-wrapper">
      <h3>Client Onboarding</h3>
      <p>Submit your parameters directly into the Bit By Bit secure pipeline to commence your advisory session.</p>
      <form id="onboarding-form">
        <div class="row">
          <div class="input-group">
            <span class="input-label">Full Name</span>
            <div class="input-with-icon">
              <svg class="input-icon" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
              <input type="text" name="client_name" placeholder="Tanmay" required />
            </div>
          </div>
          <div class="input-group">
            <span class="input-label">Age</span>
            <div class="input-with-icon">
              <svg class="input-icon" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" /></svg>
              <input type="number" name="age" min="1" max="120" placeholder="28" required />
            </div>
          </div>
        </div>
        <div class="row three-cols">
          <div class="input-group">
            <span class="input-label">Monthly Income</span>
            <div class="input-with-icon prefix">
              <span class="input-prefix">₹</span>
              <input type="number" name="income" min="1" placeholder="80000" required />
            </div>
          </div>
          <div class="input-group">
            <span class="input-label">Monthly Expenses</span>
            <div class="input-with-icon prefix">
              <span class="input-prefix">₹</span>
              <input type="number" name="expenses" min="0" placeholder="50000" required />
            </div>
          </div>
          <div class="input-group">
            <span class="input-label">Overall Debt</span>
            <div class="input-with-icon prefix">
              <span class="input-prefix">₹</span>
              <input type="number" name="debt" min="0" placeholder="0" value="0" required />
            </div>
          </div>
        </div>
        <fieldset>
          <legend>Risk Profile</legend>
          <div class="risk-options">
            <label class="risk-pill">
              <input type="radio" name="risk_profile" value="low" />
              <span>
                Low
                <span class="pill-desc">Capital Protect</span>
              </span>
            </label>
            <label class="risk-pill">
              <input type="radio" name="risk_profile" value="moderate" />
              <span>
                Moderate
                <span class="pill-desc">Balanced Grow</span>
              </span>
            </label>
            <label class="risk-pill">
              <input type="radio" name="risk_profile" value="high" checked />
              <span>
                High
                <span class="pill-desc">Max Returns</span>
              </span>
            </label>
          </div>
        </fieldset>

        <!-- Live Surplus Calculator Gauge -->
        <div class="form-preview-gauge" id="form-preview-gauge">
          <div class="gauge-header">
            <span class="gauge-title">Surplus Projections</span>
            <span id="gauge-surplus-val" class="gauge-val">₹0</span>
          </div>
          <div class="gauge-bar-bg">
            <div class="gauge-bar-fill" id="gauge-bar-fill"></div>
          </div>
          <div class="gauge-footer">
            <span id="gauge-rate-text">Savings Rate: 0%</span>
            <span id="gauge-status-text" class="gauge-status neutral">Neutral</span>
          </div>
        </div>

        <button type="submit">Establish Connection</button>
      </form>
    </div>
  `;

  chatMessagesEl.appendChild(onboardingBubble);

  const onboardingForm = document.getElementById("onboarding-form");
  const incomeInput = onboardingForm.querySelector('input[name="income"]');
  const expensesInput = onboardingForm.querySelector('input[name="expenses"]');
  const debtInput = onboardingForm.querySelector('input[name="debt"]');
  const gaugeSurplusVal = document.getElementById("gauge-surplus-val");
  const gaugeBarFill = document.getElementById("gauge-bar-fill");
  const gaugeRateText = document.getElementById("gauge-rate-text");
  const gaugeStatusText = document.getElementById("gauge-status-text");

  function updateGauge() {
    const inc = parseFloat(incomeInput.value) || 0;
    const exp = parseFloat(expensesInput.value) || 0;
    
    if (inc <= 0) {
      gaugeSurplusVal.textContent = "₹0";
      gaugeBarFill.style.width = "0%";
      gaugeRateText.textContent = "Savings Rate: 0%";
      gaugeStatusText.textContent = "Neutral";
      gaugeStatusText.className = "gauge-status neutral";
      return;
    }
    
    const surplus = inc - exp;
    const rate = Math.max(0, Math.min(100, Math.round((surplus / inc) * 100)));
    
    gaugeSurplusVal.textContent = formatCurrency(surplus);
    
    if (surplus >= 0) {
      gaugeBarFill.style.width = `${rate}%`;
      gaugeBarFill.style.background = "var(--success)";
      gaugeRateText.textContent = `Savings Rate: ${rate}%`;
      gaugeStatusText.textContent = "Surplus Profile";
      gaugeStatusText.className = "gauge-status surplus";
      gaugeSurplusVal.className = "gauge-val positive";
    } else {
      const deficitPercent = Math.max(0, Math.min(100, Math.round((Math.abs(surplus) / inc) * 100)));
      gaugeBarFill.style.width = `${deficitPercent}%`;
      gaugeBarFill.style.background = "var(--danger)";
      gaugeRateText.textContent = `Deficit Ratio: ${deficitPercent}%`;
      gaugeStatusText.textContent = "Deficit Warning";
      gaugeStatusText.className = "gauge-status deficit";
      gaugeSurplusVal.className = "gauge-val negative";
    }
  }

  incomeInput.addEventListener("input", updateGauge);
  expensesInput.addEventListener("input", updateGauge);
  debtInput.addEventListener("input", updateGauge);

  onboardingForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(onboardingForm);
    
    clientProfile = {
      client_name: formData.get("client_name"),
      age: Number(formData.get("age")),
      income: Number(formData.get("income")),
      expenses: Number(formData.get("expenses")),
      debt: Number(formData.get("debt") || 0),
      risk_profile: formData.get("risk_profile"),
    };

    activeSessionId = Date.now();
    chatMessagesEl.innerHTML = "";
    
    // Initial loading indicator
    appendMessage("advisor", "Establishing connection to secure advisor node...");
    
    chatForm.style.display = "flex";
    chatTip.style.display = "inline";

    const session = {
      id: activeSessionId,
      clientProfile,
      chatHistory,
      finalPlan: null,
      metrics: null
    };
    saveSessionToStorage(session);

    await runAdvisoryTurn("");
  });
}

function appendMessage(role, text) {
  const msgEl = document.createElement("div");
  msgEl.className = `message ${role}`;
  msgEl.textContent = text;
  chatMessagesEl.appendChild(msgEl);
  chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
}

// Render final plan inside the chat feed as a rich bubble
function renderPlanBubble(data, markdownPlan) {
  const surplusClass = data.surplus_amount >= 0 ? "positive" : "negative";

  const bubble = document.createElement("div");
  bubble.className = "message plan-bubble";
  bubble.innerHTML = `
    <div class="plan-bubble-title">
      <h3>Financial Strategy Blueprint</h3>
      <div class="badges">
        <span class="badge status-${data.status}">${data.status}</span>
        <span class="badge expert">${data.expert_path} advisor</span>
      </div>
    </div>
    
    <div class="stats">
      <div class="stat">
        <div class="stat-label">Income</div>
        <div class="stat-value">${formatCurrency(data.income)}</div>
      </div>
      <div class="stat">
        <div class="stat-label">Base Expenses</div>
        <div class="stat-value">${formatCurrency(data.expenses)}</div>
      </div>
      <div class="stat">
        <div class="stat-label">Rent</div>
        <div class="stat-value">${formatCurrency(data.rent)}</div>
      </div>
      <div class="stat">
        <div class="stat-label">Total Expenses</div>
        <div class="stat-value">${formatCurrency(data.total_expenses)}</div>
      </div>
      <div class="stat">
        <div class="stat-label">Surplus</div>
        <div class="stat-value ${surplusClass}">${formatCurrency(data.surplus_amount)}</div>
      </div>
      <div class="stat">
        <div class="stat-label">Risk profile</div>
        <div class="stat-value">${data.risk_profile}</div>
      </div>
      <div class="stat">
        <div class="stat-label">Overall Debt</div>
        <div class="stat-value">${formatCurrency(data.debt || 0)}</div>
      </div>
      <div class="stat">
        <div class="stat-label">Emergency Fund</div>
        <div class="stat-value">${formatCurrency(data.emergency_fund)}</div>
      </div>
    </div>

    <div class="plan-details">${marked.parse(markdownPlan)}</div>
    <div class="log-note">Plan logged to CRM → ${data.log_file}</div>
  `;

  chatMessagesEl.appendChild(bubble);
  chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
}

// Submit a chat message and fetch advice turn
async function runAdvisoryTurn(userMessage = "") {
  try {
    const payload = {
      ...clientProfile,
      chat_history: chatHistory,
      user_message: userMessage
    };

    const response = await fetch("/api/advise", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      appendMessage("advisor", `System Error: ${data.detail || "Unable to consult node."}`);
      return;
    }

    // Clean initial loading message if present
    if (chatHistory.length === 0) {
      chatMessagesEl.innerHTML = "";
    }

    chatHistory = data.chat_history || [];

    // Redraw normal text chat history
    chatMessagesEl.innerHTML = "";
    chatHistory.forEach(msg => {
      appendMessage(msg.role === "user" ? "client" : "advisor", msg.content);
    });

    if (data.data_gathering_complete) {
      finalPlan = data.final_plan;
      metrics = data;
      renderPlanBubble(data, data.final_plan);
      chatForm.style.display = "none";
      chatTip.style.display = "none";
    }

    // Persist session state update
    const session = {
      id: activeSessionId,
      clientProfile,
      chatHistory,
      finalPlan,
      metrics
    };
    saveSessionToStorage(session);

  } catch (err) {
    appendMessage("advisor", "Connection failed. Check your network or local server.");
  } finally {
    chatInput.disabled = false;
    chatSendBtn.disabled = false;
    chatInput.focus();
  }
}

// Message submission listener
chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = chatInput.value.trim();
  if (!text) return;

  chatInput.value = "";
  chatInput.disabled = true;
  chatSendBtn.disabled = true;

  appendMessage("client", text);
  await runAdvisoryTurn(text);
});

newChatBtn.addEventListener("click", initiateNewChat);

// Initialize application state
window.addEventListener("DOMContentLoaded", () => {
  // Dismiss loading screen overlay
  const loaderOverlay = document.getElementById("loader-overlay");
  if (loaderOverlay) {
    setTimeout(() => {
      loaderOverlay.classList.add("fade-out");
    }, 3000);
  }

  const sessions = getSavedSessions();
  if (sessions.length > 0) {
    // Load the most recent session
    loadSession(sessions[sessions.length - 1].id);
  } else {
    initiateNewChat();
  }
});
