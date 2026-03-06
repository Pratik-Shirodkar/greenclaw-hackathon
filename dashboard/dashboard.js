/* ============================================
   GreenClaw v2 — Live Dashboard Logic
   Connected to FastAPI backend at /api/*
   ============================================ */

const API_BASE = '';  // Same-origin (served by FastAPI)

// ============================================
// State
// ============================================
let currentCity = 'London';
let currentTipIndex = 0;
let chatOpen = false;
let myGlobe; // 3D Threat Map Globe Instance
let globeInitialized = false;

// ============================================
// Tab Navigation
// ============================================
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
    document.getElementById(`tab-${tabName}`).classList.add('active');

    // Lazy-init globe when Intelligence tab is first opened
    if (tabName === 'intelligence' && !globeInitialized) {
        globeInitialized = true;
        setTimeout(initGlobe, 100);
    }
}

// ============================================
// Particles Background
// ============================================
function createParticles() {
    const container = document.getElementById('particles');
    if (!container) return;
    for (let i = 0; i < 30; i++) {
        const p = document.createElement('div');
        p.className = 'particle';
        p.style.left = Math.random() * 100 + '%';
        p.style.animationDuration = (15 + Math.random() * 25) + 's';
        p.style.animationDelay = Math.random() * 20 + 's';
        p.style.width = (1 + Math.random() * 2) + 'px';
        p.style.height = p.style.width;
        container.appendChild(p);
    }
}

// ============================================
// Initialize
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    createParticles();
    // Globe is lazy-loaded when Intelligence tab is opened
    loadCityData();
    initTipDots();
    loadRandomFact();
    pollAlerts();
    loadWallet();
    loadBadges();
    loadQuests();
    buildStreakCalendar();
    refreshCommunityStats();

    document.getElementById('citySearch').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') loadCityData();
    });

    const actionInput = document.getElementById('actionInput');
    if (actionInput) {
        actionInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') logAction();
        });
    }

    // Auto-rotate tips
    setInterval(cycleTip, 6000);
    // Poll alerts every 2 minutes
    setInterval(pollAlerts, 120000);
    // Auto-refresh climate data every 60s
    setInterval(loadCityData, 60000);
    // Poll pipeline log every 10s
    pollPipeline();
    setInterval(pollPipeline, 10000);
});

// ============================================
// Multi-Agent Conversation (Live)
// ============================================
const stageAgentMap = {
    sentinel: 'stageMonitor',
    analyst: 'stageAnalyze',
    advisor: 'stageAdvise',
    dispatcher: 'stageAlert',
};

async function pollPipeline() {
    try {
        const res = await fetch(`${API_BASE}/api/agents/conversation`);
        const data = await res.json();
        const log = document.getElementById('pipelineLog');
        if (!log || !data.messages || data.messages.length === 0) return;

        log.innerHTML = '';
        document.querySelectorAll('.pipeline-stage').forEach(s => s.classList.remove('active'));

        data.messages.slice(-15).forEach(msg => {
            const entry = document.createElement('div');
            entry.className = 'agent-message';

            const time = new Date(msg.timestamp).toLocaleTimeString();
            const cityTag = msg.city !== 'global' ? `<span class="log-city">${msg.city}</span>` : '';
            const toTag = msg.to ? `<span class="agent-mention">@${msg.to}</span>` : '';

            // Highlight @mentions in text
            let text = msg.text;
            text = text.replace(/@(Analyst|Advisor|Dispatcher|Sentinel|Orchestrator)/g,
                '<span class="agent-mention">@$1</span>');
            // Bold **text**
            text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

            entry.innerHTML = `
                <div class="agent-header">
                    <span class="agent-avatar" style="background:${msg.color}22;border-color:${msg.color}">${msg.icon}</span>
                    <span class="agent-name" style="color:${msg.color}">${msg.name}</span>
                    <span class="agent-role">${msg.role}</span>
                    ${cityTag}
                    <span class="agent-time">${time}</span>
                </div>
                <div class="agent-text">${text}</div>`;
            log.appendChild(entry);

            // Highlight active stage
            const stageId = stageAgentMap[msg.agent];
            if (stageId) document.getElementById(stageId)?.classList.add('active');
        });

        log.scrollTop = log.scrollHeight;

        // Update cycle count
        const cycleMessages = data.messages.filter(m => m.action === 'cycle_start');
        if (cycleMessages.length > 0) {
            const lastText = cycleMessages[cycleMessages.length - 1].text;
            const match = lastText.match(/#(\d+)/);
            document.getElementById('pipelineCycle').textContent = `Cycle: ${match ? match[1] : '--'}`;
        }
    } catch (err) { /* silent */ }
}

// ============================================
// 3D Threat Map Globe
// ============================================
function initGlobe() {
    const container = document.getElementById('globeViz');
    if (!container || !window.Globe) return;

    myGlobe = window.Globe()
        .globeImageUrl('//unpkg.com/three-globe/example/img/earth-night.jpg')
        .bumpImageUrl('//unpkg.com/three-globe/example/img/earth-topology.png')
        .backgroundImageUrl('//unpkg.com/three-globe/example/img/night-sky.png')
        .width(container.clientWidth)
        .height(container.clientHeight)
        (container);

    // Auto-rotate
    myGlobe.controls().autoRotate = true;
    myGlobe.controls().autoRotateSpeed = 0.5;

    // Add custom emissive glow if THREE is available
    setTimeout(() => {
        try {
            const globeMaterial = myGlobe.globeMaterial();
            globeMaterial.color = new window.THREE.Color(0x2222ff);
            globeMaterial.emissive = new window.THREE.Color(0x111133);
            globeMaterial.emissiveIntensity = 0.5;
            globeMaterial.shininess = 0.7;
        } catch (e) {
            console.log("Custom 3D material fallback", e);
        }
    }, 500);

    // Handle window resize
    window.addEventListener('resize', () => {
        myGlobe.width(container.clientWidth).height(container.clientHeight);
    });
}

function updateGlobeData(data) {
    if (!myGlobe) return;

    const gData = [];

    // Add current searched city
    if (data.weather && data.weather.lat !== undefined && data.weather.lon !== undefined) {
        const aqiVal = data.aqi?.value || 0;
        gData.push({
            lat: data.weather.lat,
            lng: data.weather.lon,
            size: aqiVal > 150 ? 6 : 4,
            color: aqiVal > 150 ? '#f97316' : '#4ade80', // orange if bad, green if good
            name: `${data.city} (AQI ${aqiVal})`
        });

        // Point camera to city
        myGlobe.pointOfView({ lat: data.weather.lat, lng: data.weather.lon, altitude: 2 }, 1500);
    }

    // Add global NASA disasters
    if (data.disasters && Array.isArray(data.disasters)) {
        data.disasters.forEach(d => {
            if (d.coords && d.coords.length === 2) {
                gData.push({
                    lat: d.coords[1], // [lon, lat] from GeoJSON
                    lng: d.coords[0],
                    size: 8,
                    color: '#ef4444', // red for disasters
                    name: `${d.icon} ${d.title}`
                });
            }
        });
    }

    myGlobe
        .ringsData(gData)
        .ringColor('color')
        .ringMaxRadius('size')
        .ringPropagationSpeed(3)
        .ringRepeatPeriod(700)
        .labelsData(gData)
        .labelLat('lat')
        .labelLng('lng')
        .labelText('name')
        .labelSize(1.2)
        .labelDotRadius(0.5)
        .labelColor(() => 'rgba(255, 255, 255, 0.9)')
        .labelResolution(2);
}

// ============================================
// City Data (LIVE API)
// ============================================
async function loadCityData() {
    const cityInput = document.getElementById('citySearch');
    currentCity = cityInput ? cityInput.value.trim() || 'London' : 'London';

    try {
        const res = await fetch(`${API_BASE}/api/climate/${encodeURIComponent(currentCity)}`);
        const data = await res.json();

        if (data.weather) updateWeather(data.weather, data.city || currentCity);
        if (data.aqi) updateAQI(data.aqi);
        if (data.disasters) {
            loadDisasters(data.disasters);
            if (globeInitialized) updateGlobeData(data);
        }

        // Load new features for this city
        loadTrendChart(currentCity);
        loadPolicyAlerts(currentCity);
    } catch (err) {
        console.error('Failed to load city data:', err);
    }
}

// ============================================
// Weather (Live)
// ============================================
function updateWeather(w, city) {
    if (!w || w.error) {
        document.getElementById('weatherCondition').textContent = w?.error || 'API unavailable';
        return;
    }
    animateNumber('tempValue', w.temp, 1);
    document.getElementById('weatherIcon').textContent = w.icon || '🌍';
    document.getElementById('weatherCity').textContent = `${city}, ${w.country}`;
    document.getElementById('weatherCondition').textContent = w.condition;
    document.getElementById('feelsLike').textContent = `${w.feels}°C`;
    document.getElementById('humidity').textContent = `${w.humidity}%`;
    document.getElementById('wind').textContent = `${w.wind} m/s`;
    document.getElementById('pressure').textContent = `${w.pressure} hPa`;

    const strip = document.getElementById('forecastStrip');
    strip.innerHTML = '';
    (w.forecast || []).forEach(f => {
        const day = document.createElement('div');
        day.className = 'forecast-day';
        day.innerHTML = `
            <div class="forecast-date">${f.date}</div>
            <div class="forecast-temp">
                <span class="temp-high">${Math.round(f.high)}°</span>
                <span style="color:var(--text-muted)"> / </span>
                <span class="temp-low">${Math.round(f.low)}°</span>
            </div>`;
        strip.appendChild(day);
    });
}

// ============================================
// AQI (Live)
// ============================================
function updateAQI(aqi) {
    if (!aqi || aqi.error) {
        document.getElementById('aqiCategory').textContent = aqi?.error || 'Unavailable';
        return;
    }
    animateNumber('aqiValue', aqi.value, 0);
    document.getElementById('aqiCategory').textContent = aqi.category;
    document.getElementById('aqiIcon').textContent = aqi.icon;
    document.getElementById('aqiAdvice').textContent = aqi.advice;

    const fill = document.getElementById('aqiRingFill');
    const pct = Math.min(aqi.value / 300, 1);
    const circumference = 2 * Math.PI * 52;
    fill.style.strokeDasharray = circumference;
    fill.style.strokeDashoffset = circumference * (1 - pct);
    const colors = { "Good": "#4ade80", "Moderate": "#fbbf24", "Unhealthy for Sensitive Groups": "#fb923c", "Unhealthy": "#f87171", "Very Unhealthy": "#a78bfa", "Hazardous": "#484f58" };
    fill.style.stroke = colors[aqi.category] || "#4ade80";

    const grid = document.getElementById('pollutantGrid');
    grid.innerHTML = '';
    Object.entries(aqi.pollutants || {}).forEach(([name, val]) => {
        const item = document.createElement('div');
        item.className = 'pollutant-item';
        item.innerHTML = `<span class="pollutant-name">${name}</span><span class="pollutant-val">${val}</span>`;
        grid.appendChild(item);
    });
}

// ============================================
// Disasters (Live)
// ============================================
function loadDisasters(disasters) {
    const list = document.getElementById('disasterList');
    list.innerHTML = '';
    if (!disasters || disasters.length === 0) {
        list.innerHTML = '<div style="padding:1rem;opacity:0.5">No active disasters</div>';
        document.getElementById('disasterCount').textContent = '0 Active';
        return;
    }
    disasters.forEach((d, i) => {
        const item = document.createElement('div');
        item.className = 'disaster-item';
        item.style.animationDelay = `${i * 0.1}s`;
        item.innerHTML = `
            <span class="disaster-icon">${d.icon}</span>
            <div class="disaster-info">
                <div class="disaster-title">${d.title}</div>
                <div class="disaster-meta">${d.date}</div>
                ${d.categories.map(c => `<span class="disaster-category">${c}</span>`).join('')}
            </div>`;
        list.appendChild(item);
    });
    document.getElementById('disasterCount').textContent = `${disasters.length} Active`;
}

// ============================================
// Risk Analysis — REAL Z.AI (Live)
// ============================================
function resetRiskPanel() {
    document.getElementById('riskScoreNumber').textContent = '--';
    document.getElementById('riskScoreNumber').style.color = 'var(--text-muted)';
    document.getElementById('riskScoreCircle').style.borderColor = 'var(--glass-border)';
    document.getElementById('riskLevelText').textContent = 'Click "Run Analysis" to begin';
    document.getElementById('riskCategories').innerHTML = '';
    document.getElementById('thinkingContent').innerHTML = '<div class="thinking-placeholder">AI reasoning will appear here when analysis runs...</div>';
    document.getElementById('thinkingStatus').textContent = 'Idle';
    document.getElementById('thinkingStatus').className = 'thinking-status';
    document.getElementById('recommendationsList').innerHTML = '<div class="recommendation-placeholder">Run analysis to get recommendations</div>';
}

async function runRiskAnalysis() {
    const btn = document.getElementById('analyzeBtn');
    if (btn.classList.contains('running')) return;
    btn.classList.add('running');
    btn.innerHTML = '<span class="btn-icon">⏳</span> Analyzing...';

    const thinkingStatus = document.getElementById('thinkingStatus');
    const thinkingContent = document.getElementById('thinkingContent');
    thinkingStatus.textContent = 'Connecting to Z.AI GLM...';
    thinkingStatus.className = 'thinking-status active';
    thinkingContent.innerHTML = '';

    // Show initial thinking step
    addThinkingStep('📡 Data Ingestion', `Fetching live climate data for ${currentCity}...`);
    await sleep(500);

    try {
        const res = await fetch(`${API_BASE}/api/risk/${encodeURIComponent(currentCity)}`, { method: 'POST' });
        const data = await res.json();

        if (data.error) {
            addThinkingStep('❌ Error', data.error);
            thinkingStatus.textContent = 'Error';
            thinkingStatus.className = 'thinking-status';
            btn.classList.remove('running');
            btn.innerHTML = '<span class="btn-icon">⚡</span> Run Analysis';
            return;
        }

        // Show thinking steps from Z.AI
        const steps = data.thinking_steps || [
            { label: '🔍 Pattern Analysis', text: 'Cross-referencing environmental indicators...' },
            { label: '📊 Risk Modeling', text: 'Computing multi-factor risk scores...' },
            { label: '💡 Recommendations', text: 'Generating actionable recommendations...' },
            { label: '✅ Validation', text: `Analysis complete. Risk: ${data.level} (${data.score}/10)` },
        ];

        for (const step of steps) {
            await sleep(400 + Math.random() * 300);
            addThinkingStep(step.label, step.text);
        }

        await sleep(300);
        thinkingStatus.textContent = 'Complete';
        thinkingStatus.className = 'thinking-status done';

        // Update risk score
        const colors = { "Low": "#4ade80", "Moderate": "#fbbf24", "High": "#fb923c", "Critical": "#f87171" };
        const color = colors[data.level] || "#4ade80";
        const scoreEl = document.getElementById('riskScoreNumber');
        const circleEl = document.getElementById('riskScoreCircle');
        animateNumber('riskScoreNumber', data.score, 0);
        scoreEl.style.color = color;
        circleEl.style.borderColor = color;
        circleEl.style.boxShadow = `0 0 20px ${color}33, inset 0 0 20px ${color}11`;

        const icons = { "Low": "🟢", "Moderate": "🟡", "High": "🟠", "Critical": "🔴" };
        document.getElementById('riskLevelText').innerHTML = `${icons[data.level] || '⚠️'} <strong>${data.level} Risk</strong> · Confidence: ${data.confidence} · <em>Model: ${data.model || 'Z.AI GLM'}</em>`;

        // Risk categories
        const catContainer = document.getElementById('riskCategories');
        catContainer.innerHTML = '';
        (data.risks || []).forEach((r, i) => {
            const barColor = r.score <= 3 ? '#4ade80' : r.score <= 5 ? '#fbbf24' : r.score <= 7 ? '#fb923c' : '#f87171';
            const item = document.createElement('div');
            item.className = 'risk-category-item';
            item.style.animationDelay = `${i * 0.15}s`;
            item.innerHTML = `
                <span class="risk-cat-name">${r.category}</span>
                <div class="risk-cat-bar"><div class="risk-cat-fill" style="width:0%;background:${barColor}"></div></div>
                <span class="risk-cat-score" style="color:${barColor}">${r.score}/10</span>`;
            catContainer.appendChild(item);
            setTimeout(() => { item.querySelector('.risk-cat-fill').style.width = `${r.score * 10}%`; }, 200 + i * 150);
        });

        // Recommendations
        const recList = document.getElementById('recommendationsList');
        recList.innerHTML = '';
        const recIcons = ['🛡️', '💧', '🏃', '👴', '📱'];
        (data.recommendations || []).forEach((rec, i) => {
            const item = document.createElement('div');
            item.className = 'recommendation-item';
            item.style.animationDelay = `${i * 0.1}s`;
            item.innerHTML = `<span class="rec-icon">${recIcons[i] || '✅'}</span><span>${rec}</span>`;
            recList.appendChild(item);
        });
        if (data.sdg13) {
            const sdg = document.createElement('div');
            sdg.className = 'recommendation-item';
            sdg.innerHTML = `<span class="rec-icon">🌍</span><span><strong>SDG 13:</strong> ${data.sdg13}</span>`;
            recList.appendChild(sdg);
        }

    } catch (err) {
        addThinkingStep('❌ Connection Error', err.message);
        thinkingStatus.textContent = 'Error';
    }

    btn.classList.remove('running');
    btn.innerHTML = '<span class="btn-icon">⚡</span> Run Analysis';
}

function addThinkingStep(label, text) {
    const content = document.getElementById('thinkingContent');
    const step = document.createElement('div');
    step.className = 'thinking-step';
    step.innerHTML = `<span class="step-label">${label}:</span> ${text}`;
    content.appendChild(step);
    content.scrollTop = content.scrollHeight;
}

// ============================================
// Tip Carousel
// ============================================
function initTipDots() {
    const dots = document.getElementById('tipDots');
    const tips = document.querySelectorAll('.tip-card');
    dots.innerHTML = '';
    tips.forEach((_, i) => {
        const dot = document.createElement('div');
        dot.className = 'tip-dot' + (i === 0 ? ' active' : '');
        dot.onclick = () => showTip(i);
        dots.appendChild(dot);
    });
}

function showTip(index) {
    const tips = document.querySelectorAll('.tip-card');
    const dots = document.querySelectorAll('.tip-dot');
    tips.forEach(t => t.classList.remove('active'));
    dots.forEach(d => d.classList.remove('active'));
    tips[index]?.classList.add('active');
    dots[index]?.classList.add('active');
    currentTipIndex = index;
}

function cycleTip() {
    const tips = document.querySelectorAll('.tip-card');
    currentTipIndex = (currentTipIndex + 1) % tips.length;
    showTip(currentTipIndex);
}

// ============================================
// Community Tracker (Live Backend)
// ============================================
async function logAction() {
    const input = document.getElementById('actionInput');
    const action = input.value.trim();
    if (!action) return;

    try {
        const res = await fetch(`${API_BASE}/api/community/log`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user: 'dashboard_user', action }),
        });
        const entry = await res.json();

        // Handle rejected (harmful) actions
        if (entry.rejected) {
            const log = document.getElementById('actionLog');
            const item = document.createElement('div');
            item.className = 'log-item log-rejected';
            item.innerHTML = `<span class="log-icon">${entry.emoji}</span><span style="color:#f87171">${entry.message}</span>`;
            log.insertBefore(item, log.firstChild);
            setTimeout(() => item.remove(), 5000);
        } else {
            // Add to log
            const log = document.getElementById('actionLog');
            const item = document.createElement('div');
            item.className = 'log-item';
            item.innerHTML = `<span class="log-icon">${entry.emoji}</span><span>${action}</span><span class="log-co2">-${entry.co2_kg} kg</span>`;
            log.insertBefore(item, log.firstChild);

            // Refresh stats
            await refreshCommunityStats();
        }
    } catch (err) {
        console.error('Failed to log action:', err);
    }

    input.value = '';
    input.focus();
}

async function refreshCommunityStats() {
    try {
        const res = await fetch(`${API_BASE}/api/community/stats`);
        const stats = await res.json();
        animateNumber('totalCO2', stats.total_co2_kg, 1);
        document.getElementById('treesEquiv').textContent = stats.equivalents.trees_equivalent;
        document.getElementById('carEquiv').textContent = stats.equivalents.car_km_saved;
        document.getElementById('flightEquiv').textContent = stats.equivalents.flights_offset;

        // Populate new community features
        loadLeaderboard(stats.leaderboard || []);
        updateChallenge(stats.total_co2_kg, stats.total_actions, (stats.leaderboard || []).length);
        loadActivityFeed(stats.recent || []);
    } catch (err) {
        console.error('Failed to load stats:', err);
    }
}

// ============================================
// Alerts (Automated)
// ============================================
async function pollAlerts() {
    try {
        const res = await fetch(`${API_BASE}/api/alerts`);
        const data = await res.json();
        if (data.alerts && data.alerts.length > 0) {
            data.alerts.forEach(alert => showAlertToast(alert));
        }
    } catch (err) { /* silent fail */ }
}

function showAlertToast(alert) {
    const container = document.getElementById('alertContainer');
    if (!container) return;
    // Don't show duplicate
    if (container.querySelector(`[data-city="${alert.city}"]`)) return;

    const toast = document.createElement('div');
    toast.className = `alert-toast ${alert.severity}`;
    toast.dataset.city = alert.city;
    toast.innerHTML = `
        <div class="alert-message">${alert.message}</div>
        <button class="alert-close" onclick="this.parentElement.remove()">✕</button>`;
    container.appendChild(toast);

    // Auto-remove after 30s
    setTimeout(() => toast.remove(), 10000);
}

// ============================================
// Chat Widget
// ============================================
let kidsMode = false;

function toggleKidsMode() {
    kidsMode = !kidsMode;
    const btn = document.getElementById('kidsModeToggle');
    btn.classList.toggle('active', kidsMode);
    btn.querySelector('.kids-mode-text').textContent = kidsMode ? 'Kids Mode: ON' : 'Kids Mode: OFF';
    document.body.classList.toggle('kids-theme', kidsMode);

    // Auto-open chat with a fun welcome if turning on
    if (kidsMode) {
        if (!chatOpen) toggleChat();
        addChatMessage('bot', '🎮 **Kids Mode Activated!** 🌟\n\nHi there! I am your fun GreenClaw Guide! Ask me any question about the Earth, animals, or weather!');
    }
}

function toggleChat() {
    chatOpen = !chatOpen;
    document.getElementById('chatPanel').classList.toggle('open', chatOpen);
    document.getElementById('chatBubble').classList.toggle('active', chatOpen);
    if (chatOpen) {
        document.getElementById('chatInput').focus();
        // Show welcome on first open
        const msgs = document.getElementById('chatMessages');
        if (msgs.children.length === 0) {
            addChatMessage('bot', '📡 System: **GreenClaw Core Agent** Online\n\nAwaiting operational query. Transmit your request regarding atmospheric telemetry, algorithmic directives, or protocol status.');
        }
    }
}

async function sendChat() {
    const input = document.getElementById('chatInput');
    const msg = input.value.trim();
    if (!msg) return;

    addChatMessage('user', msg);
    input.value = '';

    // Show typing indicator
    const typing = document.createElement('div');
    typing.className = 'chat-message bot typing';
    typing.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
    document.getElementById('chatMessages').appendChild(typing);
    scrollChat();

    try {
        const res = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg, city: currentCity, kids_mode: kidsMode }),
        });
        const data = await res.json();
        typing.remove();

        // Show skill badge
        const skillBadge = data.skill !== 'orchestrator' ? `<div class="skill-badge">${skillIcons[data.skill] || '🤖'} ${data.skill}</div>` : '';
        addChatMessage('bot', skillBadge + formatMarkdown(data.reply));
    } catch (err) {
        typing.remove();
        addChatMessage('bot', '⚠️ Connection error. Is the server running?');
    }
}

const skillIcons = {
    'climate-monitor': '🌡️',
    'risk-analyzer': '⚠️',
    'action-advisor': '💚',
    'community-tracker': '📊',
    'edu-mode': '🎮',
    'carbon-calculator': '🧮',
};

function addChatMessage(role, html) {
    const msgs = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = `chat-message ${role}`;
    div.innerHTML = html;
    msgs.appendChild(div);
    scrollChat();
}

function scrollChat() {
    const msgs = document.getElementById('chatMessages');
    msgs.scrollTop = msgs.scrollHeight;
}

function formatMarkdown(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/_(.*?)_/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
}

// ============================================
// Quiz
// ============================================
const quizQuestions = [
    { q: "🌍 What gas do trees breathe in?", options: ["A) Oxygen", "B) Carbon Dioxide", "C) Nitrogen"], correct: 1 },
    { q: "☀️ What is the main source of energy for Earth?", options: ["A) Wind", "B) The Sun", "C) The Moon"], correct: 1 },
    { q: "🌊 What percentage of Earth is covered by water?", options: ["A) 50%", "B) 71%", "C) 90%"], correct: 1 },
    { q: "♻️ Which of these can be recycled?", options: ["A) Banana peel", "B) Glass bottle", "C) Used tissue"], correct: 1 },
    { q: "🔋 Which energy source is renewable?", options: ["A) Coal", "B) Natural Gas", "C) Solar"], correct: 2 },
    { q: "🌡️ How much has global temp risen since pre-industrial times?", options: ["A) 0.3°C", "B) 1.1°C", "C) 3.5°C"], correct: 1 },
    { q: "🌳 How much CO₂ does one tree absorb per year?", options: ["A) 2 kg", "B) 22 kg", "C) 220 kg"], correct: 1 },
    { q: "🐻‍❄️ Which animal is most affected by melting ice?", options: ["A) Elephant", "B) Polar Bear", "C) Monkey"], correct: 1 },
];
let currentQuizIndex = 0;

const funFacts = [
    "🐋 A single large whale captures about 33 TONS of CO₂ over its lifetime!",
    "🌱 If every family in the UK planted one tree, it would capture 5 million tonnes of CO₂!",
    "☀️ The Sun produces enough energy in ONE SECOND to power Earth for 500,000 years!",
    "🚲 If you bike instead of drive for just 10 km, you save about 2.3 kg of CO₂!",
    "🍔 Making ONE hamburger uses as much water as taking a 2-MONTH shower!",
];

function checkAnswer(btn, isCorrect) {
    document.querySelectorAll('.quiz-option').forEach(opt => {
        opt.disabled = true;
        if (opt.classList.contains('correct')) opt.classList.add('selected-correct');
    });
    if (isCorrect) {
        btn.classList.add('selected-correct');
        document.getElementById('quizResult').innerHTML = '✅ METRIC VERIFIED! Agent aligned with baseline data. ⭐';
        document.getElementById('quizResult').style.color = '#4ade80';
    } else {
        btn.classList.add('selected-wrong');
        document.getElementById('quizResult').innerHTML = '⚠️ ALIGNMENT FAILURE! Agent diverted from baseline. Re-calibrate.';
        document.getElementById('quizResult').style.color = '#fb923c';
    }
    document.getElementById('nextQuestionBtn').style.display = 'block';
}

function nextQuestion() {
    currentQuizIndex = (currentQuizIndex + 1) % quizQuestions.length;
    const q = quizQuestions[currentQuizIndex];
    document.getElementById('quizQuestion').textContent = q.q;
    const optionsContainer = document.getElementById('quizOptions');
    optionsContainer.innerHTML = '';
    q.options.forEach((opt, i) => {
        const btn = document.createElement('button');
        btn.className = 'quiz-option' + (i === q.correct ? ' correct' : '');
        btn.textContent = opt;
        btn.onclick = () => checkAnswer(btn, i === q.correct);
        optionsContainer.appendChild(btn);
    });
    document.getElementById('quizResult').innerHTML = '';
    document.getElementById('nextQuestionBtn').style.display = 'none';
    loadRandomFact();
}

function loadRandomFact() {
    const fact = funFacts[Math.floor(Math.random() * funFacts.length)];
    document.getElementById('factText').textContent = fact;
}

// ============================================
// Utilities
// ============================================
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function animateNumber(elementId, target, decimals) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const start = parseFloat(el.textContent) || 0;
    const diff = target - start;
    const duration = 800;
    const startTime = performance.now();
    function update(t) {
        const elapsed = t - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = (start + diff * eased).toFixed(decimals);
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

// ============================================
// Carbon Wallet (Live)
// ============================================
const WALLET_USER = 'demo_user';

async function loadWallet() {
    try {
        const r = await fetch(`${API_BASE}/api/wallet/${WALLET_USER}`);
        const data = await r.json();
        document.getElementById('walletRankIcon').textContent = data.rank_icon || '🌱';
        document.getElementById('walletRankName').textContent = data.rank_name || 'Beginner';
        document.getElementById('walletCredits').textContent = data.credits || 0;
        document.getElementById('walletCO2').textContent = data.lifetime_co2_kg || 0;
        document.getElementById('walletStreak').textContent = data.streak_days || 0;
        document.getElementById('walletActions').textContent = data.actions_count || 0;

        if (data.next_rank) {
            let nextRankName = data.next_rank.name === 'Sprout' ? 'Verified Operator' : data.next_rank.name === 'Guardian' ? 'Protocol Securer' : data.next_rank.name;
            document.getElementById('walletNextRank').textContent = `${data.next_rank.icon} ${nextRankName}`;
            const pct = Math.min(100, ((data.credits / data.next_rank.threshold) * 100));
            document.getElementById('walletProgressBar').style.width = `${pct}%`;
            document.getElementById('walletRemaining').textContent = `${data.next_rank.remaining} credits to next level`;
        } else {
            document.getElementById('walletNextRank').textContent = '🦞 MAX LEVEL';
            document.getElementById('walletProgressBar').style.width = '100%';
            document.getElementById('walletRemaining').textContent = 'You reached the highest level!';
        }

        // Update hero stats on Home tab
        const heroCredits = document.getElementById('heroCredits');
        const heroStreak = document.getElementById('heroStreak');
        if (heroCredits) heroCredits.textContent = data.credits || 0;
        if (heroStreak) heroStreak.textContent = data.streak_days || 0;

        // Update carbon breakdown donut
        buildCarbonBreakdown(data);

        // Show connected wallet address
        if (data.wallet_address) {
            const addr = data.wallet_address;
            document.querySelector('.wallet-connect-row').style.display = 'none';
            document.querySelector('.wallet-connect-label').textContent = '🔗 Wallet connected:';
            document.getElementById('walletConnectedInfo').style.display = 'flex';
            document.getElementById('walletLinkedAddress').textContent = `${addr.slice(0, 6)}...${addr.slice(-4)}`;
            document.getElementById('walletLinkedAddress').title = addr;
        }
    } catch (e) {
        console.error('Wallet load error:', e);
    }
}

async function connectWallet() {
    const input = document.getElementById('walletAddressInput');
    const address = input.value.trim();
    if (!address.startsWith('0x') || address.length !== 42) {
        alert('Invalid address. Must be 0x followed by 40 hex characters.');
        return;
    }
    try {
        const r = await fetch(`${API_BASE}/api/wallet/connect?user=${WALLET_USER}&address=${address}`, { method: 'POST' });
        const data = await r.json();
        if (data.success) {
            loadWallet(); // Refresh to show connected state
        } else {
            alert(data.error || 'Connection failed');
        }
    } catch (e) {
        alert('Error connecting wallet: ' + e.message);
    }
}

// ============================================
// Trophy Case (Badges)
// ============================================
const BADGE_MAP = {
    genesis: { icon: '🌱', name: 'Genesis Green', desc: 'First eco-action' },
    halfcentury: { icon: '🌿', name: 'Half Century', desc: '50 kg CO₂' },
    centurion: { icon: '🌳', name: 'Centurion', desc: '100 kg CO₂' },
    photo_proof: { icon: '📸', name: 'Proof of Green', desc: 'Vision AI verified' },
    streak7: { icon: '🔥', name: 'Streak Master', desc: '7-day streak' },
    guardian: { icon: '🌍', name: 'Guardian', desc: '500 kg CO₂' },
    streak30: { icon: '💎', name: 'Streak Legend', desc: '30-day streak' },
    legend: { icon: '🦞', name: 'GreenClaw Legend', desc: '1000 kg CO₂' },
};

async function loadBadges() {
    try {
        const r = await fetch(`${API_BASE}/api/badges/${WALLET_USER}`);
        const data = await r.json();
        const earned = new Set(data.badges.map(b => b.id));
        const grid = document.getElementById('trophyGrid');
        grid.innerHTML = '';

        for (const [id, info] of Object.entries(BADGE_MAP)) {
            const isEarned = earned.has(id);
            const badge = data.badges.find(b => b.id === id);
            const el = document.createElement('div');
            el.className = `trophy-item ${isEarned ? 'trophy-earned' : 'trophy-locked'}`;
            el.innerHTML = `
                <div class="trophy-icon">${info.icon}</div>
                <div class="trophy-name">${info.name}</div>
                <div class="trophy-desc">${isEarned && badge ? badge.token_id.slice(-8) : info.desc}</div>
            `;
            if (isEarned) el.title = `Token: ${badge.token_id}`;
            grid.appendChild(el);
        }
    } catch (e) {
        console.error('Badges load error:', e);
    }
}

// ============================================
// Quest Board (Daily)
// ============================================
async function loadQuests() {
    try {
        const r = await fetch(`${API_BASE}/api/quests`);
        const data = await r.json();
        const list = document.getElementById('questList');

        // Also load profile
        let profile = { total_xp: 0, level_name: '🥚 Hatchling' };
        try {
            const r2 = await fetch(`${API_BASE}/api/quest/profile/${WALLET_USER}`);
            profile = await r2.json();
        } catch (e) { }

        const parts = (profile.level_name || '🥚 Hatchling').split(' ');
        document.getElementById('questLevelIcon').textContent = parts[0];
        document.getElementById('questLevelName').textContent = parts.slice(1).join(' ');
        document.getElementById('questXP').textContent = `${profile.total_xp || 0} XP`;

        list.innerHTML = '';
        for (const q of data.quests) {
            const el = document.createElement('div');
            el.className = 'quest-item';
            el.id = `quest-${q.id}`;
            el.innerHTML = `
                <span class="quest-title">${q.title}</span>
                <span class="quest-xp-badge">⭐${q.xp} XP</span>
                <button class="quest-complete-btn" onclick="completeQuest(${q.id})">Done ✓</button>
            `;
            list.appendChild(el);
        }
    } catch (e) {
        console.error('Quests load error:', e);
    }
}

async function completeQuest(questId) {
    try {
        const r = await fetch(`${API_BASE}/api/quest/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user: WALLET_USER, quest_id: questId }),
        });
        const data = await r.json();
        if (data.error) {
            alert(data.error);
            return;
        }

        // Mark quest as done
        const el = document.getElementById(`quest-${questId}`);
        if (el) {
            el.classList.add('quest-done');
            el.querySelector('.quest-complete-btn').textContent = '✅';
            el.querySelector('.quest-complete-btn').disabled = true;
        }

        // Refresh wallet and badges
        loadWallet();
        loadBadges();

        // Update quest profile display
        const parts = (data.level_name || '🥚 Hatchling').split(' ');
        document.getElementById('questLevelIcon').textContent = parts[0];
        document.getElementById('questLevelName').textContent = parts.slice(1).join(' ');
        document.getElementById('questXP').textContent = `${data.total_xp || 0} XP`;
    } catch (e) {
        console.error('Quest complete error:', e);
    }
}

// ============================================
// Streak Calendar (Home Tab)
// ============================================
function buildStreakCalendar() {
    const calendar = document.getElementById('streakCalendar');
    if (!calendar) return;
    calendar.innerHTML = '';

    // Start clean — all 30 days empty (no fake data)
    const today = new Date();

    for (let i = 29; i >= 0; i--) {
        const d = new Date(today);
        d.setDate(d.getDate() - i);
        const dateStr = d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        const cell = document.createElement('div');
        cell.className = 'streak-day';
        cell.title = `${dateStr}: 0 actions`;
        calendar.appendChild(cell);
    }

    const streakTotal = document.getElementById('streakTotal');
    const streakBest = document.getElementById('streakBest');
    const streakActive = document.getElementById('streakActive');
    if (streakTotal) streakTotal.textContent = 0;
    if (streakBest) streakBest.textContent = 0;
    if (streakActive) streakActive.textContent = 0;
}

// ============================================
// Carbon Breakdown Donut (Home Tab)
// ============================================
function buildCarbonBreakdown(walletData) {
    const svg = document.getElementById('donutChart');
    const totalEl = document.getElementById('donutTotal');
    if (!svg || !totalEl) return;

    const totalCO2 = walletData ? walletData.lifetime_co2_kg || walletData.credits || 0 : 0;
    totalEl.textContent = totalCO2;

    // Simulate category breakdown based on total
    const categories = [
        { id: 'Transport', pct: 0.35, color: '#4ade80', elId: 'bkdTransport' },
        { id: 'Food', pct: 0.25, color: '#60a5fa', elId: 'bkdFood' },
        { id: 'Energy', pct: 0.2, color: '#a78bfa', elId: 'bkdEnergy' },
        { id: 'Recycling', pct: 0.12, color: '#f472b6', elId: 'bkdRecycle' },
        { id: 'Other', pct: 0.08, color: '#fbbf24', elId: 'bkdOther' },
    ];

    const r = 50;
    const circumference = 2 * Math.PI * r;
    let offset = 0;

    // Remove old segments
    svg.querySelectorAll('.donut-seg').forEach(el => el.remove());

    categories.forEach(cat => {
        const catVal = Math.round(totalCO2 * cat.pct * 100) / 100;
        const segLen = circumference * cat.pct;

        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.classList.add('donut-seg');
        circle.setAttribute('cx', '60');
        circle.setAttribute('cy', '60');
        circle.setAttribute('r', String(r));
        circle.setAttribute('fill', 'none');
        circle.setAttribute('stroke', cat.color);
        circle.setAttribute('stroke-width', '16');
        circle.setAttribute('stroke-dasharray', `${segLen} ${circumference - segLen}`);
        circle.setAttribute('stroke-dashoffset', String(-offset));
        circle.setAttribute('transform', 'rotate(-90 60 60)');
        circle.style.transition = 'all 0.6s ease';
        svg.appendChild(circle);

        offset += segLen;

        // Update legend
        const valEl = document.getElementById(cat.elId);
        if (valEl) valEl.textContent = `${catVal} kg`;
    });
}

// ============================================
// Leaderboard (Community Tab)
// ============================================
function loadLeaderboard(leaderboard) {
    const list = document.getElementById('leaderboardList');
    if (!list || !leaderboard) return;
    list.innerHTML = '';

    const medals = ['🥇', '🥈', '🥉'];

    leaderboard.forEach((entry, i) => {
        const el = document.createElement('div');
        el.className = 'lb-item';
        const rankClass = i < 3 ? ` lb-rank-${i + 1}` : '';
        el.innerHTML = `
            <span class="lb-rank${rankClass}">${i < 3 ? medals[i] : i + 1}</span>
            <span class="lb-name">${entry.user}</span>
            <span class="lb-score">${entry.co2_kg} kg CO₂</span>
        `;
        list.appendChild(el);
    });

    if (leaderboard.length === 0) {
        list.innerHTML = '<div class="lb-item"><span class="lb-name" style="color:var(--text-muted)">No warriors yet — be the first!</span></div>';
    }
}

// ============================================
// Community Challenge (Community Tab)
// ============================================
function updateChallenge(totalCO2, totalActions, leaderboardCount) {
    const challengeGoal = 500;
    const pct = Math.min(100, (totalCO2 / challengeGoal) * 100);

    const bar = document.getElementById('challengeBar');
    const current = document.getElementById('challengeCurrent');
    const participants = document.getElementById('challengeParticipants');

    if (bar) bar.style.width = `${pct}%`;
    if (current) current.textContent = `${totalCO2} kg`;
    if (participants) participants.textContent = `${leaderboardCount} participant${leaderboardCount !== 1 ? 's' : ''}`;
}

// ============================================
// Activity Feed (Community Tab)
// ============================================
function loadActivityFeed(recent) {
    const list = document.getElementById('feedList');
    if (!list || !recent) return;
    list.innerHTML = '';

    const actionIcons = {
        'recycle': '♻️', 'cycle': '🚲', 'bike': '🚲', 'walk': '🚶',
        'bus': '🚌', 'train': '🚂', 'vegan': '🥗', 'plant': '🌱',
        'solar': '☀️', 'tree': '🌳', 'shower': '🚿', 'led': '💡',
    };

    recent.forEach(entry => {
        const action = entry.action || '';
        const lower = action.toLowerCase();
        let icon = '💚';
        for (const [key, emoji] of Object.entries(actionIcons)) {
            if (lower.includes(key)) { icon = emoji; break; }
        }

        const timeAgo = entry.timestamp ? getTimeAgo(entry.timestamp) : 'recently';

        const el = document.createElement('div');
        el.className = 'feed-item';
        el.innerHTML = `
            <span class="feed-icon">${icon}</span>
            <span class="feed-text"><strong>${entry.user || 'anonymous'}</strong> ${action}</span>
            ${entry.co2_kg ? `<span class="feed-co2">-${entry.co2_kg} kg</span>` : ''}
            <span class="feed-time">${timeAgo}</span>
        `;
        list.appendChild(el);
    });

    if (recent.length === 0) {
        list.innerHTML = '<div class="feed-item"><span class="feed-icon">⏳</span><span class="feed-text">No activity yet — log your first eco-action!</span></div>';
    }
}

function getTimeAgo(timestamp) {
    try {
        const now = new Date();
        const then = new Date(timestamp);
        const diff = Math.floor((now - then) / 1000);
        if (diff < 60) return 'just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return `${Math.floor(diff / 86400)}d ago`;
    } catch { return 'recently'; }
}

// ============================================
// Feature 6: Carbon Footprint Calculator
// ============================================
async function calculateFootprint() {
    const data = {
        transport: document.getElementById('calcTransport').value,
        diet: document.getElementById('calcDiet').value,
        energy: document.getElementById('calcEnergy').value,
        flights: document.getElementById('calcFlights').value,
        household: parseInt(document.getElementById('calcHousehold').value) || 1,
    };

    const btn = document.querySelector('.calc-submit');
    btn.textContent = '⏳ Calculating...';
    btn.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/api/carbon-footprint`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        const result = await res.json();

        document.getElementById('calcResults').style.display = 'block';
        document.getElementById('calcTotalKg').textContent = result.total_kg.toLocaleString();
        document.getElementById('calcRating').textContent = result.rating;

        const ukSign = result.vs_uk_pct >= 0 ? '+' : '';
        const globalSign = result.vs_global_pct >= 0 ? '+' : '';
        document.getElementById('calcVsUk').innerHTML = `🇬🇧 ${ukSign}${result.vs_uk_pct}% vs UK avg (${result.uk_avg.toLocaleString()} kg)`;
        document.getElementById('calcVsGlobal').innerHTML = `🌍 ${globalSign}${result.vs_global_pct}% vs Global avg (${result.global_avg.toLocaleString()} kg)`;

        // Breakdown bars
        const breakdown = document.getElementById('calcBreakdown');
        breakdown.innerHTML = '';
        const colors = { transport: '#4ade80', diet: '#60a5fa', energy: '#a78bfa', flights: '#fbbf24' };
        for (const [key, val] of Object.entries(result.breakdown)) {
            breakdown.innerHTML += `
                <div class="calc-bar-item">
                    <div class="calc-bar-label">${val.label}</div>
                    <div class="calc-bar-bg"><div class="calc-bar-fill" style="width:${val.pct}%;background:${colors[key]}"></div></div>
                    <div class="calc-bar-val">${val.kg.toLocaleString()} kg (${val.pct}%)</div>
                </div>`;
        }

        // Strategies
        const strategies = document.getElementById('calcStrategies');
        strategies.innerHTML = '';
        const diffIcons = { easy: '🟢', medium: '🟡', hard: '🔴' };
        (result.strategies || []).forEach(s => {
            strategies.innerHTML += `
                <div class="calc-strategy">
                    <span class="calc-strat-diff">${diffIcons[s.difficulty] || '⚪'}</span>
                    <span class="calc-strat-action">${s.action}</span>
                    <span class="calc-strat-save">saves ~${s.savings_kg} kg/yr</span>
                </div>`;
        });
    } catch (err) {
        console.error('Footprint calc error:', err);
    }

    btn.textContent = 'Calculate My Footprint';
    btn.disabled = false;
}

// ============================================
// Feature 7: Historical Climate Trends
// ============================================
let trendChartInstance = null;

async function loadTrendChart(city) {
    try {
        const res = await fetch(`${API_BASE}/api/climate/history/${encodeURIComponent(city)}`);
        const data = await res.json();

        const canvas = document.getElementById('trendChart');
        const emptyMsg = document.getElementById('trendEmpty');
        if (!canvas) return;

        if (!data.history || data.history.length === 0) {
            canvas.style.display = 'none';
            if (emptyMsg) emptyMsg.style.display = 'block';
            return;
        }
        canvas.style.display = 'block';
        if (emptyMsg) emptyMsg.style.display = 'none';

        const labels = data.history.map(h => {
            const d = new Date(h.timestamp);
            return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
        });
        const aqiData = data.history.map(h => h.aqi);
        const tempData = data.history.map(h => h.temp);

        if (trendChartInstance) trendChartInstance.destroy();

        trendChartInstance = new Chart(canvas.getContext('2d'), {
            type: 'line',
            data: {
                labels,
                datasets: [
                    {
                        label: 'AQI',
                        data: aqiData,
                        borderColor: '#f87171',
                        backgroundColor: 'rgba(248,113,113,0.1)',
                        fill: true,
                        tension: 0.4,
                        yAxisID: 'y',
                    },
                    {
                        label: 'Temp (°C)',
                        data: tempData,
                        borderColor: '#60a5fa',
                        backgroundColor: 'rgba(96,165,250,0.1)',
                        fill: true,
                        tension: 0.4,
                        yAxisID: 'y1',
                    },
                ],
            },
            options: {
                responsive: true,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { labels: { color: '#94a3b8', font: { family: 'Inter' } } },
                },
                scales: {
                    x: {
                        ticks: { color: '#475569', maxTicksLimit: 8 },
                        grid: { color: 'rgba(255,255,255,0.04)' },
                    },
                    y: {
                        type: 'linear', position: 'left',
                        title: { display: true, text: 'AQI', color: '#f87171' },
                        ticks: { color: '#f87171' },
                        grid: { color: 'rgba(255,255,255,0.04)' },
                    },
                    y1: {
                        type: 'linear', position: 'right',
                        title: { display: true, text: '°C', color: '#60a5fa' },
                        ticks: { color: '#60a5fa' },
                        grid: { drawOnChartArea: false },
                    },
                },
            },
        });
    } catch (err) {
        console.error('Trend chart error:', err);
    }
}

// ============================================
// Feature 8: Shareable Impact Cards
// ============================================
function shareImpact() {
    window.open(`${API_BASE}/api/impact-card/${WALLET_USER}`, '_blank');
}

// ============================================
// Feature 9: Policy & Flood Alerts
// ============================================
async function loadPolicyAlerts(city) {
    const list = document.getElementById('policyAlertsList');
    if (!list) return;

    try {
        const res = await fetch(`${API_BASE}/api/policy-alerts/${encodeURIComponent(city)}`);
        const data = await res.json();

        if (!data.alerts || data.alerts.length === 0) {
            list.innerHTML = '<div class="policy-empty">✅ No active flood or policy warnings for this area.</div>';
            return;
        }

        list.innerHTML = '';
        data.alerts.forEach(alert => {
            const el = document.createElement('div');
            el.className = `policy-alert-item severity-${alert.severity}`;
            el.innerHTML = `
                <div class="policy-alert-header">
                    <span class="policy-severity">${alert.severity_icon} ${alert.severity_label}</span>
                    <span class="policy-area">${alert.area || 'UK'}</span>
                </div>
                <div class="policy-desc">${alert.description}</div>
                ${alert.message ? `<div class="policy-msg">${alert.message.substring(0, 200)}${alert.message.length > 200 ? '...' : ''}</div>` : ''}
                ${alert.time_raised ? `<div class="policy-time">Raised: ${new Date(alert.time_raised).toLocaleString()}</div>` : ''}
            `;
            list.appendChild(el);
        });
    } catch (err) {
        list.innerHTML = '<div class="policy-empty">⚠️ Could not fetch government alerts.</div>';
    }
}

// ============================================
// Operator Guided Tour (Initialization Sequence)
// ============================================
const tourSteps = [
    {
        target: '#walletCard',
        title: 'GREEN WALLET',
        text: 'Track your green credits and eco-rank here. Log eco-actions to earn credits and level up!'
    },
    {
        target: '#globeCard',
        title: 'CLIMATE MAP',
        text: 'Explore live climate data from cities around the world — weather, air quality, and NASA disaster alerts.'
    },
    {
        target: '#questCard',
        title: 'DAILY CHALLENGES',
        text: 'Complete daily eco-challenges to earn bonus XP and keep your streak going!'
    },
    {
        target: '#chatBubble',
        title: 'AI ASSISTANT',
        text: 'Chat with our AI to get climate info, eco-tips, or ask questions about the environment.'
    }
];

let currentTourStep = 0;
let tourActive = false;

function initTour() {
    if (localStorage.getItem('greenclawTourCompleted') === 'true') return;

    // Slight delay to allow UI to render and globe to map
    setTimeout(() => {
        startTour();
    }, 1500);
}

function startTour() {
    tourActive = true;
    currentTourStep = 0;

    document.getElementById('tourOverlay').style.display = 'block';
    const overlay = document.getElementById('tourOverlay');
    const tooltip = document.getElementById('tourTooltip');

    // Trigger reflow for transition
    void overlay.offsetWidth;
    overlay.style.opacity = '1';

    tooltip.style.display = 'block';

    // Switch to appropriate tab if needed (assuming intelligence tab for globe)
    // Actually, all targets except Earth are on Home, Earth is on Intelligence

    renderTourStep();
}

function endTour() {
    tourActive = false;
    localStorage.setItem('greenclawTourCompleted', 'true');

    const overlay = document.getElementById('tourOverlay');
    const tooltip = document.getElementById('tourTooltip');

    overlay.style.opacity = '0';
    tooltip.classList.remove('active');

    // Remove previous highlights
    document.querySelectorAll('.tour-highlight').forEach(el => el.classList.remove('tour-highlight'));

    setTimeout(() => {
        overlay.style.display = 'none';
        tooltip.style.display = 'none';
    }, 500);
}

function skipTour() {
    endTour();
}

function nextTourStep() {
    currentTourStep++;
    if (currentTourStep >= tourSteps.length) {
        endTour();
    } else {
        renderTourStep();
    }
}

function renderTourStep() {
    const step = tourSteps[currentTourStep];
    const tooltip = document.getElementById('tourTooltip');
    const titleEl = tooltip.querySelector('.tour-title');
    const textEl = document.getElementById('tourText');
    const progressEl = document.getElementById('tourProgress');
    const nextBtn = tooltip.querySelector('.tour-btn-next');

    // Remove previous highlights
    document.querySelectorAll('.tour-highlight').forEach(el => el.classList.remove('tour-highlight'));

    // Auto-switch tabs to ensure element is visible
    if (step.target === '#walletCard' || step.target === '#questCard') {
        switchTab('home');
    } else if (step.target === '#globeCard') {
        switchTab('intelligence');
    }

    // Use setTimeout to allow DOM to switch tabs if necessary
    setTimeout(() => {
        const targetEl = document.querySelector(step.target);
        if (targetEl) {
            targetEl.classList.add('tour-highlight');
            targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });

            // Wait for scroll
            setTimeout(() => {
                const rect = targetEl.getBoundingClientRect();
                positionTooltip(rect, tooltip);

                titleEl.textContent = step.title;
                textEl.textContent = step.text;
                progressEl.textContent = `${currentTourStep + 1}/${tourSteps.length}`;

                if (currentTourStep === tourSteps.length - 1) {
                    nextBtn.textContent = 'Finish';
                } else {
                    nextBtn.textContent = 'Next ⟶';
                }

                tooltip.classList.add('active');
            }, 300); // Wait for scroll animation
        } else {
            // Target not found, skip step
            nextTourStep();
        }
    }, 100);
}

function positionTooltip(targetRect, tooltip) {
    const tooltipWidth = tooltip.offsetWidth || 320;
    const tooltipHeight = tooltip.offsetHeight || 180;

    // Calculate horizontal center relative to the full document width (including scroll)
    let left = targetRect.left + window.scrollX + (targetRect.width / 2) - (tooltipWidth / 2);

    // Ensure it doesn't overflow horizontally
    if (left < 10) left = 10;
    if (left + tooltipWidth > window.innerWidth + window.scrollX - 10) {
        left = window.innerWidth + window.scrollX - tooltipWidth - 10;
    }

    // Default vertical position: Bottom
    let top = targetRect.bottom + window.scrollY + 15;

    // Check available space below the element in the CURRENT viewport
    const spaceBelow = window.innerHeight - targetRect.bottom;

    // If there is not enough space below (e.g. less than tooltip height + padding), put it ABOVE the element
    if (spaceBelow < tooltipHeight + 30) {
        top = targetRect.top + window.scrollY - tooltipHeight - 15;

        // If it also overflows the top, clamp it inside the viewport
        if ((top - window.scrollY) < 10) {
            top = window.scrollY + 10;
        }
    }

    tooltip.style.top = `${top}px`;
    tooltip.style.left = `${left}px`;
}

// Hook tour init into window load
window.addEventListener('load', initTour);
