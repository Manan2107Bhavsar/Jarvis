// JARVIS HUD Interface - Main JavaScript
// Handles animations, particle system, and WebSocket integration

// ===== CONFIGURATION =====
const WS_URL = 'ws://localhost:8765';
const PARTICLE_COUNT = 60;
const RING_COUNT = 3;

// ===== STATE =====
let ws = null;
let reconnectInterval = null;
let conversationCount = 0;
let startTime = Date.now();
let animationFrame = 0;

// ===== DOM ELEMENTS =====
const elements = {
    particlesContainer: document.getElementById('particles-container'),
    commandInput: document.getElementById('commandInput'),
    sendBtn: document.getElementById('sendBtn'),
    conversationLog: document.getElementById('conversationLog'),
    historyToggle: document.getElementById('historyToggle'),
    historySidebar: document.getElementById('historySidebar'),
    historyClose: document.getElementById('historyClose'),
    historyList: document.getElementById('historyList'),
    historySearch: document.getElementById('historySearch'),
    uptime: document.getElementById('uptime'),
    neuralStatus: document.getElementById('neuralStatus'),
    inputStatus: document.getElementById('inputStatus'),
    tempGraph: document.getElementById('temp-graph')
};

// ===== UTILITY FUNCTIONS =====
const random = (min, max) => Math.random() * (max - min) + min;

// ===== PARTICLE SYSTEM =====
function createParticles() {
    if (!elements.particlesContainer) return;

    for (let i = 0; i < PARTICLE_COUNT; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';

        // Random position
        particle.style.left = random(0, 100) + '%';
        particle.style.top = random(100, 110) + '%';

        // Random animation duration and delay
        const duration = random(8, 15);
        const delay = random(0, 5);
        particle.style.animationDuration = duration + 's';
        particle.style.animationDelay = delay + 's';

        // Random horizontal drift
        particle.style.setProperty('--drift', random(-50, 50) + 'px');

        elements.particlesContainer.appendChild(particle);
    }
}

// ===== ARC REACTOR RINGS =====
// ===== ARC REACTOR RINGS =====
function createReactorRings() {
    const rings = [
        { id: 'ring-outer', radius: 180, segments: 12, strokeWidth: 2, type: 'arc' },
        { id: 'ring-middle', radius: 140, segments: 8, strokeWidth: 2.5, type: 'arc' },
        { id: 'ring-inner', radius: 100, segments: 6, strokeWidth: 3, type: 'arc' },
        { id: 'ring-ticks', radius: 160, segments: 36, strokeWidth: 2, type: 'tick' }
    ];

    rings.forEach(ring => {
        const group = document.getElementById(ring.id);
        if (!group) return;

        // Clear existing content
        group.innerHTML = '';

        if (ring.type === 'arc') {
            const circumference = 2 * Math.PI * ring.radius;
            const segmentLength = circumference / ring.segments;

            for (let i = 0; i < ring.segments; i++) {
                const angle = (360 / ring.segments) * i;

                // Create arc segment
                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                const startAngle = (angle - 15) * Math.PI / 180;
                const endAngle = (angle + 15) * Math.PI / 180;

                const x1 = 250 + ring.radius * Math.cos(startAngle);
                const y1 = 250 + ring.radius * Math.sin(startAngle);
                const x2 = 250 + ring.radius * Math.cos(endAngle);
                const y2 = 250 + ring.radius * Math.sin(endAngle);

                path.setAttribute('d', `M ${x1} ${y1} A ${ring.radius} ${ring.radius} 0 0 1 ${x2} ${y2}`);
                path.setAttribute('class', 'ring-segment');
                path.setAttribute('stroke-width', ring.strokeWidth);

                group.appendChild(path);
            }
        } else if (ring.type === 'tick') {
            for (let i = 0; i < ring.segments; i++) {
                const angle = (360 / ring.segments) * i;
                const rad = angle * Math.PI / 180;

                const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                const x1 = 250 + (ring.radius - 5) * Math.cos(rad);
                const y1 = 250 + (ring.radius - 5) * Math.sin(rad);
                const x2 = 250 + (ring.radius + 5) * Math.cos(rad);
                const y2 = 250 + (ring.radius + 5) * Math.sin(rad);

                line.setAttribute('x1', x1);
                line.setAttribute('y1', y1);
                line.setAttribute('x2', x2);
                line.setAttribute('y2', y2);
                line.setAttribute('class', 'ring-tick');
                line.setAttribute('stroke-width', ring.strokeWidth);

                group.appendChild(line);
            }
        }
    });
}

// ===== MINI GRAPH =====
function drawTemperatureGraph() {
    const canvas = elements.tempGraph;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Generate random data points
    const points = 20;
    const data = [];
    for (let i = 0; i < points; i++) {
        data.push(random(0.3, 0.8));
    }

    // Draw line graph
    ctx.strokeStyle = '#00f0ff';
    ctx.lineWidth = 2;
    ctx.shadowBlur = 10;
    ctx.shadowColor = 'rgba(0, 240, 255, 0.6)';

    ctx.beginPath();
    data.forEach((value, index) => {
        const x = (index / (points - 1)) * width;
        const y = height - (value * height);

        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    ctx.stroke();

    // Draw dots
    ctx.fillStyle = '#00f0ff';
    data.forEach((value, index) => {
        const x = (index / (points - 1)) * width;
        const y = height - (value * height);

        ctx.beginPath();
        ctx.arc(x, y, 2, 0, Math.PI * 2);
        ctx.fill();
    });
}

// ===== DYNAMIC DATA UPDATES =====
function updateRandomData() {
    // Update CPU/RAM bars
    const cpuBar = document.getElementById('cpu-bar');
    const ramBar = document.getElementById('ram-bar');

    if (cpuBar) {
        const cpuValue = random(30, 70);
        cpuBar.style.width = cpuValue + '%';
        cpuBar.nextElementSibling.textContent = Math.round(cpuValue) + '%';
    }

    if (ramBar) {
        const ramValue = random(40, 80);
        ramBar.style.width = ramValue + '%';
        ramBar.nextElementSibling.textContent = Math.round(ramValue) + '%';
    }

    // Update gauges
    updateGauge('gauge-1-progress', 'gauge-1-text', random(40, 90));
    updateGauge('gauge-2-progress', 'gauge-2-text', random(20, 60));

    // Update temperature
    const tempValue = document.getElementById('temp-value');
    if (tempValue) {
        tempValue.textContent = Math.round(random(20, 25)) + '°C';
    }
}

function updateGauge(progressId, textId, percentage) {
    const progress = document.getElementById(progressId);
    const text = document.getElementById(textId);

    if (progress && text) {
        const circumference = 2 * Math.PI * 40; // radius = 40
        const offset = circumference - (percentage / 100) * circumference;
        progress.style.strokeDashoffset = offset;
        text.textContent = Math.round(percentage) + '%';
    }
}

// ===== WEBSOCKET CONNECTION =====
function connectWebSocket() {
    try {
        ws = new WebSocket(WS_URL);

        ws.onopen = () => {
            console.log('✅ Connected to JARVIS backend');
            updateConnectionStatus(true);
            clearInterval(reconnectInterval);
            reconnectInterval = null;

            // Request history when connected
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'get_history',
                    payload: {}
                }));
            }
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        ws.onclose = () => {
            console.log('❌ Disconnected from JARVIS backend');
            updateConnectionStatus(false);

            if (!reconnectInterval) {
                reconnectInterval = setInterval(connectWebSocket, 5000);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

    } catch (error) {
        console.error('Connection error:', error);
        updateConnectionStatus(false);
    }
}

function updateConnectionStatus(connected) {
    if (elements.neuralStatus) {
        elements.neuralStatus.textContent = connected ? 'ONLINE' : 'OFFLINE';
        elements.neuralStatus.className = connected ? 'value status-online' : 'value';
        elements.neuralStatus.style.color = connected ? '#0f0' : '#f33';
    }

    if (elements.inputStatus) {
        elements.inputStatus.textContent = connected ? 'Ready' : 'Offline - Commands queued';
    }
}

function handleWebSocketMessage(data) {
    const { type, payload } = data;

    switch (type) {
        case 'status':
            updateSystemStatus(payload);
            break;
        case 'user_speech':
            addLogEntry('user', payload.text);
            break;
        case 'jarvis_response':
            addLogEntry('jarvis', payload.text);
            break;
        case 'state_change':
            updateReactorState(payload.state);
            break;
        case 'history_data':
            displayHistory(payload.history || []);
            break;
    }
}

function updateSystemStatus(status) {
    // Update any system status indicators
    if (status.voiceRecognition) {
        // Update voice status if needed
    }
}

function updateReactorState(state) {
    const core = document.querySelector('.core-main');
    const coreInner = document.querySelector('.core-inner');
    const rays = document.querySelector('.core-rays');

    if (!core) return;

    let color;
    let pulseSpeed;

    switch (state) {
        case 'listening':
            color = '#00ff88'; // Green
            pulseSpeed = '1s';
            break;
        case 'processing':
            color = '#ffaa00'; // Orange
            pulseSpeed = '0.5s';
            break;
        case 'speaking':
            color = '#aa00ff'; // Purple
            pulseSpeed = '1.5s';
            break;
        default:
            color = '#00f0ff'; // Cyan
            pulseSpeed = '2s';
    }

    core.style.fill = color;
    core.style.filter = `drop-shadow(0 0 20px ${color})`;
    core.style.animationDuration = pulseSpeed;

    if (coreInner) {
        coreInner.style.animationDuration = pulseSpeed;
    }

    if (rays) {
        const rayBeams = rays.querySelectorAll('.ray-beam');
        rayBeams.forEach(beam => {
            beam.style.stroke = color;
        });
    }
}

// ===== CONVERSATION LOG =====
function addLogEntry(sender, text) {
    const log = elements.conversationLog;
    if (!log) return;

    // Remove empty state
    const empty = log.querySelector('.conversation-empty');
    if (empty) empty.remove();

    const entry = document.createElement('div');
    entry.className = `log-entry ${sender}`;

    const time = new Date().toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });

    entry.innerHTML = `
        <span class="log-time">${time}</span>
        <span class="log-text">${escapeHtml(text)}</span>
    `;

    log.appendChild(entry);
    log.scrollTop = log.scrollHeight;

    if (sender === 'user') {
        conversationCount++;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===== COMMAND INPUT =====
function sendCommand() {
    const input = elements.commandInput;
    if (!input) return;

    const command = input.value.trim();
    if (!command) return;

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'text_command',
            payload: { text: command }
        }));
        addLogEntry('user', command);
    } else {
        addLogEntry('user', command + ' (Offline)');
        addLogEntry('system', 'Not connected to backend. Command queued.');
    }

    input.value = '';
    input.focus();
}

// ===== HISTORY SIDEBAR =====
function parseTimestamp(timestamp) {
    // Parse timestamp format: YYYYMMDD-HHMMSS
    if (!timestamp || timestamp.length < 8) return null;

    const year = parseInt(timestamp.substring(0, 4));
    const month = parseInt(timestamp.substring(4, 6)) - 1; // JS months are 0-indexed
    const day = parseInt(timestamp.substring(6, 8));

    return new Date(year, month, day);
}

function getDateLabel(date) {
    if (!date) return 'Unknown Date';

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const itemDate = new Date(date);
    itemDate.setHours(0, 0, 0, 0);

    if (itemDate.getTime() === today.getTime()) {
        return 'Today';
    } else if (itemDate.getTime() === yesterday.getTime()) {
        return 'Yesterday';
    } else {
        // Format as "Month Day, Year"
        const options = { year: 'numeric', month: 'long', day: 'numeric' };
        return itemDate.toLocaleDateString('en-US', options);
    }
}

function displayHistory(history) {
    const list = elements.historyList;
    if (!list) return;

    if (history.length === 0) {
        list.innerHTML = '<div class="history-empty">No history available</div>';
        return;
    }

    // Group history by date
    const groupedHistory = {};

    history.forEach(item => {
        const date = parseTimestamp(item.timestamp);
        const dateLabel = getDateLabel(date);

        if (!groupedHistory[dateLabel]) {
            groupedHistory[dateLabel] = {
                date: date,
                items: []
            };
        }

        groupedHistory[dateLabel].items.push(item);
    });

    // Sort date groups (most recent first)
    const sortedGroups = Object.entries(groupedHistory).sort((a, b) => {
        const dateA = a[1].date || new Date(0);
        const dateB = b[1].date || new Date(0);
        return dateB - dateA;
    });

    // Build HTML
    let html = '';

    sortedGroups.forEach(([dateLabel, group]) => {
        const folderId = `folder-${dateLabel.replace(/[^a-zA-Z0-9]/g, '-')}`;

        html += `
            <div class="history-date-folder">
                <div class="history-date-header" onclick="toggleHistoryFolder('${folderId}')">
                    <span class="history-date-icon">▶</span>
                    <span class="history-date-label">${dateLabel}</span>
                    <span class="history-date-count">${group.items.length}</span>
                </div>
                <div class="history-date-items" id="${folderId}">
                    ${group.items.map(item => `
                        <div class="history-item" onclick="addLogEntry('${item.role}', '${escapeHtml(item.text).replace(/'/g, "\\'")}')" >
                            <div class="history-item-role">
                                ${item.role}
                            </div>
                            <div class="history-item-text">
                                ${escapeHtml(item.text)}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    });

    list.innerHTML = html;
}

window.toggleHistoryFolder = function (folderId) {
    const folder = document.getElementById(folderId);
    if (!folder) return;

    const header = folder.previousElementSibling;
    const icon = header.querySelector('.history-date-icon');

    if (folder.classList.contains('open')) {
        folder.classList.remove('open');
        icon.textContent = '▶';
    } else {
        folder.classList.add('open');
        icon.textContent = '▼';
    }
}

function toggleFullScreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(err => {
            console.error(`Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
        });
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
    }
}

// ===== UPTIME COUNTER =====
function updateUptime() {
    const elapsed = Date.now() - startTime;
    const hours = Math.floor(elapsed / 3600000).toString().padStart(2, '0');
    const minutes = Math.floor((elapsed % 3600000) / 60000).toString().padStart(2, '0');
    const seconds = Math.floor((elapsed % 60000) / 1000).toString().padStart(2, '0');

    if (elements.uptime) {
        elements.uptime.textContent = `${hours}:${minutes}:${seconds}`;
    }
}

// ===== EVENT LISTENERS =====
function setupEventListeners() {
    // Send button
    if (elements.sendBtn) {
        elements.sendBtn.addEventListener('click', sendCommand);
    }

    // Command input - Enter key
    if (elements.commandInput) {
        elements.commandInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendCommand();
            }
        });
    }

    // History toggle
    if (elements.historyToggle) {
        elements.historyToggle.addEventListener('click', () => {
            if (elements.historySidebar) {
                elements.historySidebar.classList.add('open');

                // Request history from backend
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'get_history',
                        payload: {}
                    }));
                }
            }
        });
    }

    // History close
    if (elements.historyClose) {
        elements.historyClose.addEventListener('click', () => {
            if (elements.historySidebar) {
                elements.historySidebar.classList.remove('open');
            }
        });
    }

    // History search
    if (elements.historySearch) {
        elements.historySearch.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const items = elements.historyList.querySelectorAll('.history-item');
            const folders = elements.historyList.querySelectorAll('.history-date-folder');

            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                const matches = text.includes(query);
                item.style.display = matches ? 'block' : 'none';

                // If item matches, expand its parent folder
                if (matches && query) {
                    const parentFolder = item.closest('.history-date-items');
                    if (parentFolder && !parentFolder.classList.contains('open')) {
                        parentFolder.classList.add('open');
                        const icon = parentFolder.previousElementSibling.querySelector('.history-date-icon');
                        if (icon) icon.textContent = '▼';
                    }
                }
            });

            // Hide folders with no visible items
            folders.forEach(folder => {
                const itemsContainer = folder.querySelector('.history-date-items');
                const visibleItems = Array.from(itemsContainer.querySelectorAll('.history-item'))
                    .filter(item => item.style.display !== 'none');

                folder.style.display = visibleItems.length > 0 ? 'block' : 'none';
            });
        });
    }

    // Fullscreen toggle
    const fullscreenToggle = document.getElementById('fullscreenToggle');
    if (fullscreenToggle) {
        fullscreenToggle.addEventListener('click', toggleFullScreen);
    }
}

// ===== INITIALIZATION =====
function init() {
    console.log('🚀 Initializing JARVIS HUD...');

    // Create visual elements
    createParticles();
    createReactorRings();
    drawTemperatureGraph();

    // Setup event listeners
    setupEventListeners();

    // Connect to WebSocket
    connectWebSocket();

    // Start periodic updates
    setInterval(updateUptime, 1000);
    setInterval(updateRandomData, 3000);
    setInterval(drawTemperatureGraph, 5000);

    // Focus command input
    if (elements.commandInput) {
        elements.commandInput.focus();
    }

    console.log('✅ JARVIS HUD initialized');
}

// Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

