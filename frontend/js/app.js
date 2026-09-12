// ResQAgent Application Engine with Role-Based Authentication & Route Guard
document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

// Global Application State
const state = {
  currentUser: null,
  currentRole: 'citizen', // citizen | responder | dispatch | timeline | report | admin
  activeIncidentId: null,
  activeIncident: null,
  selectedCategory: 'Accident',
  currentResponderId: null,
  pollingTimer: null,
  soundEnabled: true,
  authMode: 'signin' // signin | register | forgot
};

// Web Audio API Sound Synthesizer
const audioCtx = (window.AudioContext || window.webkitAudioContext) ? new (window.AudioContext || window.webkitAudioContext)() : null;

function playTone(freq, type = 'sine', duration = 0.2, volume = 0.6) {
  if (!state.soundEnabled || !audioCtx) return;
  try {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
    const safeVolume = Math.min(Math.max(volume, 0.05), 1.0);
    gain.gain.setValueAtTime(safeVolume, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    osc.start();
    osc.stop(audioCtx.currentTime + duration);
  } catch (e) {
    // Ignore audio permission warnings
  }
}

function playAlertChime() {
  playTone(880, 'triangle', 0.15);
  setTimeout(() => playTone(1174, 'triangle', 0.25), 160);
}

function playSirenPing() {
  playTone(523, 'sawtooth', 0.12);
  setTimeout(() => playTone(659, 'sawtooth', 0.18), 120);
}

// Initialization & Route Guard
async function initApp() {
  setupLiveClock();
  setupNavigation();
  setupAuthForms();
  setupCitizenForm();
  setupSimulationBar();
  setupResponderTerminal();
  setupAdminForms();

  // Listen for session expiry event from api.js
  window.addEventListener('session-expired', () => {
    handleSignOut(true, "Your session has expired. Please sign in again.");
  });

  // URL Parameter auto-login for demo, evaluation & screenshots
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('demo') === 'admin' && !getAuthToken()) {
    try {
      const res = await api.login('admin@resqagent.org', 'ResQAdmin2026!');
      state.currentUser = res.user;
    } catch (e) {
      console.warn("Demo auto-login error:", e);
    }
  }

  // Verify authentication on startup
  await checkAuthSession();

  // SPA Path Routing Support (e.g. /dashboard, /sos, /responder, /dispatcher, /admin, /login)
  const path = window.location.pathname.toLowerCase().replace(/\/+$/, '');
  const pathViewMap = {
    '/login': 'login',
    '/dashboard': 'dispatch',
    '/dispatcher': 'dispatch',
    '/dispatch': 'dispatch',
    '/sos': 'citizen',
    '/citizen': 'citizen',
    '/responder': 'responder',
    '/timeline': 'timeline',
    '/report': 'report',
    '/admin': 'admin'
  };
  const pathTarget = pathViewMap[path];

  const targetTab = urlParams.get('tab') || urlParams.get('view') || (pathTarget && pathTarget !== 'login' ? pathTarget : null);
  if (targetTab) {
    switchView(targetTab);
    const tabs = document.querySelectorAll('.role-tab-btn');
    tabs.forEach(btn => btn.classList.toggle('active', btn.dataset.role === targetTab));
  }

  // If directly accessing /login and not authenticated, display sign-in modal
  if (path === '/login' && !state.currentUser) {
    showAuthOverlay('signin');
  }
}

// 1. Authentication Session Guard
async function checkAuthSession() {
  const token = getAuthToken();
  if (!token) {
    onUnauthenticated();
    return;
  }

  try {
    const user = await api.getMe();
    state.currentUser = user;
    onAuthenticated(user);
  } catch (err) {
    console.warn("Session check failed:", err.message);
    setAuthToken(null);
    onUnauthenticated();
  }
}

function onUnauthenticated() {
  hideAuthOverlay();
  state.currentUser = null;
  state.activeIncidentId = null;
  state.activeIncident = null;
  updateHeaderProfile(null);
  filterNavigationByRole('guest');
  switchView('citizen');

  // Highlight Citizen Navigation Tab
  const tabs = document.querySelectorAll('.role-tab-btn');
  tabs.forEach(btn => {
    btn.classList.toggle('active', btn.dataset.role === 'citizen');
  });
}

function onAuthenticated(user, welcomeMessage = null) {
  hideAuthOverlay();
  updateHeaderProfile(user);
  filterNavigationByRole(user.role);

  // Auto-redirect to role-appropriate dashboard
  const roleRedirectMap = {
    'citizen': 'citizen',
    'responder': 'responder',
    'dispatcher': 'dispatch',
    'admin': 'admin'
  };
  const targetView = roleRedirectMap[user.role.toLowerCase()] || 'citizen';
  switchView(targetView);

  // Synchronize navigation tabs active indicator
  const tabs = document.querySelectorAll('.role-tab-btn');
  tabs.forEach(btn => {
    btn.classList.toggle('active', btn.dataset.role === targetView);
  });

  if (welcomeMessage) {
    showToast(welcomeMessage, 'success');
  }

  // Set responder ID if responder role
  if (user.role === 'responder' && user.responder_id) {
    state.currentResponderId = user.responder_id;
  }

  // Start live operational polling
  startPolling();
}

function updateHeaderProfile(user) {
  const profileArea = document.getElementById('header-user-profile');
  const signInBtn = document.getElementById('btn-open-signin');
  const nameEl = document.getElementById('header-user-name');
  const roleEl = document.getElementById('header-user-role');

  if (user) {
    signInBtn.style.display = 'none';
    profileArea.style.display = 'flex';
    nameEl.innerText = user.name;
    roleEl.innerText = user.role.toUpperCase();
    roleEl.className = `user-role-tag role-tag-${user.role.toLowerCase()}`;
  } else {
    profileArea.style.display = 'none';
    signInBtn.style.display = 'block';
  }
}

function filterNavigationByRole(role) {
  const r = (role || '').toLowerCase();
  const tabs = document.querySelectorAll('.role-tab-btn');

  tabs.forEach(tab => {
    const tabRole = tab.dataset.role;
    // The SOS Emergency tab is always available to EVERY user role
    if (tabRole === 'citizen') {
      tab.style.display = 'inline-flex';
    } else if (r === 'admin') {
      tab.style.display = 'inline-flex';
    } else if (r === 'dispatcher') {
      tab.style.display = ['citizen', 'dispatch', 'timeline', 'report'].includes(tabRole) ? 'inline-flex' : 'none';
    } else if (r === 'responder') {
      tab.style.display = ['citizen', 'responder'].includes(tabRole) ? 'inline-flex' : 'none';
    } else { // citizen or guest
      tab.style.display = ['citizen', 'timeline'].includes(tabRole) ? 'inline-flex' : 'none';
    }
  });

  // Admin tab specifically
  const adminTab = document.getElementById('tab-btn-admin');
  if (adminTab) {
    adminTab.style.display = r === 'admin' ? 'inline-flex' : 'none';
  }

  // Demo controls visibility (only visible to dispatchers & admins)
  const demoBar = document.getElementById('demo-bar');
  if (demoBar) {
    demoBar.style.display = ['admin', 'dispatcher'].includes(r) ? 'block' : 'none';
  }
}

// Universal Trigger for SOS (30s Countdown Workflow) for any user role
function triggerGlobalSos() {
  switchView('citizen');
  const tabs = document.querySelectorAll('.role-tab-btn');
  tabs.forEach(btn => btn.classList.toggle('active', btn.dataset.role === 'citizen'));

  const bigSos = document.getElementById('big-sos-btn');
  if (bigSos) {
    bigSos.click();
  }
}
window.triggerGlobalSos = triggerGlobalSos;

// Geolocation & GPS Auto-Detection (HTML5 Geolocation API)
window.lastGpsCoords = null;

function detectGpsLocation(inputId, statusId) {
  if (!navigator.geolocation) {
    showToast("Geolocation is not supported by your browser.", "warning");
    return;
  }
  const statusEl = statusId ? document.getElementById(statusId) : null;
  if (statusEl) {
    statusEl.innerHTML = `<span style="color: #2563eb; font-weight: 600;">🛰️ Acquiring live GPS signal...</span>`;
  }

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const lat = pos.coords.latitude.toFixed(5);
      const lon = pos.coords.longitude.toFixed(5);
      const acc = Math.round(pos.coords.accuracy);
      window.lastGpsCoords = { lat, lon, acc };

      const input = document.getElementById(inputId);
      if (input) {
        input.value = `${lat}, ${lon} (GPS Live)`;
        input.style.borderColor = '#10b981';
      }
      if (statusEl) {
        statusEl.innerHTML = `<span style="color: #059669; font-weight: 600;">📍 GPS Acquired: ${lat}, ${lon} (±${acc}m)</span>`;
      }
      showToast(`GPS Acquired: ${lat}, ${lon}`, "success");
    },
    (err) => {
      let msg = "GPS unavailable. Please enter location manually.";
      if (err.code === 1) msg = "GPS permission denied. Using manual location mode.";
      if (statusEl) {
        statusEl.innerHTML = `<span style="color: #d97706; font-size: 11px;">⚠️ ${msg}</span>`;
      }
      showToast(msg, "warning");
    },
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 }
  );
}
window.detectGpsLocation = detectGpsLocation;

// 2. Authentication UI & Form Handlers
function setupAuthForms() {
  document.getElementById('btn-signout')?.addEventListener('click', () => {
    handleSignOut(false, "Signed out successfully.");
  });

  document.getElementById('btn-open-signin')?.addEventListener('click', () => {
    showAuthOverlay('signin');
  });

  // Sign In Form
  const signinForm = document.getElementById('signin-form');
  signinForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearAuthError();

    const email = document.getElementById('signin-email').value.trim();
    const password = document.getElementById('signin-password').value;
    const submitBtn = signinForm.querySelector('button[type="submit"]');

    submitBtn.disabled = true;
    submitBtn.innerText = 'Authenticating...';

    try {
      const res = await api.login(email, password);
      state.currentUser = res.user;
      signinForm.reset();
      onAuthenticated(res.user, `Welcome back, ${res.user.name}!`);
    } catch (err) {
      showAuthError(err.message);
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerText = 'Sign In';
    }
  });

  // Restrict phone input to 10 digits
  function setupPhoneInputFormatter(inputId) {
    const el = document.getElementById(inputId);
    if (!el) return;

    el.addEventListener('input', () => {
      el.value = el.value.replace(/\D/g, '').slice(0, 10);
    });

    el.addEventListener('blur', () => {
      const digits = el.value.replace(/\D/g, '');
      if (digits.length > 0 && digits.length !== 10) {
        el.style.borderColor = 'var(--accent-red)';
      } else {
        el.style.borderColor = '';
      }
    });
  }

  setupPhoneInputFormatter('reg-phone');

  // Multi-Role Registration Role Switcher
  window.selectRegRole = function(role) {
    const hiddenInput = document.getElementById('reg-selected-role');
    if (hiddenInput) hiddenInput.value = role;

    document.querySelectorAll('.reg-role-option').forEach(el => {
      el.classList.toggle('selected', el.dataset.role === role);
    });

    const respFields = document.getElementById('reg-responder-fields');
    if (respFields) {
      respFields.style.display = role === 'responder' ? 'block' : 'none';
    }

    const submitBtn = document.getElementById('reg-submit-btn');
    if (submitBtn) {
      const roleLabels = {
        'citizen': 'Create Citizen Account & Launch SOS',
        'responder': 'Create Responder Account & Open Field Terminal',
        'dispatcher': 'Create Dispatcher Account & Open Command Center',
        'admin': 'Create Admin Account & Open Control Panel'
      };
      submitBtn.innerText = roleLabels[role] || 'Create Account';
    }
  };

  // Multi-Role Registration Form Submit
  const regForm = document.getElementById('register-form');
  regForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearAuthError();

    const name = document.getElementById('reg-name').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const phoneInput = document.getElementById('reg-phone');
    const rawPhone = (phoneInput?.value || '').trim();
    const location = document.getElementById('reg-location').value.trim();
    const password = document.getElementById('reg-password').value;
    const confirmPassword = document.getElementById('reg-confirm').value;
    const role = document.getElementById('reg-selected-role')?.value || 'citizen';

    // 10-digit phone number condition and validation
    const phoneDigits = rawPhone.replace(/\D/g, '');
    if (!rawPhone || phoneDigits.length !== 10) {
      showAuthError("Phone number must contain exactly 10 digits.");
      if (phoneInput) {
        phoneInput.focus();
        phoneInput.style.borderColor = 'var(--accent-red)';
      }
      return;
    }
    if (phoneInput) phoneInput.style.borderColor = '';

    if (password !== confirmPassword) {
      showAuthError("Passwords do not match.");
      return;
    }

    const submitBtn = document.getElementById('reg-submit-btn') || regForm.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerText = 'Creating account...';

    const payload = {
      name,
      email,
      phone: phoneDigits,
      location,
      password,
      confirm_password: confirmPassword,
      role
    };

    if (role === 'responder') {
      payload.responder_role = document.getElementById('reg-resp-role')?.value || 'Paramedic / First Responder';
      payload.specialization = document.getElementById('reg-resp-spec')?.value || 'Medical';
      payload.distance = parseFloat(document.getElementById('reg-resp-dist')?.value || '0.8');
    }

    try {
      const res = await api.register(payload);
      state.currentUser = res.user;
      regForm.reset();
      window.selectRegRole('citizen');
      onAuthenticated(res.user, `Account created! Welcome, ${res.user.name} (${res.user.role.toUpperCase()}).`);
    } catch (err) {
      showAuthError(err.message);
    } finally {
      submitBtn.disabled = false;
      const roleLabels = {
        'citizen': 'Create Citizen Account & Launch SOS',
        'responder': 'Create Responder Account & Open Field Terminal',
        'dispatcher': 'Create Dispatcher Account & Open Command Center',
        'admin': 'Create Admin Account & Open Control Panel'
      };
      submitBtn.innerText = roleLabels[role] || 'Create Account';
    }
  });

  // Forgot Password Form
  const forgotForm = document.getElementById('forgot-form');
  forgotForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearAuthError();
    const email = document.getElementById('forgot-email').value.trim();
    try {
      await api.forgotPassword(email);
      showToast("Password reset link sent if account exists.", "success");
      switchAuthMode('signin');
    } catch (err) {
      showAuthError(err.message);
    }
  });
}

function showAuthOverlay(mode = 'signin', alertMsg = null) {
  stopPolling();
  const overlay = document.getElementById('auth-overlay');
  if (overlay) overlay.style.display = 'flex';
  switchAuthMode(mode);
  if (alertMsg) {
    showAuthError(alertMsg);
  } else {
    clearAuthError();
  }
}

function hideAuthOverlay() {
  const overlay = document.getElementById('auth-overlay');
  if (overlay) overlay.style.display = 'none';
  clearAuthError();
}

function switchAuthMode(mode) {
  state.authMode = mode;
  clearAuthError();

  const signinForm = document.getElementById('signin-form');
  const registerForm = document.getElementById('register-form');
  const forgotForm = document.getElementById('forgot-form');
  const tabSignin = document.getElementById('auth-tab-signin');
  const tabRegister = document.getElementById('auth-tab-register');

  signinForm.style.display = mode === 'signin' ? 'block' : 'none';
  registerForm.style.display = mode === 'register' ? 'block' : 'none';
  forgotForm.style.display = mode === 'forgot' ? 'block' : 'none';

  if (tabSignin && tabRegister) {
    tabSignin.classList.toggle('active', mode === 'signin');
    tabRegister.classList.toggle('active', mode === 'register');
  }

  const card = document.querySelector('.auth-card');
  if (card) card.scrollTop = 0;
}

window.switchAuthMode = switchAuthMode;
window.hideAuthOverlay = hideAuthOverlay;
window.showAuthOverlay = showAuthOverlay;
window.fillSignIn = function(email, password) {
  const emailInput = document.getElementById('signin-email');
  const pwdInput = document.getElementById('signin-password');
  if (emailInput) emailInput.value = email;
  if (pwdInput) pwdInput.value = password;
};

function showAuthError(msg) {
  const banner = document.getElementById('auth-error-banner');
  const text = document.getElementById('auth-error-text');
  if (banner && text) {
    text.innerText = msg;
    banner.style.display = 'flex';
  }
}

function clearAuthError() {
  const banner = document.getElementById('auth-error-banner');
  if (banner) banner.style.display = 'none';
}

async function handleSignOut(expired = false, msg = "Signed out successfully.") {
  stopResponderAcceptanceTimer();
  if (typeof window.cancelSosCountdown === 'function') {
    window.cancelSosCountdown();
  }
  await api.logout();
  stopPolling();
  onUnauthenticated();
  showToast(msg, expired ? 'warning' : 'success');
}

// 3. Navigation Tabs
function setupNavigation() {
  const tabs = document.querySelectorAll('.role-tab-btn');
  tabs.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetRole = btn.dataset.role;
      if (!state.currentUser && ['dispatch', 'responder', 'report', 'admin'].includes(targetRole)) {
        showAuthOverlay('signin', `Please sign in to access ${btn.innerText.trim()}.`);
        return;
      }
      tabs.forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      switchView(targetRole);
    });
  });
}

function switchView(role) {
  state.currentRole = role;
  document.querySelectorAll('.view-section').forEach(sec => sec.classList.remove('active'));
  const targetSec = document.getElementById(`view-${role}`);
  if (targetSec) targetSec.classList.add('active');

  if (role !== 'responder') {
    stopResponderAcceptanceTimer();
  }
  if (role !== 'citizen' && typeof window.cancelSosCountdown === 'function') {
    window.cancelSosCountdown();
  }

  // Trigger role-specific renders
  if (role === 'dispatch') renderDispatchBoard();
  if (role === 'responder') renderResponderTerminal();
  if (role === 'timeline') renderCognitiveTimeline();
  if (role === 'report') renderReportSection();
  if (role === 'admin') renderAdminDashboard();
}

window.switchView = switchView;

// 4. Live Polling Engine
function startPolling() {
  stopPolling();
  refreshAllData();
  state.pollingTimer = setInterval(() => {
    refreshAllData();
  }, 1500);
  state.clockTimer = setInterval(() => {
    if (state.currentRole === 'dispatch') {
      updateDispatchBoardTimers();
    }
  }, 1000);
}

function stopPolling() {
  if (state.pollingTimer) {
    clearInterval(state.pollingTimer);
    state.pollingTimer = null;
  }
  if (state.clockTimer) {
    clearInterval(state.clockTimer);
    state.clockTimer = null;
  }
}

async function refreshAllData() {
  if (!state.currentUser) return;
  try {
    const incidents = await api.getIncidents();
    
    // Pick most recent active incident if none selected
    if (!state.activeIncidentId && incidents.length > 0) {
      state.activeIncidentId = incidents[0].id;
      state.activeIncident = incidents[0];
    } else if (state.activeIncidentId) {
      const updated = incidents.find(i => i.id === state.activeIncidentId);
      if (updated) state.activeIncident = updated;
    }

    // Update active incident tracker for citizen
    renderCitizenTracker();

    // Update active view
    if (state.currentRole === 'dispatch') renderDispatchBoard(incidents);
    if (state.currentRole === 'responder') renderResponderTerminal();
    if (state.currentRole === 'timeline') renderCognitiveTimeline();
    if (state.currentRole === 'report') renderReportSection();
    if (state.currentRole === 'admin') renderAdminDashboard();

    // Update metrics if dispatcher/admin
    if (['dispatcher', 'admin'].includes(state.currentUser.role.toLowerCase())) {
      const responders = await api.getResponders().catch(() => []);
      updateGlobalMetrics(incidents, responders);
    }

    // Background alert check for logged-in responder
    if (state.currentUser?.role === 'responder' && state.currentRole !== 'responder') {
      const userAssignments = await api.getAssignments().catch(() => []);
      const pendingCall = userAssignments.find(a => a.assignment_status === 'PENDING');
      if (pendingCall) {
        startResponderSosAlertBeep();
      } else {
        stopResponderSosAlertBeep();
      }
    }
  } catch (err) {
    console.warn('Sync poll notice:', err.message);
  }
}

function updateGlobalMetrics(incidents = [], responders = []) {
  const activeCount = incidents.filter(i => i.status !== 'RESOLVED').length;
  const availCount = responders.filter(r => r.availability === 'AVAILABLE').length;

  const countBadge = document.getElementById('metric-active-count');
  if (countBadge) countBadge.innerText = activeCount;

  const respBadge = document.getElementById('metric-avail-responders');
  if (respBadge) respBadge.innerText = availCount;
}

// 5. Citizen SOS & Form Submission
const incidentPresets = {
  Accident: {
    icon: '🚗',
    badgeLabel: '🚗 Road Collision Preset',
    badgeClass: 'badge-p1',
    description: 'Multi-vehicle collision at intersection. Two victims conscious with lacerations and airbag deployment; traffic blocked and vehicle leaking fluid.',
    location: 'Crossroad of 5th Ave & Pine St, Sector 3',
    details: 'Casualties: 2 injured • Hazards: Fuel leak, glass • Urgency: Immediate ambulance & traffic control'
  },
  Medical: {
    icon: '🩺',
    badgeLabel: '🩺 Cardiac / Trauma Preset',
    badgeClass: 'badge-p1',
    description: 'Elderly patient collapsed, experiencing severe chest pain, shortness of breath, and irregular pulse. Immediate cardiac paramedic intervention needed.',
    location: 'Apartment 4B, Oakridge Towers, Sector 7',
    details: 'Casualties: 1 critical • Symptoms: Unresponsiveness, chest pain • Urgency: Paramedic with AED'
  },
  Fire: {
    icon: '🔥',
    badgeLabel: '🔥 Structural Fire Preset',
    badgeClass: 'badge-p1',
    description: 'Structural fire detected on 2nd floor residential building. Dense smoke billowing, possible victims trapped inside, fire spreading rapidly toward adjacent units.',
    location: 'Building 14, Commercial District, Block B',
    details: 'Hazards: Dense toxic smoke, electrical short • Urgency: Fire tender & search rescue team'
  },
  Crime: {
    icon: '🚨',
    badgeLabel: '🚨 Active Threat Preset',
    badgeClass: 'badge-p1',
    description: 'Armed robbery in progress at local pharmacy. Suspect carrying weapon, cashier threatened, urgent police intervention required.',
    location: 'Market Square, Central Plaza, East Wing',
    details: 'Threat Level: Armed suspect • Civilians present • Urgency: Rapid tactical police dispatch'
  },
  Rescue: {
    icon: '🌊',
    badgeLabel: '🌊 Swift Water Rescue Preset',
    badgeClass: 'badge-p2',
    description: 'Flash flood trapping two people on vehicle roof near stormwater canal. Water level rising fast, swift water rescue required immediately.',
    location: 'Canal Bridge, North Riverway Drainage Basin',
    details: 'Victims: 2 stranded • Hazards: Fast flood waters • Urgency: Inflatable boat & rope rescue team'
  }
};

function setupCitizenForm() {
  const chips = document.querySelectorAll('.type-chip');
  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      chips.forEach(c => c.classList.remove('selected'));
      chip.classList.add('selected');
      const category = chip.dataset.type;
      state.selectedCategory = category;

      // Dynamically update "What is happening?" scenario, location, and hints
      const preset = incidentPresets[category];
      if (preset) {
        const descInput = document.getElementById('input-desc');
        const locInput = document.getElementById('input-loc');
        const hintBadge = document.getElementById('desc-category-hint');
        const detailsText = document.getElementById('desc-scenario-text');

        if (descInput) {
          descInput.value = preset.description;
          // Visual micro-interaction feedback
          descInput.style.borderColor = 'var(--accent-blue)';
          descInput.style.boxShadow = '0 0 0 3px rgba(37, 99, 235, 0.18)';
          setTimeout(() => {
            descInput.style.borderColor = '';
            descInput.style.boxShadow = '';
          }, 450);
        }

        if (locInput) {
          locInput.value = preset.location;
        }

        if (hintBadge) {
          hintBadge.innerText = preset.badgeLabel;
          hintBadge.className = `badge ${preset.badgeClass}`;
        }

        if (detailsText) {
          detailsText.innerText = preset.details;
        }
      }
    });
  });

  let sosCountdownTimer = null;
  let sosRemainingSeconds = 15;

  function cancelSosCountdown() {
    if (sosCountdownTimer) {
      clearInterval(sosCountdownTimer);
      sosCountdownTimer = null;
    }
    const countdownBox = document.getElementById('sos-countdown-container');
    const btnWrapper = document.getElementById('sos-btn-wrapper');
    const subtext = document.getElementById('sos-help-subtext');

    if (countdownBox) countdownBox.style.display = 'none';
    if (btnWrapper) btnWrapper.style.display = 'flex';
    if (subtext) subtext.style.display = 'block';

    playTone(440, 'triangle', 0.15);
    showToast('SOS broadcast cancelled.', 'warning');
  }

  window.cancelSosCountdown = cancelSosCountdown;

  async function executeExistingSosBroadcast() {
    const sosBtn = document.getElementById('big-sos-btn');
    if (sosBtn) {
      sosBtn.disabled = true;
      sosBtn.innerText = 'TRIGGERING...';
    }

    playSirenPing();

    try {
      const rolePrefix = state.currentUser?.role ? state.currentUser.role.toUpperCase() : 'CITIZEN';
      const userName = state.currentUser?.name || '';
      let sosLocation = state.currentUser?.location || 'Downtown Sector 4';
      if (window.lastGpsCoords) {
        sosLocation = `${window.lastGpsCoords.lat}, ${window.lastGpsCoords.lon} (GPS Live)`;
      }
      const payload = {
        emergency_type: 'Accident',
        description: `CRITICAL ONE-TOUCH SOS: Severe distress reported by ${rolePrefix} ${userName}, victim in urgent need of assistance.`,
        location: sosLocation
      };
      const created = await api.createIncident(payload);
      state.activeIncidentId = created.id;
      state.activeIncident = created;
      showToast('Emergency SOS Broadcasted! AI Agents dispatched.', 'danger');
      await refreshAllData();
      const trackerCard = document.getElementById('active-tracker-card');
      if (trackerCard) trackerCard.style.display = 'block';
    } catch (err) {
      showToast('Failed to send SOS: ' + err.message, 'danger');
    } finally {
      if (sosBtn) {
        sosBtn.disabled = false;
        sosBtn.innerHTML = '<span>SOS</span><span class="sos-btn-sub">PRESS FOR HELP</span>';
      }
    }
  }

  const sosBtn = document.getElementById('big-sos-btn');
  sosBtn?.addEventListener('click', () => {
    if (!state.currentUser) {
      showAuthOverlay('signin', 'Please sign in or register to broadcast emergency SOS.');
      return;
    }

    if (sosCountdownTimer) return; // Prevent multiple timers

    // Opportunistically acquire real-time GPS position during countdown
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          window.lastGpsCoords = {
            lat: pos.coords.latitude.toFixed(5),
            lon: pos.coords.longitude.toFixed(5),
            acc: Math.round(pos.coords.accuracy)
          };
        },
        () => {},
        { enableHighAccuracy: true, timeout: 12000, maximumAge: 30000 }
      );
    }

    playAlertChime();

    const countdownBox = document.getElementById('sos-countdown-container');
    const btnWrapper = document.getElementById('sos-btn-wrapper');
    const subtext = document.getElementById('sos-help-subtext');
    const numberEl = document.getElementById('sos-countdown-number');

    if (btnWrapper) btnWrapper.style.display = 'none';
    if (subtext) subtext.style.display = 'none';
    if (countdownBox) countdownBox.style.display = 'flex';

    sosRemainingSeconds = 15;
    if (numberEl) numberEl.innerText = sosRemainingSeconds;
    playTone(750, 'sine', 0.12, 0.75);

    sosCountdownTimer = setInterval(async () => {
      sosRemainingSeconds--;
      if (numberEl) numberEl.innerText = sosRemainingSeconds;

      // Audible countdown beep on every second with high amplified volume
      if (sosRemainingSeconds > 5) {
        playTone(750, 'sine', 0.12, 0.75);
      } else if (sosRemainingSeconds > 0) {
        playTone(950, 'sawtooth', 0.16, 0.85);
      }

      if (sosRemainingSeconds <= 0) {
        clearInterval(sosCountdownTimer);
        sosCountdownTimer = null;

        if (countdownBox) countdownBox.style.display = 'none';
        if (btnWrapper) btnWrapper.style.display = 'flex';
        if (subtext) subtext.style.display = 'block';

        // 15 seconds completed: Execute EXISTING SOS functionality
        await executeExistingSosBroadcast();
      }
    }, 1000);
  });

  document.getElementById('sos-cancel-btn')?.addEventListener('click', () => {
    cancelSosCountdown();
  });

  const form = document.getElementById('emergency-form');
  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!state.currentUser) {
      showAuthOverlay('signin', 'Please sign in or register as a citizen to submit an emergency request.');
      return;
    }

    const desc = document.getElementById('input-desc').value.trim();
    const loc = document.getElementById('input-loc').value.trim() || state.currentUser?.location || 'Sector 5, Downtown';

    if (!desc) {
      showToast('Please describe the emergency.', 'warning');
      return;
    }

    playAlertChime();
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerText = 'Analyzing & Dispatching...';

    try {
      const payload = {
        emergency_type: state.selectedCategory,
        description: desc,
        location: loc
      };
      const created = await api.createIncident(payload);
      state.activeIncidentId = created.id;
      state.activeIncident = created;
      showToast(`Incident #${created.id} reported! AI Orchestrator active.`, 'success');
      await refreshAllData();
      document.getElementById('active-tracker-card').style.display = 'block';
    } catch (err) {
      showToast('Failed to report incident: ' + err.message, 'danger');
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '⚡ Submit Emergency Request';
    }
  });
}

function renderCitizenTracker() {
  const tracker = document.getElementById('active-tracker-card');
  if (!tracker) return;

  if (!state.activeIncident) {
    tracker.style.display = 'none';
    return;
  }

  tracker.style.display = 'block';
  const inc = state.activeIncident;

  document.getElementById('tracker-inc-id').innerText = `INC-${inc.id}`;
  document.getElementById('tracker-type').innerText = inc.emergency_type;
  document.getElementById('tracker-loc').innerText = inc.location;
  document.getElementById('tracker-desc').innerText = inc.description;

  const timeEl = document.getElementById('tracker-time');
  if (timeEl) {
    timeEl.innerText = formatDateTime(inc.created_at);
  }

  const pBadge = document.getElementById('tracker-priority');
  pBadge.className = `badge badge-${(inc.priority || 'p3').toLowerCase().slice(0, 2)}`;
  pBadge.innerText = inc.priority || 'Analyzing';

  const steps = [
    { id: 'step-triage', done: ['ANALYZED', 'RESPONDER_SEARCH', 'RESPONDER_ASSIGNED', 'WAITING_FOR_RESPONSE', 'ASSISTANCE_IN_PROGRESS', 'RESOLVED'].includes(inc.status) },
    { id: 'step-dispatch', done: ['RESPONDER_ASSIGNED', 'WAITING_FOR_RESPONSE', 'ASSISTANCE_IN_PROGRESS', 'RESOLVED'].includes(inc.status) },
    { id: 'step-enroute', done: ['ASSISTANCE_IN_PROGRESS', 'RESOLVED'].includes(inc.status) },
    { id: 'step-resolved', done: inc.status === 'RESOLVED' }
  ];

  let completedCount = 0;
  steps.forEach((s, idx) => {
    const el = document.getElementById(s.id);
    if (!el) return;
    el.className = 'step-item';
    if (s.done) {
      el.classList.add('completed');
      completedCount++;
    } else if (idx === completedCount) {
      el.classList.add('active');
    }
  });

  const progressBar = document.getElementById('stepper-progress-bar');
  if (progressBar) {
    const pct = (completedCount / (steps.length - 1)) * 100;
    progressBar.style.width = `${Math.min(100, pct)}%`;
  }
}

// 6. Responder Terminal & Acceptance Timer Engine
let responderAcceptanceTimer = null;
let currentActiveAssignmentId = null;
let isResponderActionPending = false;

function parseUtcDate(dateStr) {
  if (!dateStr) return Date.now();
  const str = String(dateStr);
  const utcStr = (str.endsWith('Z') || str.includes('+')) ? str : str + 'Z';
  const parsed = new Date(utcStr).getTime();
  return isNaN(parsed) ? Date.now() : parsed;
}

function formatDateTime(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(parseUtcDate(dateStr));
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  });
}

function formatTime(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(parseUtcDate(dateStr));
  return d.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  });
}

function setupLiveClock() {
  updateLiveDateTime();
  setInterval(updateLiveDateTime, 1000);
}

function updateLiveDateTime() {
  const el = document.getElementById('live-date-time-display');
  if (!el) return;
  const now = new Date();
  const options = {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true
  };
  el.innerText = now.toLocaleString(undefined, options);
}

// Emergency Responder SOS Alert Beep Notification Engine
let responderSosBeepTimer = null;

function playResponderSosAlertBeep() {
  if (!state.soundEnabled || !audioCtx) return;
  try {
    if (audioCtx.state === 'suspended') audioCtx.resume();
    // High-urgency dual-tone alert beep for responder SOS notification (loud, amplified 0.85 volume)
    playTone(900, 'sine', 0.16, 0.85);
    setTimeout(() => {
      if (responderSosBeepTimer) {
        playTone(1200, 'triangle', 0.20, 0.9);
      }
    }, 150);
  } catch (e) {
    // Audio context safety fallback
  }
}

function startResponderSosAlertBeep() {
  if (responderSosBeepTimer) return;
  playResponderSosAlertBeep();
  responderSosBeepTimer = setInterval(() => {
    playResponderSosAlertBeep();
  }, 900); // Rhythmic SOS alert beep until responder accepts or declines
}

function stopResponderSosAlertBeep() {
  if (responderSosBeepTimer) {
    clearInterval(responderSosBeepTimer);
    responderSosBeepTimer = null;
  }
}

window.startResponderSosAlertBeep = startResponderSosAlertBeep;
window.stopResponderSosAlertBeep = stopResponderSosAlertBeep;

function startResponderAcceptanceTimer(assignmentId, assignedAtStr) {
  const assignedAt = parseUtcDate(assignedAtStr);

  // Sound continuous emergency SOS alert beep until accepted or declined
  startResponderSosAlertBeep();

  const updateTick = async () => {
    const elapsed = Math.floor((Date.now() - assignedAt) / 1000);
    const remaining = Math.max(0, 5 - elapsed);

    const displayEl = document.getElementById('resp-timer-display');
    const countEl = document.getElementById('resp-sec-count');
    if (displayEl) {
      displayEl.innerText = `00:${remaining < 10 ? '0' + remaining : remaining}`;
      if (remaining <= 2) {
        displayEl.classList.add('urgent');
      } else {
        displayEl.classList.remove('urgent');
      }
    }
    if (countEl) countEl.innerText = remaining;

    if (remaining <= 2 && remaining > 0) {
      playTone(720, 'sine', 0.1, 0.75);
    }

    if (remaining <= 0) {
      stopResponderSosAlertBeep();
      stopResponderAcceptanceTimer();
      await handleAssignmentTimeout(assignmentId);
    }
  };

  if (responderAcceptanceTimer && currentActiveAssignmentId === assignmentId) {
    updateTick(); // Fast update on re-rendered DOM without resetting running interval
    return;
  }

  stopResponderAcceptanceTimer();
  currentActiveAssignmentId = assignmentId;

  updateTick();
  responderAcceptanceTimer = setInterval(updateTick, 1000);
}

function stopResponderAcceptanceTimer() {
  stopResponderSosAlertBeep();
  if (responderAcceptanceTimer) {
    clearInterval(responderAcceptanceTimer);
    responderAcceptanceTimer = null;
  }
  currentActiveAssignmentId = null;
}

async function handleAssignmentTimeout(assignmentId) {
  if (isResponderActionPending) return;
  isResponderActionPending = true;

  stopResponderAcceptanceTimer();

  const btnAccept = document.getElementById('resp-btn-accept');
  const btnDecline = document.getElementById('resp-btn-decline');
  if (btnAccept) btnAccept.disabled = true;
  if (btnDecline) btnDecline.disabled = true;

  try {
    playSirenPing();
    showToast("No response received. Escalating to another responder.", "danger");
    await api.timeoutAssignment(assignmentId);
    await refreshAllData();
  } catch (e) {
    console.warn("Assignment timeout notice:", e.message);
    await refreshAllData();
  } finally {
    isResponderActionPending = false;
  }
}

function setupResponderTerminal() {
  const respSelect = document.getElementById('responder-selector');
  respSelect?.addEventListener('change', (e) => {
    state.currentResponderId = parseInt(e.target.value);
    stopResponderAcceptanceTimer();
    renderResponderTerminal();
  });
}

async function renderResponderTerminal() {
  const container = document.getElementById('responder-active-call-area');
  if (!container) return;

  let currentResp = null;
  try {
    const responders = await api.getResponders();
    if (state.currentUser?.role === 'responder') {
      currentResp = responders.find(r => r.user_id === state.currentUser.id || (state.currentUser.responder_id && r.id === state.currentUser.responder_id) || r.name.toLowerCase() === state.currentUser.name.toLowerCase()) || responders[0];
      document.getElementById('resp-simulator-dropdown-container').style.display = 'none';
    } else {
      // Dispatcher/Admin inspecting responder view
      currentResp = responders.find(r => r.id === state.currentResponderId) || responders[0];
      document.getElementById('resp-simulator-dropdown-container').style.display = 'block';
    }
  } catch (err) {
    container.innerHTML = `<div style="text-align:center; padding:40px; color:var(--text-muted);">Responder profile unavailable.</div>`;
    return;
  }

  if (!currentResp) {
    container.innerHTML = `<div style="text-align:center; padding:40px; color:var(--text-muted);">No responder unit registered.</div>`;
    return;
  }

  document.getElementById('resp-current-name').innerText = currentResp.name;
  document.getElementById('resp-current-role').innerText = `${currentResp.role} (${currentResp.specialization})`;
  document.getElementById('resp-current-dist').innerText = `${currentResp.distance} km from center`;
  
  const statusBadge = document.getElementById('resp-current-status');
  statusBadge.innerText = currentResp.availability;
  statusBadge.className = `badge badge-${currentResp.availability === 'AVAILABLE' ? 'avail' : currentResp.availability === 'BUSY' ? 'busy' : 'p2'}`;

  // Fetch assignments for this responder
  const assignments = await api.getAssignments(null, currentResp.id).catch(() => []);
  const activeAssignment = assignments.find(a => ['PENDING', 'ACCEPTED', 'EN_ROUTE', 'ON_SCENE'].includes(a.assignment_status));

  if (!activeAssignment) {
    stopResponderAcceptanceTimer();
    container.innerHTML = `
      <div style="text-align: center; padding: 50px 20px; color: var(--text-muted);">
        <div style="font-size: 38px; margin-bottom: 12px;">📡</div>
        <h3 style="font-family: var(--font-heading); color: var(--text-secondary);">No Active Assignments</h3>
        <p style="font-size: 13px; margin-top: 6px;">Unit ${currentResp.name} is on standby. Incoming calls will appear here in real time.</p>
      </div>
    `;
    return;
  }

  const inc = await api.getIncident(activeAssignment.incident_id).catch(() => null);
  if (!inc) return;

  if (activeAssignment.assignment_status === 'PENDING') {
    const elapsed = Math.floor((Date.now() - parseUtcDate(activeAssignment.assigned_at)) / 1000);
    const initialRemaining = Math.max(0, 5 - elapsed);
    const clockText = `00:${initialRemaining < 10 ? '0' + initialRemaining : initialRemaining}`;

    if (initialRemaining <= 0) {
      stopResponderAcceptanceTimer();
      handleAssignmentTimeout(activeAssignment.id);
      return;
    }

    container.innerHTML = `
      <div class="glass-card" style="border: 2px solid var(--accent-amber); box-shadow: 0 4px 20px rgba(245, 158, 11, 0.15);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span class="pulsing-alert-dot"></span>
            <span style="font-family: var(--font-heading); font-size: 14px; font-weight: 800; letter-spacing: 0.5px; color: var(--accent-amber); text-transform: uppercase;">
              NEW EMERGENCY ASSIGNMENT
            </span>
          </div>
          <span class="badge badge-busy">PENDING CONFIRMATION</span>
        </div>

        <div style="background: #f8fafc; border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 14px; margin-bottom: 16px;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <div style="font-size: 14px; color: var(--text-primary);">
              <strong style="color: var(--text-muted);">Emergency:</strong> ${inc.emergency_type}
            </div>
            <div>
              <strong style="color: var(--text-muted); font-size: 13px;">Priority:</strong> 
              <span class="badge ${inc.priority === 'P1-Critical' ? 'badge-p1' : inc.priority === 'P2-High' ? 'badge-p2' : 'badge-p3'}">${inc.priority || 'HIGH'}</span>
            </div>
          </div>
          <div style="font-size: 13px; color: var(--text-primary); margin-bottom: 6px;">
            <strong style="color: var(--text-muted);">Location:</strong> ${inc.location}
          </div>
          <div style="font-size: 12px; color: var(--text-secondary); line-height: 1.4;">
            <strong style="color: var(--text-muted);">Details:</strong> ${inc.description}
          </div>
        </div>

        <!-- Countdown Acceptance Box -->
        <div class="resp-timer-box">
          <div class="resp-timer-left">
            <div class="resp-timer-label">Response Required</div>
            <div class="resp-timer-sub">Accept in: <span id="resp-sec-count">${initialRemaining}</span>s</div>
          </div>
          <div id="resp-timer-display" class="resp-timer-clock ${initialRemaining <= 2 ? 'urgent' : ''}">${clockText}</div>
        </div>

        <div style="display: flex; gap: 12px;">
          <button id="resp-btn-accept" class="btn btn-success" style="flex: 1; padding: 12px; font-weight: 700; font-size: 14px;" onclick="handleResponderAction(${activeAssignment.id}, 'ACCEPTED')">
            [ ACCEPT ]
          </button>
          <button id="resp-btn-decline" class="btn btn-danger" style="flex: 1; padding: 12px; font-weight: 700; font-size: 14px;" onclick="handleResponderAction(${activeAssignment.id}, 'DECLINED')">
            [ DECLINE ]
          </button>
        </div>
      </div>
    `;
    startResponderAcceptanceTimer(activeAssignment.id, activeAssignment.assigned_at);
  } else {
    stopResponderAcceptanceTimer();
    container.innerHTML = `
      <div class="glass-card" style="border: 2px solid var(--accent-emerald);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
          <div style="display: flex; align-items: center; gap: 10px;">
            <span class="badge ${inc.priority === 'P1-Critical' ? 'badge-p1' : 'badge-p2'}">${inc.priority}</span>
            <span style="font-family: var(--font-mono); color: var(--text-muted); font-size: 12px;">INC-${inc.id}</span>
          </div>
          <span class="badge badge-avail">
            ${activeAssignment.assignment_status}
          </span>
        </div>

        <h2 style="font-family: var(--font-heading); font-size: 20px; color: var(--text-primary); margin-bottom: 8px;">
          🚨 ${inc.emergency_type} Emergency
        </h2>
        <p style="font-size: 14px; color: var(--text-primary); margin-bottom: 14px; background: #f8fafc; border: 1px solid var(--border-color); padding: 12px 14px; border-radius: var(--radius-sm);">
          ${inc.description}
        </p>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 13px; margin-bottom: 20px;">
          <div><strong style="color: var(--text-muted);">Location:</strong> ${inc.location}</div>
          <div><strong style="color: var(--text-muted);">Caller:</strong> ${inc.reporter_name || 'Citizen'}</div>
          <div><strong style="color: var(--text-muted);">Attempt:</strong> #${activeAssignment.attempt_number}</div>
          <div><strong style="color: var(--text-muted);">Assigned At:</strong> ${formatTime(activeAssignment.assigned_at)}</div>
        </div>

        <div style="display: flex; gap: 12px; flex-wrap: wrap;">
          ${activeAssignment.assignment_status === 'ACCEPTED' ? `
            <button class="btn btn-primary" style="flex: 1;" onclick="handleProgressAction(${activeAssignment.id}, 'EN_ROUTE')">
              🚗 MARK EN ROUTE
            </button>
            <button class="btn btn-success" style="flex: 1;" onclick="handleProgressAction(${activeAssignment.id}, 'COMPLETED')">
              🏁 MARK COMPLETED
            </button>
          ` : `
            <button class="btn btn-success" style="flex: 1;" onclick="handleProgressAction(${activeAssignment.id}, 'COMPLETED')">
              ✓ MARK ASSISTANCE COMPLETED & RESOLVED
            </button>
          `}
        </div>
      </div>
    `;
  }
}

window.handleResponderAction = async (assignmentId, status) => {
  if (isResponderActionPending) return;
  isResponderActionPending = true;

  stopResponderAcceptanceTimer();

  const btnAccept = document.getElementById('resp-btn-accept');
  const btnDecline = document.getElementById('resp-btn-decline');
  if (btnAccept) btnAccept.disabled = true;
  if (btnDecline) btnDecline.disabled = true;

  try {
    playAlertChime();
    await api.respondToAssignment(assignmentId, status);
    showToast(
      status === 'ACCEPTED' ? 'Responder accepted the emergency assignment.' : 'Responder declined the assignment. Finding another responder.',
      status === 'ACCEPTED' ? 'success' : 'warning'
    );
    await refreshAllData();
  } catch (e) {
    showToast(e.message, 'danger');
    await refreshAllData();
  } finally {
    isResponderActionPending = false;
  }
};

window.handleProgressAction = async (assignmentId, status) => {
  try {
    playAlertChime();
    await api.updateAssignmentProgress(assignmentId, status);
    showToast(`Status updated to ${status}!`, 'success');
    await refreshAllData();
  } catch (e) {
    showToast(e.message, 'danger');
  }
};

// 7. Dispatch Coordinator Dashboard
function updateDispatchBoardTimers() {
  document.querySelectorAll('.dispatch-timer-clock').forEach(el => {
    const raw = el.dataset.assignedAt;
    if (!raw) return;
    const elapsed = Math.floor((Date.now() - parseUtcDate(raw)) / 1000);
    const remaining = Math.max(0, 5 - elapsed);
    el.innerText = `00:${remaining < 10 ? '0' + remaining : remaining}`;
    if (remaining <= 2) {
      el.classList.add('urgent');
    } else {
      el.classList.remove('urgent');
    }
  });
}

async function renderDispatchBoard(incidentsList = null) {
  const incidents = incidentsList || await api.getIncidents().catch(() => []);
  const responders = await api.getResponders().catch(() => []);

  const roster = document.getElementById('dispatch-fleet-grid');
  if (roster) {
    if (responders.length === 0) {
      roster.innerHTML = `<div style="text-align:center; color:var(--text-muted); padding:20px;">No responders in fleet. Admin can create responders in Admin Panel.</div>`;
    } else {
      roster.innerHTML = responders.map(r => `
        <div class="responder-card">
          <div class="responder-top">
            <div class="responder-name">${r.name}</div>
            <span class="badge ${r.availability === 'AVAILABLE' ? 'badge-avail' : r.availability === 'BUSY' ? 'badge-busy' : 'badge-offline'}">
              ${r.availability}
            </span>
          </div>
          <div class="responder-role">${r.role} • <span style="color: var(--accent-blue); font-weight: 600;">${r.specialization}</span></div>
          <div class="responder-meta">
            <span>📍 ${r.current_location}</span>
            <span>⚡ ${r.distance} km</span>
          </div>
          <div style="display: flex; gap: 6px; margin-top: 6px;">
            <button class="sim-btn" style="font-size: 10px; padding: 4px 8px;" onclick="toggleResponderAvailability(${r.id}, 'AVAILABLE')">Available</button>
            <button class="sim-btn" style="font-size: 10px; padding: 4px 8px;" onclick="toggleResponderAvailability(${r.id}, 'BUSY')">Busy</button>
            <button class="sim-btn" style="font-size: 10px; padding: 4px 8px;" onclick="toggleResponderAvailability(${r.id}, 'OFFLINE')">Offline</button>
          </div>
        </div>
      `).join('');
    }
  }

  const tableBody = document.getElementById('dispatch-incidents-body');
  if (tableBody) {
    if (incidents.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No operational incidents recorded.</td></tr>`;
      return;
    }

    tableBody.innerHTML = incidents.map(inc => {
      const assignedResp = responders.find(r => r.id === inc.assigned_responder_id);
      const respName = assignedResp ? assignedResp.name : (inc.assigned_responder_id ? `Unit #${inc.assigned_responder_id}` : '—');

      let statusBadge = '';
      let timerActionDisplay = '';

      if (inc.status === 'WAITING_FOR_RESPONSE') {
        const rawTime = inc.updated_at || inc.created_at;
        const elapsed = Math.floor((Date.now() - parseUtcDate(rawTime)) / 1000);
        const remaining = Math.max(0, 5 - elapsed);
        statusBadge = `<span class="badge badge-busy">WAITING FOR RESPONSE</span>`;
        timerActionDisplay = `<span class="resp-timer-clock dispatch-timer-clock ${remaining <= 2 ? 'urgent' : ''}" data-assigned-at="${rawTime}" style="font-size: 13px; padding: 2px 8px;">00:${remaining < 10 ? '0' + remaining : remaining}</span>`;
      } else if (inc.status === 'NO_RESPONSE') {
        statusBadge = `<span class="badge badge-p1">TIMEOUT</span>`;
        timerActionDisplay = `<span style="color: #ef4444; font-weight: 700; font-size: 11px;">ESCALATING...</span>`;
      } else if (inc.status === 'ASSISTANCE_IN_PROGRESS') {
        statusBadge = `<span class="badge badge-avail">IN_PROGRESS</span>`;
        timerActionDisplay = `<span style="color: var(--accent-emerald); font-size: 12px; font-weight: 600;">ACTIVE</span>`;
      } else if (inc.status === 'RESOLVED') {
        statusBadge = `<span class="badge badge-avail">RESOLVED</span>`;
        timerActionDisplay = `<span style="color: var(--text-muted); font-size: 12px;">RESOLVED</span>`;
      } else {
        statusBadge = `<span class="badge">${inc.status}</span>`;
        timerActionDisplay = `<span style="color: var(--text-muted); font-size: 12px;">—</span>`;
      }

      return `
        <tr style="cursor: pointer;" onclick="selectIncidentForDetail(${inc.id})">
          <td><strong style="font-family: var(--font-mono); color: var(--accent-blue);">INC-${inc.id}</strong></td>
          <td>
            <span class="badge ${inc.priority === 'P1-Critical' ? 'badge-p1' : inc.priority === 'P2-High' ? 'badge-p2' : 'badge-p3'}">
              ${inc.priority || 'Triage'}
            </span>
          </td>
          <td>${inc.emergency_type}</td>
          <td><strong>${respName}</strong></td>
          <td>${statusBadge}</td>
          <td>${timerActionDisplay}</td>
          <td>
            <button class="sim-btn primary" style="font-size: 11px;" onclick="selectIncidentForDetail(${inc.id})">
              Inspect
            </button>
          </td>
        </tr>
      `;
    }).join('');
  }
}

window.toggleResponderAvailability = async (id, availability) => {
  await api.updateResponderStatus(id, availability);
  showToast(`Unit #${id} set to ${availability}`, 'success');
  await refreshAllData();
};

window.selectIncidentForDetail = async (id) => {
  state.activeIncidentId = id;
  const inc = await api.getIncident(id);
  state.activeIncident = inc;
  showToast(`Loaded Incident #${id}`, 'success');
  switchView('timeline');
};

// 8. AI Cognitive Inspector & Decision Timeline
async function renderCognitiveTimeline() {
  const container = document.getElementById('cognitive-timeline-stream');
  if (!container) return;

  if (!state.activeIncidentId) {
    container.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 40px;">Select an incident to view Agent Cognitive Stream.</div>`;
    return;
  }

  const actions = await api.getAgentActions(state.activeIncidentId).catch(() => []);
  document.getElementById('timeline-header-id').innerText = `Incident #INC-${state.activeIncidentId}`;

  if (actions.length === 0) {
    container.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 40px;">Agents are perceiving incoming emergency telemetry...</div>`;
    return;
  }

  container.innerHTML = actions.map(act => {
    let nodeClass = 'analysis';
    let icon = '🧠';
    if (act.agent_name.includes('Selection')) { nodeClass = 'selection'; icon = '📍'; }
    if (act.agent_name.includes('Communication')) { nodeClass = 'comm'; icon = '📡'; }
    if (act.agent_name.includes('Escalation')) { nodeClass = 'escalation'; icon = '⚡'; }
    if (act.agent_name.includes('Report')) { nodeClass = 'resolved'; icon = '📄'; }

    return `
      <div class="timeline-node ${nodeClass}">
        <div class="timeline-dot">${icon}</div>
        <div class="timeline-content-card">
          <div class="timeline-header-row">
            <span class="timeline-actor">${act.agent_name}</span>
            <span class="timeline-time">${formatTime(act.created_at)}</span>
          </div>
          <div style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); font-weight: 700; margin-bottom: 4px;">
            ACTION: ${act.action_type}
          </div>
          <div class="timeline-desc">
            ${act.reasoning || 'Autonomous decision executed.'}
          </div>
          ${act.output_data ? `
            <details style="margin-top: 10px; font-size: 11px;">
              <summary style="cursor: pointer; color: var(--accent-blue); font-family: var(--font-mono); font-weight: 600;">
                View Structured Agent Output JSON
              </summary>
              <pre style="background: #f8fafc; border: 1px solid var(--border-color); padding: 10px 12px; border-radius: var(--radius-sm); margin-top: 6px; overflow-x: auto; color: var(--text-primary); font-family: var(--font-mono); font-size: 12px;">${formatJson(act.output_data)}</pre>
            </details>
          ` : ''}
        </div>
      </div>
    `;
  }).join('');
}

function formatJson(str) {
  try {
    return JSON.stringify(JSON.parse(str), null, 2);
  } catch (e) {
    return str;
  }
}

// 9. Incident Report Section
async function renderReportSection() {
  const container = document.getElementById('report-display-container');
  if (!container) return;

  if (!state.activeIncidentId) {
    container.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 50px;">Select an incident to view its post-incident report.</div>`;
    return;
  }

  let report = await api.getReport(state.activeIncidentId);

  if (!report) {
    container.innerHTML = `
      <div class="glass-card" style="text-align: center; padding: 50px 20px;">
        <div style="font-size: 42px; margin-bottom: 12px;">📊</div>
        <h2 style="font-family: var(--font-heading); color: var(--text-primary); margin-bottom: 8px;">No Debrief Report Generated Yet</h2>
        <p style="font-size: 13px; color: var(--text-secondary); max-width: 500px; margin: 0 auto 20px auto;">
          Incident #INC-${state.activeIncidentId} is in progress or awaiting resolution.
        </p>
        <button class="btn btn-primary" onclick="triggerReportGeneration(${state.activeIncidentId})">
          ⚡ Trigger AI Report Agent Now
        </button>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="report-paper">
      <div class="report-header-banner">
        <div>
          <div class="report-id">INCIDENT REPORT • INC-${report.incident_id}</div>
          <h1 style="font-family: var(--font-heading); font-size: 26px; color: var(--text-primary); margin-top: 4px;">
            Emergency Response Postmortem
          </h1>
        </div>
        <button class="btn btn-outline" onclick="window.print()">
          🖨️ Print / Export PDF
        </button>
      </div>

      <div class="report-grid-stats">
        <div class="report-stat-box">
          <div class="report-stat-label">Emergency Category</div>
          <div class="report-stat-value" style="color: var(--accent-blue);">${report.emergency_type}</div>
        </div>
        <div class="report-stat-box">
          <div class="report-stat-label">Triage Priority</div>
          <div class="report-stat-value" style="color: var(--accent-red);">${report.priority}</div>
        </div>
        <div class="report-stat-box">
          <div class="report-stat-label">Initial Responder</div>
          <div class="report-stat-value">${report.initial_responder || 'None'}</div>
        </div>
        <div class="report-stat-box">
          <div class="report-stat-label">Final Responder</div>
          <div class="report-stat-value" style="color: var(--accent-emerald);">${report.final_responder || 'None'}</div>
        </div>
        <div class="report-stat-box">
          <div class="report-stat-label">Escalations Count</div>
          <div class="report-stat-value" style="color: ${report.escalation_count > 0 ? 'var(--accent-amber)' : 'var(--text-muted)'};">
            ${report.escalation_count}
          </div>
        </div>
        <div class="report-stat-box">
          <div class="report-stat-label">Final Status</div>
          <div class="report-stat-value" style="color: var(--accent-emerald);">${report.final_status}</div>
        </div>
      </div>

      <div style="margin-bottom: 24px;">
        <h3 style="font-family: var(--font-heading); font-size: 16px; margin-bottom: 8px; color: var(--text-primary);">
          Executive Debrief Summary
        </h3>
        <p style="font-size: 14px; line-height: 1.6; color: var(--text-primary); background: #f8fafc; border: 1px solid var(--border-color); padding: 16px; border-radius: var(--radius-sm); border-left: 4px solid var(--accent-blue);">
          ${report.summary}
        </p>
      </div>

      <div>
        <h3 style="font-family: var(--font-heading); font-size: 15px; margin-bottom: 8px; color: var(--text-primary);">
          Agentic Cognitive Trace Architecture
        </h3>
        <div style="display: flex; gap: 8px; flex-wrap: wrap; font-family: var(--font-mono); font-size: 12px; color: var(--accent-emerald);">
          <span class="badge badge-p3">PERCEIVE</span> → 
          <span class="badge badge-p3">REASON</span> → 
          <span class="badge badge-p3">DECIDE</span> → 
          <span class="badge badge-p3">ACT</span> → 
          <span class="badge badge-p2">OBSERVE</span> → 
          <span class="badge badge-p1">ADAPT</span>
        </div>
      </div>
    </div>
  `;
}

window.triggerReportGeneration = async (incidentId) => {
  try {
    playAlertChime();
    showToast('AI Report Agent synthesizing debrief...', 'success');
    await api.generateReport(incidentId);
    await renderReportSection();
  } catch (e) {
    showToast(e.message, 'danger');
  }
};

// 10. Administrator Dashboard
function setupAdminForms() {
  const createForm = document.getElementById('admin-create-user-form');
  createForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('admin-new-name').value.trim();
    const email = document.getElementById('admin-new-email').value.trim();
    const password = document.getElementById('admin-new-pwd').value;
    const role = document.getElementById('admin-new-role').value;

    const payload = { name, email, password, role };
    if (role === 'responder') {
      payload.responder_role = document.getElementById('admin-resp-role').value;
      payload.specialization = document.getElementById('admin-resp-spec').value;
      payload.distance = parseFloat(document.getElementById('admin-resp-dist').value) || 1.0;
    }

    try {
      await api.adminCreateUser(payload);
      showToast(`User ${name} provisioned successfully (${role.toUpperCase()})!`, 'success');
      createForm.reset();
      toggleAdminCreateForm(false);
      await renderAdminDashboard();
    } catch (err) {
      showToast(err.message, 'danger');
    }
  });
}

function toggleAdminCreateForm(forceState = null) {
  const panel = document.getElementById('admin-create-user-panel');
  if (!panel) return;
  if (forceState !== null) {
    panel.style.display = forceState ? 'block' : 'none';
  } else {
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
  }
}

window.toggleAdminCreateForm = toggleAdminCreateForm;

function toggleResponderParams(role) {
  const fields = document.getElementById('admin-responder-fields');
  if (fields) {
    fields.style.display = role === 'responder' ? 'grid' : 'none';
  }
}

window.toggleResponderParams = toggleResponderParams;

async function renderAdminDashboard() {
  if (!state.currentUser || state.currentUser.role !== 'admin') return;
  const tbody = document.getElementById('admin-users-table-body');
  if (!tbody) return;

  try {
    const users = await api.adminGetUsers();
    tbody.innerHTML = users.map(u => `
      <tr>
        <td><strong style="font-family: var(--font-mono); color: var(--accent-blue);">#${u.id}</strong></td>
        <td><strong>${u.name}</strong></td>
        <td>${u.email}</td>
        <td><span class="user-role-tag role-tag-${u.role.toLowerCase()}">${u.role.toUpperCase()}</span></td>
        <td>
          <span class="badge ${u.is_active ? 'badge-avail' : 'badge-busy'}">
            ${u.is_active ? 'ACTIVE' : 'DEACTIVATED'}
          </span>
        </td>
        <td>${new Date(u.created_at).toLocaleDateString()}</td>
        <td>
          <button class="sim-btn ${u.is_active ? 'danger' : 'primary'}" style="font-size: 11px; padding: 4px 8px;" onclick="adminToggleUserStatus(${u.id}, ${!u.is_active})">
            ${u.is_active ? 'Deactivate' : 'Activate'}
          </button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--accent-red);">${err.message}</td></tr>`;
  }
}

window.adminToggleUserStatus = async (userId, newStatus) => {
  try {
    await api.adminToggleUserStatus(userId, newStatus);
    showToast(`User status updated to ${newStatus ? 'ACTIVE' : 'DEACTIVATED'}.`, 'success');
    await renderAdminDashboard();
  } catch (err) {
    showToast(err.message, 'danger');
  }
};

// 11. Simulation Controls
function setupSimulationBar() {
  document.getElementById('btn-reset-sim')?.addEventListener('click', async () => {
    if (confirm('Reset operational incident records and simulation state?')) {
      await api.resetSimulation();
      state.activeIncidentId = null;
      state.activeIncident = null;
      showToast('Simulation state cleared.', 'success');
      await refreshAllData();
    }
  });

  document.getElementById('btn-scenario-1')?.addEventListener('click', async () => {
    playAlertChime();
    const payload = {
      emergency_type: 'Accident',
      description: 'Minor two-car collision at crossroad, passenger suffering from sprain and cuts.',
      location: 'Sector 3 Market Road'
    };
    const inc = await api.createIncident(payload);
    state.activeIncidentId = inc.id;
    state.activeIncident = inc;
    showToast('Scenario 1 Launched: Road Accident -> Suresh assigned.', 'success');
    switchView('responder');
    await refreshAllData();
  });

  document.getElementById('btn-scenario-2')?.addEventListener('click', async () => {
    playAlertChime();
    const payload = {
      emergency_type: 'Accident',
      description: 'HIGH SPEED VEHICLE OVERTURNED: Victim trapped, heavy bleeding, smoke billowing from engine.',
      location: 'Highway 101, Mile 42'
    };
    const inc = await api.createIncident(payload);
    state.activeIncidentId = inc.id;
    state.activeIncident = inc;
    showToast('Scenario 2 Launched: Critical Crash -> Click "Simulate Timeout" to watch auto-escalation!', 'warning');
    switchView('timeline');
    await refreshAllData();
  });

  document.getElementById('btn-timeout-sim')?.addEventListener('click', async () => {
    if (!state.activeIncidentId) {
      showToast('No active incident selected. Create an incident first.', 'warning');
      return;
    }
    try {
      const res = await api.triggerTimeout(state.activeIncidentId);
      playSirenPing();
      showToast(`Timeout Triggered! ${res.timed_out_responder} dropped. Escalation Agent activated.`, 'danger');
      await refreshAllData();
      switchView('timeline');
    } catch (e) {
      showToast(e.message, 'danger');
    }
  });
}

window.triggerTimeoutSimulation = async () => {
  const btn = document.getElementById('btn-timeout-sim');
  if (btn) btn.click();
};

// UI Notification Toast
function showToast(message, type = 'success') {
  const existing = document.querySelector('.toast-banner');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = `toast-banner ${type}`;
  toast.style.cssText = `
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 1000;
    padding: 12px 20px;
    border-radius: var(--radius-md);
    font-weight: 600;
    font-size: 13px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    background: ${type === 'danger' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#10b981'};
    color: white;
    display: flex;
    align-items: center;
    gap: 8px;
    animation: fadeIn 0.2s ease;
  `;
  toast.innerHTML = `<span>${type === 'danger' ? '⚠️' : type === 'warning' ? '⚡' : '✓'}</span> ${message}`;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}
