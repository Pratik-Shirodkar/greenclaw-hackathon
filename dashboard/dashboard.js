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
    initGlobe(); // Initialize 3D Threat Map
    loadCityData();
    initTipDots();
    loadRandomFact();
    pollAlerts();

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
    const input = document.getElementById('citySearch');
    const city = input.value.trim() || currentCity;
    currentCity = city;

    try {
        const res = await fetch(`${API_BASE}/api/climate/${encodeURIComponent(city)}`);
        const data = await res.json();
        updateWeather(data.weather, city);
        updateAQI(data.aqi);
        loadDisasters(data.disasters);
        updateGlobeData(data); // Feed to Threat Map
        resetRiskPanel();
    } catch (err) {
        console.error('Failed to load climate data:', err);
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

        // Add to log
        const log = document.getElementById('actionLog');
        const item = document.createElement('div');
        item.className = 'log-item';
        item.innerHTML = `<span class="log-icon">${entry.emoji}</span><span>${action}</span><span class="log-co2">-${entry.co2_kg} kg</span>`;
        log.insertBefore(item, log.firstChild);

        // Refresh stats
        await refreshCommunityStats();
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
    setTimeout(() => toast.remove(), 30000);
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
            addChatMessage('bot', '👋 Hey! I\'m **GreenClaw** 🌍🦞\n\nAsk me about weather, climate risks, eco-tips, or say **help**!');
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
        document.getElementById('quizResult').innerHTML = '🎉 AMAZING! You\'re a true Earth Expert! ⭐';
        document.getElementById('quizResult').style.color = '#4ade80';
    } else {
        btn.classList.add('selected-wrong');
        document.getElementById('quizResult').innerHTML = '💪 Not quite, but great try! Keep learning!';
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
