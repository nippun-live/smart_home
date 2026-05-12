const POLL_INTERVALS = {
  latest: 1000,
  events: 5000,
  history: 15000,
  status: 5000,
};

const state = {
  latest: null,
  events: [],
  history: [],
  status: null,
  thresholds: null,
  endpointModes: {
    latest: "mock",
    events: "mock",
    history: "mock",
    status: "mock",
  },
  source: "loading",
  lastSync: null,
  route: "dashboard",
};

const elements = {
  connectionChip: document.querySelector("#connection-chip"),
  connectionLabel: document.querySelector("#connection-label"),
  lastSync: document.querySelector("#last-sync"),
  modeBanner: document.querySelector("#mode-banner"),
  modeLabel: document.querySelector("#mode-label"),
  modeCopy: document.querySelector("#mode-copy"),
  navButtons: [...document.querySelectorAll(".nav-pill")],
  views: [...document.querySelectorAll(".view")],
  heroSeverity: document.querySelector("#hero-severity"),
  heroEventTitle: document.querySelector("#hero-event-title"),
  heroEventMessage: document.querySelector("#hero-event-message"),
  heroEventTime: document.querySelector("#hero-event-time"),
  heroOccupancy: document.querySelector("#hero-occupancy"),
  snapshotImage: document.querySelector("#snapshot-image"),
  snapshotEmpty: document.querySelector("#snapshot-empty"),
  sensorHealth: document.querySelector("#sensor-health"),
  sensorHealthLarge: document.querySelector("#sensor-health-large"),
  systemStatus: document.querySelector("#system-status"),
  systemDisk: document.querySelector("#system-disk"),
  systemIp: document.querySelector("#system-ip"),
  systemUptime: document.querySelector("#system-uptime"),
  systemCpu: document.querySelector("#system-cpu"),
  eventList: document.querySelector("#event-list"),
  eventTemplate: document.querySelector("#event-item-template"),
  eventsSummary: document.querySelector("#events-summary"),
  historySummary: document.querySelector("#history-summary"),
  settingsSummary: document.querySelector("#settings-summary"),
  statusSummary: document.querySelector("#status-summary"),
  statusSource: document.querySelector("#status-source"),
  statusPacketTime: document.querySelector("#status-packet-time"),
  statusEventCount: document.querySelector("#status-event-count"),
  statusHistoryCount: document.querySelector("#status-history-count"),
  actionResponse: document.querySelector("#action-response"),
  thresholdForm: document.querySelector("#threshold-form"),
  forceRefresh: document.querySelector("#force-refresh"),
  triggerCapture: document.querySelector("#trigger-capture"),
  triggerLed: document.querySelector("#trigger-led"),
  thresholdInputs: [...document.querySelectorAll("#threshold-form input[name]")],
};

const metricBindings = {
  temperature: {
    value: document.querySelector("#metric-temperature"),
    foot: document.querySelector("#metric-temperature-foot"),
  },
  humidity: {
    value: document.querySelector("#metric-humidity"),
    foot: document.querySelector("#metric-humidity-foot"),
  },
  pressure: {
    value: document.querySelector("#metric-pressure"),
    foot: document.querySelector("#metric-pressure-foot"),
  },
  noise: {
    value: document.querySelector("#metric-noise"),
    foot: document.querySelector("#metric-noise-foot"),
  },
  distance: {
    value: document.querySelector("#metric-distance"),
    foot: document.querySelector("#metric-distance-foot"),
  },
  occupancy: {
    value: document.querySelector("#metric-occupancy"),
    foot: document.querySelector("#metric-occupancy-foot"),
  },
};

const chartBindings = {
  temperature_c: {
    canvas: document.querySelector("#chart-temperature"),
    label: document.querySelector("#chart-temp-range"),
    color: "#4af0ae",
    unit: "°C",
  },
  humidity_percent: {
    canvas: document.querySelector("#chart-humidity"),
    label: document.querySelector("#chart-humidity-range"),
    color: "#73c1ff",
    unit: "%",
  },
  pressure_hpa: {
    canvas: document.querySelector("#chart-pressure"),
    label: document.querySelector("#chart-pressure-range"),
    color: "#ffd76f",
    unit: "hPa",
  },
  noise_score: {
    canvas: document.querySelector("#chart-noise"),
    label: document.querySelector("#chart-noise-range"),
    color: "#ff965f",
    unit: "",
  },
};

const MOCK_CONFIG = {
  thresholds: {
    temperature_high_c: 30,
    humidity_high_percent: 70,
    motion_delta_cm: 25,
    presence_distance_cm: 80,
    noise_threshold: 0.7,
  },
};

const API_BASE = window.location.port === "8000"
  ? ""
  : `${window.location.protocol}//${window.location.hostname}:8000`;

function apiUrl(path) {
  if (!path) return path;
  if (/^https?:\/\//i.test(path) || path.startsWith("data:")) return path;
  return `${API_BASE}${path}`;
}

function routeFromLocation() {
  const hash = window.location.hash.replace("#", "").trim();
  const path = window.location.pathname.split("/").filter(Boolean).pop();
  const requested = hash || path || "dashboard";
  return ["dashboard", "events", "history", "settings", "status"].includes(requested)
    ? requested
    : "dashboard";
}

function setRoute(route, pushHistory = true) {
  state.route = route;

  elements.navButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.route === route);
  });

  elements.views.forEach((view) => {
    view.classList.toggle("active", view.dataset.view === route);
  });

  if (pushHistory) {
    history.replaceState({ route }, "", `${window.location.pathname}#${route}`);
  }
}

function setConnectionState(kind, label, copy = "") {
  elements.connectionChip.dataset.state = kind;
  elements.connectionLabel.textContent = label;

  if (!copy) {
    elements.modeBanner.hidden = true;
    return;
  }

  elements.modeBanner.hidden = false;
  elements.modeLabel.textContent = kind === "mock" ? "Mock mode" : "Disconnected";
  elements.modeCopy.textContent = copy;
}

function markSynced() {
  state.lastSync = new Date();
  elements.lastSync.textContent = `${state.lastSync.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}`;
}

function formatTimestamp(value) {
  if (!value) return "Unavailable";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatNumber(value, unit = "", digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return `${Number(value).toFixed(digits)}${unit ? ` ${unit}` : ""}`;
}

function formatPercent(value) {
  return formatNumber(value, "%", 0);
}

function formatUptime(totalSeconds) {
  if (!Number.isFinite(totalSeconds)) return "--";
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  return `${hours}h ${minutes}m`;
}

function titleFromEventType(type) {
  return (type || "No event")
    .toLowerCase()
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function severityTone(severity) {
  if (severity === "high") return "alert";
  if (severity === "medium") return "warning";
  return "normal";
}

function healthTone(value) {
  const normalized = (value || "offline").toLowerCase();
  if (normalized === "ok" || normalized === "online") return "ok";
  if (normalized === "warning" || normalized === "degraded") return "warning";
  return "offline";
}

function applyMetricTone(binding, tone) {
  binding.value.closest(".metric-card").dataset.tone = tone;
}

function renderLatest() {
  const latest = state.latest;
  const lastEvent = newestEvent(latest?.last_event, state.events[0]);
  const system = latest?.system || state.status || {};
  const occupancy = latest?.occupancy;
  const health = latest?.sensor_health || {};

  metricBindings.temperature.value.textContent = formatNumber(latest?.temperature_c, "°C");
  metricBindings.temperature.foot.textContent = latest ? "Environmental reading" : "Waiting for sensor";
  applyMetricTone(metricBindings.temperature, latest?.temperature_c > 30 ? "warning" : "normal");

  metricBindings.humidity.value.textContent = formatPercent(latest?.humidity_percent);
  metricBindings.humidity.foot.textContent = latest ? "Relative humidity" : "Waiting for sensor";
  applyMetricTone(metricBindings.humidity, latest?.humidity_percent > 70 ? "warning" : "normal");

  metricBindings.pressure.value.textContent = formatNumber(latest?.pressure_hpa, "hPa");
  metricBindings.pressure.foot.textContent = latest ? "Atmospheric pressure" : "Waiting for sensor";
  applyMetricTone(metricBindings.pressure, "normal");

  metricBindings.noise.value.textContent = formatNumber(latest?.noise_score, "", 2);
  metricBindings.noise.foot.textContent = latest ? "Rolling amplitude score" : "Waiting for sensor";
  applyMetricTone(metricBindings.noise, latest?.noise_score > 0.7 ? "alert" : "normal");

  metricBindings.distance.value.textContent = formatNumber(latest?.distance_cm, "cm");
  metricBindings.distance.foot.textContent = latest ? "Ultrasonic distance" : "Waiting for sensor";
  applyMetricTone(metricBindings.distance, latest?.distance_cm < 80 ? "warning" : "normal");

  metricBindings.occupancy.value.textContent = occupancy === true ? "Detected" : occupancy === false ? "Clear" : "--";
  metricBindings.occupancy.foot.textContent = latest ? "Presence estimate" : "Waiting for sensor";
  applyMetricTone(metricBindings.occupancy, occupancy === true ? "warning" : "normal");

  elements.heroEventTitle.textContent = lastEvent ? titleFromEventType(lastEvent.event_type) : "Waiting for event stream";
  elements.heroEventMessage.textContent = lastEvent?.message || "The hub will surface motion, noise, and environmental alerts here.";
  elements.heroEventTime.textContent = lastEvent ? formatTimestamp(lastEvent.timestamp) : "No event yet";
  elements.heroOccupancy.textContent = occupancy === true ? "Occupied" : occupancy === false ? "No presence" : "Unknown";

  setSeverityBadge(elements.heroSeverity, lastEvent?.severity, lastEvent ? titleFromEventType(lastEvent.event_type) : "Standby");

  elements.systemStatus.textContent = system.status || "Unknown";
  elements.systemDisk.textContent = Number.isFinite(system.disk_free_gb) ? `${system.disk_free_gb.toFixed(1)} GB` : "--";
  elements.systemIp.textContent = system.ip_address || "--";
  elements.systemUptime.textContent = formatUptime(system.uptime_seconds);
  elements.systemCpu.textContent = system.cpu_temp_c ? `${Number(system.cpu_temp_c).toFixed(1)} °C` : "--";

  renderHealth(elements.sensorHealth, health);
  renderHealth(elements.sensorHealthLarge, health);

  const snapshotUrl = latest?.latest_media_url || state.events.find((event) => event.media_url)?.media_url || lastEvent?.media_url || "";
  if (snapshotUrl) {
    elements.snapshotImage.hidden = false;
    elements.snapshotImage.src = snapshotUrl;
    elements.snapshotEmpty.hidden = true;
  } else {
    elements.snapshotImage.hidden = true;
    elements.snapshotImage.removeAttribute("src");
    elements.snapshotEmpty.hidden = false;
  }
}

function renderHealth(container, sensorHealth) {
  const entries = Object.entries(sensorHealth || {});
  container.innerHTML = "";

  if (!entries.length) {
    container.innerHTML = '<div class="health-pill" data-state="offline"><span class="health-label">Sensors</span><span class="health-value">No health data yet</span></div>';
    return;
  }

  entries.forEach(([sensor, value]) => {
    const pill = document.createElement("div");
    pill.className = "health-pill";
    pill.dataset.state = healthTone(value);
    pill.innerHTML = `
      <span class="health-label">${sensor.replace(/_/g, " ")}</span>
      <span class="health-value">${String(value).toUpperCase()}</span>
    `;
    container.appendChild(pill);
  });
}

function setSeverityBadge(element, severity, label) {
  element.dataset.severity = severity || "low";
  element.textContent = label || "Standby";
}

function newestEvent(...events) {
  return events
    .filter(Boolean)
    .sort((left, right) => new Date(right.timestamp).getTime() - new Date(left.timestamp).getTime())[0] || null;
}

function renderEvents() {
  elements.eventList.innerHTML = "";

  if (!state.events.length) {
    elements.eventsSummary.textContent = "No events loaded yet.";
    elements.eventList.innerHTML = '<article class="event-card"><p class="event-type">No events yet</p><p class="event-message">Motion, noise, and environmental alerts will appear here.</p></article>';
    return;
  }

  const securityEvents = state.events.filter((event) =>
    ["MOTION_DETECTED", "LOUD_NOISE", "PRESENCE_DETECTED"].includes(event.event_type)
  ).length;

  elements.eventsSummary.textContent = `${state.events.length} events loaded, ${securityEvents} security-related.`;

  state.events.forEach((event) => {
    const fragment = elements.eventTemplate.content.cloneNode(true);
    const card = fragment.querySelector(".event-card");
    fragment.querySelector(".event-type").textContent = titleFromEventType(event.event_type);
    fragment.querySelector(".event-time").textContent = formatTimestamp(event.timestamp);
    fragment.querySelector(".event-message").textContent = event.message || "No message provided.";
    setSeverityBadge(fragment.querySelector(".severity-badge"), event.severity, event.severity || "low");

    const mediaWrap = fragment.querySelector(".event-media-wrap");
    const media = fragment.querySelector(".event-media");
    if (event.media_url) {
      media.src = event.media_url;
      mediaWrap.hidden = false;
    }

    card.dataset.tone = severityTone(event.severity);
    elements.eventList.appendChild(fragment);
  });
}

function renderHistory() {
  elements.historySummary.textContent = state.history.length
    ? `${state.history.length} history points loaded for graphing.`
    : "Graphs render from `/api/history?hours=24` when available.";

  Object.entries(chartBindings).forEach(([key, binding]) => {
    const values = state.history.map((point) => ({
      timestamp: point.timestamp,
      value: Number(point[key]),
    })).filter((point) => Number.isFinite(point.value));

    binding.label.textContent = values.length
      ? `${Math.min(...values.map((item) => item.value)).toFixed(1)} to ${Math.max(...values.map((item) => item.value)).toFixed(1)} ${binding.unit}`.trim()
      : "--";

    drawLineChart(binding.canvas, values, binding.color);
  });
}

function drawLineChart(canvas, points, color) {
  const context = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  context.clearRect(0, 0, width, height);

  context.fillStyle = "rgba(255,255,255,0.02)";
  context.fillRect(0, 0, width, height);

  context.strokeStyle = "rgba(141, 207, 207, 0.12)";
  context.lineWidth = 1;
  for (let index = 1; index < 4; index += 1) {
    const y = (height / 4) * index;
    context.beginPath();
    context.moveTo(0, y);
    context.lineTo(width, y);
    context.stroke();
  }

  if (!points.length) {
    context.fillStyle = "#8baeb1";
    context.font = "16px IBM Plex Sans";
    context.fillText("No history data", 24, height / 2);
    return;
  }

  const min = Math.min(...points.map((point) => point.value));
  const max = Math.max(...points.map((point) => point.value));
  const range = max - min || 1;
  const xStep = points.length > 1 ? width / (points.length - 1) : width / 2;

  context.strokeStyle = color;
  context.lineWidth = 3;
  context.beginPath();

  points.forEach((point, index) => {
    const x = points.length > 1 ? xStep * index : width / 2;
    const y = height - 28 - ((point.value - min) / range) * (height - 56);
    if (index === 0) {
      context.moveTo(x, y);
    } else {
      context.lineTo(x, y);
    }
  });

  context.stroke();
}

function renderStatus() {
  elements.statusSource.textContent = state.source;
  elements.statusPacketTime.textContent = formatTimestamp(state.latest?.timestamp);
  elements.statusEventCount.textContent = String(state.events.length);
  elements.statusHistoryCount.textContent = String(state.history.length);
  elements.statusSummary.textContent = state.source === "live"
    ? "Connected to FastAPI endpoints."
    : state.source === "mock"
      ? "Backend endpoints unavailable. Mock data keeps the UI demoable."
      : "Backend disconnected. The interface will recover when endpoints respond again.";
}

function renderAll() {
  renderLatest();
  renderEvents();
  renderHistory();
  renderStatus();
  renderThresholds();
}

function renderThresholds() {
  elements.thresholdInputs.forEach((input) => {
    const value = state.thresholds?.[input.name];
    if (value !== undefined && value !== null && document.activeElement !== input) {
      input.value = value;
    }
  });
}

async function fetchEndpoint(url, fallback) {
  try {
    const response = await fetch(apiUrl(url), { headers: { Accept: "application/json" } });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return {
      live: true,
      data: await response.json(),
    };
  } catch {
    return {
      live: false,
      data: fallback(),
    };
  }
}

async function loadLatest() {
  const result = await fetchEndpoint("/api/latest", () => mockLatestPacket());
  state.endpointModes.latest = result.live ? "live" : "mock";
  state.latest = normalizeLatest(result.data);
}

async function loadEvents() {
  const result = await fetchEndpoint("/api/events?limit=50", () => mockEvents());
  state.endpointModes.events = result.live ? "live" : "mock";
  state.events = normalizeEvents(result.data);
}

async function loadHistory() {
  const result = await fetchEndpoint("/api/history?hours=24", () => mockHistory());
  state.endpointModes.history = result.live ? "live" : "mock";
  state.history = normalizeHistory(result.data);
}

async function loadStatus() {
  const result = await fetchEndpoint("/api/status", () => mockStatus());
  state.endpointModes.status = result.live ? "live" : "mock";
  state.status = normalizeStatus(result.data);
}

async function loadThresholds() {
  const result = await fetchEndpoint("/api/config/thresholds", () => ({ ...MOCK_CONFIG.thresholds }));
  state.thresholds = normalizeThresholds(result.data);
  Object.assign(MOCK_CONFIG.thresholds, state.thresholds);
}

function updateSourceFromEndpoints() {
  const modes = Object.values(state.endpointModes);
  const allLive = modes.every((mode) => mode === "live");
  const anyLive = modes.some((mode) => mode === "live");

  if (allLive) {
    state.source = "live";
    setConnectionState("online", "Live backend", "");
    return;
  }

  if (anyLive) {
    state.source = "warning";
    setConnectionState("warning", "Partial backend", "Some endpoints are live, but one or more panels are using fallback data.");
    return;
  }

  if (state.source === "live" || state.source === "warning") {
    state.source = "offline";
    setConnectionState("offline", "Backend offline", "The dashboard is retaining mock fallback data until the backend returns.");
    return;
  }

  state.source = "mock";
  setConnectionState("mock", "Mock data", "Backend unavailable. Rendering realistic demo data.");
}

async function hydrateAll() {
  await Promise.all([loadLatest(), loadEvents(), loadHistory(), loadStatus(), loadThresholds()]);
  updateSourceFromEndpoints();
  markSynced();
  renderAll();
}

async function refreshPanel(loadFn) {
  await loadFn();
  updateSourceFromEndpoints();
  markSynced();
  renderAll();
}

function normalizeLatest(payload) {
  if (!payload || Array.isArray(payload)) return mockLatestPacket();
  return {
    ...payload,
    latest_media_url: apiUrl(payload.latest_media_url || ""),
    last_event: payload.last_event
      ? { ...payload.last_event, media_url: apiUrl(payload.last_event.media_url || "") }
      : null,
  };
}

function normalizeEvents(payload) {
  const events = Array.isArray(payload) ? payload : Array.isArray(payload?.events) ? payload.events : null;
  if (events) {
    return events.map((event) => ({
      ...event,
      media_url: apiUrl(event.media_url || ""),
    }));
  }
  return mockEvents();
}

function normalizeHistory(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.history)) return payload.history;
  return mockHistory();
}

function normalizeStatus(payload) {
  return payload && !Array.isArray(payload) ? payload : mockStatus();
}

function normalizeThresholds(payload) {
  const source = payload && !Array.isArray(payload) ? payload : MOCK_CONFIG.thresholds;
  return Object.fromEntries(
    Object.entries(MOCK_CONFIG.thresholds).map(([key, fallback]) => {
      const parsed = Number(source[key]);
      return [key, Number.isFinite(parsed) ? parsed : fallback];
    })
  );
}

function mockLatestPacket() {
  const now = new Date();
  const temperature = 24.3 + Math.sin(now.getMinutes() / 8) * 1.8;
  const humidity = 46 + Math.sin(now.getMinutes() / 10) * 6;
  const pressure = 1012.4 + Math.cos(now.getMinutes() / 9) * 1.3;
  const distance = 72 + Math.sin(now.getSeconds() / 7) * 18;
  const noise = 0.24 + Math.abs(Math.sin(now.getSeconds() / 4)) * 0.38;
  const occupancy = distance < MOCK_CONFIG.thresholds.presence_distance_cm;
  const events = mockEvents();

  return {
    timestamp: now.toISOString(),
    temperature_c: Number(temperature.toFixed(1)),
    humidity_percent: Number(humidity.toFixed(1)),
    pressure_hpa: Number(pressure.toFixed(1)),
    distance_cm: Number(distance.toFixed(1)),
    noise_score: Number(noise.toFixed(2)),
    occupancy,
    last_event: events[0],
    latest_media_url: events[0].media_url,
    system: mockStatus(),
    sensor_health: {
      aht20: "ok",
      dps310: "ok",
      ultrasonic: occupancy ? "warning" : "ok",
      microphone: noise > 0.55 ? "warning" : "ok",
      camera: "ok",
      storage: "ok",
    },
  };
}

function mockSnapshotData(label, accent, background) {
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="900" height="600" viewBox="0 0 900 600">
      <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="${background}" />
          <stop offset="100%" stop-color="#08161c" />
        </linearGradient>
      </defs>
      <rect width="900" height="600" fill="url(#bg)" />
      <circle cx="700" cy="130" r="110" fill="${accent}" fill-opacity="0.16" />
      <circle cx="180" cy="470" r="140" fill="#73c1ff" fill-opacity="0.12" />
      <rect x="72" y="78" width="756" height="444" rx="28" fill="rgba(4,16,21,0.34)" stroke="${accent}" stroke-opacity="0.5" />
      <text x="96" y="170" fill="#edf9f7" font-size="54" font-family="Segoe UI, Arial, sans-serif">Smart Home Hub</text>
      <text x="96" y="244" fill="${accent}" font-size="34" font-family="Segoe UI, Arial, sans-serif">${label}</text>
      <text x="96" y="318" fill="#8baeb1" font-size="24" font-family="Segoe UI, Arial, sans-serif">Mock snapshot for frontend testing before camera integration.</text>
      <text x="96" y="372" fill="#8baeb1" font-size="24" font-family="Segoe UI, Arial, sans-serif">Backend media URLs can replace this immediately.</text>
    </svg>
  `.trim();

  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

function mockEvents() {
  const base = Date.now();
  return [
    {
      id: 17,
      timestamp: new Date(base - 90 * 1000).toISOString(),
      event_type: "MOTION_DETECTED",
      severity: "medium",
      message: "Ultrasonic distance changed rapidly near the entry zone.",
      media_url: mockSnapshotData("Motion detected near entry zone", "#85f1f4", "#153742"),
      acknowledged: false,
    },
    {
      id: 16,
      timestamp: new Date(base - 8 * 60 * 1000).toISOString(),
      event_type: "LOUD_NOISE",
      severity: "high",
      message: "Noise score exceeded threshold for 0.5 seconds.",
      media_url: mockSnapshotData("Loud noise trigger", "#ff965f", "#35201a"),
      acknowledged: false,
    },
    {
      id: 15,
      timestamp: new Date(base - 24 * 60 * 1000).toISOString(),
      event_type: "HIGH_HUMIDITY",
      severity: "medium",
      message: "Humidity remained above configured threshold for 30 seconds.",
      media_url: "",
      acknowledged: true,
    },
    {
      id: 14,
      timestamp: new Date(base - 55 * 60 * 1000).toISOString(),
      event_type: "SYSTEM_ONLINE",
      severity: "low",
      message: "Services restarted and the hub returned to monitoring mode.",
      media_url: "",
      acknowledged: true,
    },
  ];
}

function mockHistory() {
  const now = Date.now();
  return Array.from({ length: 24 }, (_, index) => {
    const hoursAgo = 23 - index;
    const timestamp = new Date(now - hoursAgo * 60 * 60 * 1000).toISOString();
    const temperature = 22 + Math.sin(index / 4) * 3 + (index > 18 ? 1 : 0);
    const humidity = 44 + Math.cos(index / 5) * 8;
    const pressure = 1014 - index * 0.05 + Math.sin(index / 3) * 0.7;
    const noise = 0.2 + Math.abs(Math.sin(index / 2.2)) * 0.38;

    return {
      timestamp,
      temperature_c: Number(temperature.toFixed(1)),
      humidity_percent: Number(humidity.toFixed(1)),
      pressure_hpa: Number(pressure.toFixed(1)),
      noise_score: Number(noise.toFixed(2)),
    };
  });
}

function mockStatus() {
  return {
    status: "online",
    ip_address: "192.168.1.42",
    disk_free_gb: 823.4,
    cpu_temp_c: 48.2,
    uptime_seconds: 5421,
  };
}

async function postJson(url, payload) {
  const response = await fetch(apiUrl(url), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  try {
    return await response.json();
  } catch {
    return { ok: true };
  }
}

function bindEvents() {
  elements.navButtons.forEach((button) => {
    button.addEventListener("click", () => setRoute(button.dataset.route));
  });

  window.addEventListener("popstate", (event) => {
    const route = event.state?.route || routeFromLocation();
    setRoute(route, false);
  });

  elements.snapshotImage.addEventListener("error", () => {
    elements.snapshotImage.hidden = true;
    elements.snapshotImage.removeAttribute("src");
    elements.snapshotEmpty.hidden = false;
  });

  elements.forceRefresh.addEventListener("click", async () => {
    elements.actionResponse.textContent = "Refreshing dashboard data.";
    await hydrateAll();
    elements.actionResponse.textContent = `Refresh completed using ${state.source} data.`;
  });

  elements.thresholdForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(elements.thresholdForm).entries());
    Object.assign(MOCK_CONFIG.thresholds, payload);

    if (state.source === "mock") {
      elements.actionResponse.textContent = "Thresholds updated locally in mock mode. Backend endpoint will use the same payload shape.";
      return;
    }

    try {
      const saved = await postJson("/api/config/thresholds", payload);
      state.thresholds = normalizeThresholds(saved);
      Object.assign(MOCK_CONFIG.thresholds, state.thresholds);
      renderThresholds();
      elements.actionResponse.textContent = "Thresholds saved to backend.";
    } catch {
      elements.actionResponse.textContent = "Threshold save failed. Backend endpoint may not be implemented yet.";
    }
  });

  elements.triggerCapture.addEventListener("click", async () => {
    if (state.source === "mock") {
      elements.actionResponse.textContent = "Mock capture triggered. Use `/api/actions/capture` when the backend is available.";
      return;
    }

    try {
      const result = await postJson("/api/actions/capture", {});
      elements.actionResponse.textContent = result.message || "Capture request sent.";
      await Promise.all([loadLatest(), loadEvents()]);
      updateSourceFromEndpoints();
      markSynced();
      renderAll();
    } catch {
      elements.actionResponse.textContent = "Capture request failed.";
    }
  });

  elements.triggerLed.addEventListener("click", async () => {
    if (state.source === "mock") {
      elements.actionResponse.textContent = "Mock LED test triggered. Use `/api/actions/test-led` when the backend is available.";
      return;
    }

    try {
      const result = await postJson("/api/actions/test-led", {});
      elements.actionResponse.textContent = result.message || "LED test request sent.";
      await Promise.all([loadLatest(), loadEvents()]);
      updateSourceFromEndpoints();
      markSynced();
      renderAll();
    } catch {
      elements.actionResponse.textContent = "LED test request failed.";
    }
  });
}

async function startPolling() {
  setInterval(() => refreshPanel(loadLatest), POLL_INTERVALS.latest);
  setInterval(() => refreshPanel(loadEvents), POLL_INTERVALS.events);
  setInterval(() => refreshPanel(loadHistory), POLL_INTERVALS.history);
  setInterval(() => refreshPanel(loadStatus), POLL_INTERVALS.status);
}

async function init() {
  setRoute(routeFromLocation(), false);
  bindEvents();
  await hydrateAll();
  await startPolling();
}

init();
