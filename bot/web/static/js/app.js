/**
 * Troop Command — Admin Panel Client Logic
 */

// State
const state = {
  user: { authenticated: false, role: 'guest', name: null },
  players: [],
  stats: null,
  activeFilter: 'all',
  searchQuery: '',
  currentGuildId: localStorage.getItem('troop_guild_id') || '*',
  activeAllianceTag: '',
  allianceTags: [],
  guilds: [],
  botInfo: null,

  sim: {
    mode: 'attack',
    formation_type: 'rally',
    inf: 50,
    lan: 20,
    mrk: 30,
    capacity: 1500000,
    heroes: ['Jessie', 'Jasser', 'Seoyoon', 'Norah'],
    result: null,
  },
  editingPlayerId: null,
  deletingPlayerId: null,
  // Hero tracking for the modal form
  formHeroes: [],   // [{name, stars, skill_level}]
  // Formation presets (loaded once)
  presets: [],
  heroCatalog: [],
  heroPresets: [],
};

// DOM Elements
const elements = {
  // Tabs
  navTabs: document.querySelectorAll('.nav-tab'),
  tabPanes: document.querySelectorAll('.tab-pane'),
  // Server picker & invite
  serverPickerWrap: document.getElementById('server-picker-wrap'),
  serverSelect: document.getElementById('server-select'),
  btnHeaderInvite: document.getElementById('btn-header-invite'),
  btnGuideInvite: document.getElementById('btn-guide-invite'),
  // Auth
  userRoleBadge: document.getElementById('user-role-badge'),
  userDisplayName: document.getElementById('user-display-name'),
  btnAuthAction: document.getElementById('btn-auth-action'),
  authModal: document.getElementById('auth-modal'),
  authCloseBtn: document.getElementById('auth-modal-close'),
  authForm: document.getElementById('auth-passkey-form'),
  authPasskeyInput: document.getElementById('auth-passkey-input'),
  authOauthWrap: document.getElementById('auth-oauth-wrap'),
  authOauthDivider: document.getElementById('auth-oauth-divider'),

  // Stats
  statTotalPlayers: document.getElementById('stat-total-players'),
  statCompletePlayers: document.getElementById('stat-complete-players'),
  statIncompletePlayers: document.getElementById('stat-incomplete-players'),
  statTotalCapacity: document.getElementById('stat-total-capacity'),
  statTotalHelios: document.getElementById('stat-total-helios'),
  statAvgFc: document.getElementById('stat-avg-fc'),
  statFcBreakdown: document.getElementById('stat-fc-breakdown'),
  barInfStat: document.getElementById('bar-infantry-stat'),
  barLanStat: document.getElementById('bar-lancers-stat'),
  barMrkStat: document.getElementById('bar-marksman-stat'),
  barInfFill: document.getElementById('bar-infantry-fill'),
  barLanFill: document.getElementById('bar-lancers-fill'),
  barMrkFill: document.getElementById('bar-marksman-fill'),
  // Roster
  rosterTableBody: document.getElementById('roster-table-body'),
  rosterSearch: document.getElementById('roster-search'),
  rosterAllianceSelect: document.getElementById('roster-alliance-select'),
  filterChips: document.querySelectorAll('.filter-chip'),
  btnAddPlayer: document.getElementById('btn-add-player'),
  btnImportCsv: document.getElementById('btn-import-csv'),
  btnSurveyGenerator: document.getElementById('btn-survey-generator'),
  btnGuideSurvey: document.getElementById('btn-guide-survey'),
  csvFileInput: document.getElementById('csv-file-input'),
  btnQuickAddPlayer: document.getElementById('btn-quick-add-player'),
  btnQuickCalculate: document.getElementById('btn-quick-calculate'),
  btnClearRoster: document.getElementById('btn-clear-roster'),
  clearDataModal: document.getElementById('clear-data-modal'),
  clearDataModalClose: document.getElementById('clear-data-modal-close'),
  clearDataModalCancel: document.getElementById('clear-data-modal-cancel'),
  clearDataModalConfirm: document.getElementById('clear-data-modal-confirm'),
  clearDataServerName: document.getElementById('clear-data-server-name'),
  // Survey Modal
  surveyModal: document.getElementById('survey-modal'),
  surveyModalClose: document.getElementById('survey-modal-close'),
  surveyModalDone: document.getElementById('survey-modal-done'),
  btnCopySurveyScript: document.getElementById('btn-copy-survey-script'),
  surveyScriptCode: document.getElementById('survey-script-code'),
  // Modals
  playerModal: document.getElementById('player-modal'),
  playerModalTitle: document.getElementById('player-modal-title'),
  playerModalClose: document.getElementById('player-modal-close'),
  playerModalCancel: document.getElementById('player-modal-cancel'),
  playerForm: document.getElementById('player-form'),
  formPlayerId: document.getElementById('form-player-id'),
  formName: document.getElementById('form-name'),
  formGameId: document.getElementById('form-game-id'),
  formMarchLimit: document.getElementById('form-march-limit'),
  formAllianceTag: document.getElementById('form-alliance-tag'),
  formDiscordId: document.getElementById('form-discord-id'),

  formInfHelios: document.getElementById('form-inf-helios'),
  formInfLevel: document.getElementById('form-inf-level'),
  formInfQty: document.getElementById('form-inf-qty'),
  formLanHelios: document.getElementById('form-lan-helios'),
  formLanLevel: document.getElementById('form-lan-level'),
  formLanQty: document.getElementById('form-lan-qty'),
  formMrkHelios: document.getElementById('form-mrk-helios'),
  formMrkLevel: document.getElementById('form-mrk-level'),
  formMrkQty: document.getElementById('form-mrk-qty'),
  deleteModal: document.getElementById('delete-modal'),
  deleteModalClose: document.getElementById('delete-modal-close'),
  deleteModalCancel: document.getElementById('delete-modal-cancel'),
  deleteModalConfirm: document.getElementById('delete-modal-confirm'),
  deletePlayerName: document.getElementById('delete-player-name'),
  // Simulator
  simModeBtns: document.querySelectorAll('#sim-mode-toggle .segment-btn'),
  simTypeBtns: document.querySelectorAll('#sim-type-toggle .segment-btn'),
  sliderInf: document.getElementById('slider-inf'),
  sliderLan: document.getElementById('slider-lan'),
  sliderMrk: document.getElementById('slider-mrk'),
  numInf: document.getElementById('num-inf'),
  numLan: document.getElementById('num-lan'),
  numMrk: document.getElementById('num-mrk'),
  ratioSumBadge: document.getElementById('ratio-sum-badge'),
  simCapacityInput: document.getElementById('sim-capacity'),
  btnRunSim: document.getElementById('btn-run-simulation'),
  simPlaceholder: document.getElementById('sim-placeholder'),
  simContent: document.getElementById('sim-content'),
  simFillPct: document.getElementById('sim-fill-pct'),
  simTotalAssigned: document.getElementById('sim-total-assigned'),
  simTargetCapacity: document.getElementById('sim-target-capacity'),
  simPlayersCount: document.getElementById('sim-players-count'),
  simComparisonBars: document.getElementById('sim-comparison-bars'),
  simAssignmentsTbody: document.getElementById('sim-assignments-tbody'),
  simResultTitle: document.getElementById('sim-result-title'),
  simResultMeta: document.getElementById('sim-result-meta'),
  simGenSelect: document.getElementById('sim-gen-select'),
  simAllianceSelect: document.getElementById('sim-alliance-select'),
  simPresetSelect: null, // removed
  simPresetGuide: null,  // removed
  simPresetPlace: null,
  simPresetCallers: null,
  simPresetJoiners: null,
  simPresetNotes: null,
  simJoinersCard: document.getElementById('sim-joiners-card'),
  simJoinersList: document.getElementById('sim-joiners-list'),
  // Captain & Captain Heroes (Simulator)
  simCaptainSelect: document.getElementById('sim-captain-select'),
  simCaptainHero1: document.getElementById('sim-captain-hero-1'),
  simCaptainHero2: document.getElementById('sim-captain-hero-2'),
  simCaptainHero3: document.getElementById('sim-captain-hero-3'),
  simCaptainBuff1: document.getElementById('sim-captain-buff-1'),
  simCaptainBuff2: document.getElementById('sim-captain-buff-2'),
  simCaptainBuff3: document.getElementById('sim-captain-buff-3'),
  // Target Hero Slots (Simulator)
  simHeroSlot1: document.getElementById('sim-hero-slot-1'),
  simHeroSlot2: document.getElementById('sim-hero-slot-2'),
  simHeroSlot3: document.getElementById('sim-hero-slot-3'),
  simHeroSlot4: document.getElementById('sim-hero-slot-4'),
  simHeroBuff1: document.getElementById('sim-hero-buff-1'),
  simHeroBuff2: document.getElementById('sim-hero-buff-2'),
  simHeroBuff3: document.getElementById('sim-hero-buff-3'),
  simHeroBuff4: document.getElementById('sim-hero-buff-4'),
  btnHeroPresets: document.querySelectorAll('.btn-hero-preset'),
  btnHeroReset: document.getElementById('btn-hero-reset'),
  // Rules
  ruleAttackOrder: document.getElementById('rule-attack-order'),
  ruleDefenceOrder: document.getElementById('rule-defence-order'),
  ruleHeliosBonus: document.getElementById('rule-helios-bonus'),
  ruleFcWeight: document.getElementById('rule-fc-weight'),
  btnSaveRules: document.getElementById('btn-save-rules'),
  // Toasts
  toastContainer: document.getElementById('toast-container'),
  // Hero form elements
  heroAddName: document.getElementById('hero-add-name'),
  btnAddHero: document.getElementById('btn-add-hero'),
  heroesGrid: document.getElementById('heroes-grid'),
};

// Utilities
function formatNumber(num) {
  if (num === null || num === undefined) return '0';
  return Number(num).toLocaleString();
}

function formatFcLevel(lvl, decimals) {
  if (lvl === null || lvl === undefined) return '';
  const num = Number(lvl);
  if (isNaN(num)) return '';
  if (num >= 31) {
    const fc = num - 30;
    if (decimals !== undefined && !Number.isInteger(fc)) return `FC${fc.toFixed(decimals)}`;
    return `FC${fc}`;
  }
  if (decimals !== undefined && !Number.isInteger(num)) return `F${num.toFixed(decimals)}`;
  return `F${num}`;
}


function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
  toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
  elements.toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(40px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// API client
async function fetchApi(url, options = {}) {
  try {
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };
    if (state.currentGuildId && state.currentGuildId !== '*') {
      headers['X-Guild-Id'] = state.currentGuildId;
    }
    const res = await fetch(url, {
      ...options,
      headers,
    });
    if (res.status === 401) {
      if (!url.includes('/api/auth/login') && !url.includes('/api/auth/me')) {
        state.user = { authenticated: false, role: 'guest', name: null };
        renderAuth();
        openAuthModal();
        throw new Error('Authentication required');
      }
    }
    const text = await res.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch (e) {
      throw new Error(`Server returned non-JSON response (${res.status}): ${text.substring(0, 100)}`);
    }
    if (!res.ok) {
      throw new Error(data.error || 'Server error');
    }
    return data;

  } catch (err) {
    throw err;
  }
}

// Bot Info & Invite Link
async function loadBotInfo() {
  try {
    const res = await fetch('/api/bot/info');
    if (res.ok) {
      const data = await res.json();
      state.botInfo = data;
      if (data.invite_url) {
        if (elements.btnHeaderInvite) elements.btnHeaderInvite.href = data.invite_url;
        if (elements.btnGuideInvite) elements.btnGuideInvite.href = data.invite_url;
      }
    }
  } catch (e) {
    console.warn('Could not load bot info:', e);
  }
}

// Guilds / Multi-Server Picker
async function loadGuilds() {
  if (!state.user.authenticated) {
    if (elements.serverPickerWrap) elements.serverPickerWrap.style.display = 'none';
    return;
  }
  try {
    const guilds = await fetchApi('/api/guilds');
    state.guilds = guilds;

    if (!elements.serverSelect) return;
    elements.serverSelect.innerHTML = '';

    if (!guilds || guilds.length === 0) {
      if (elements.serverPickerWrap) elements.serverPickerWrap.style.display = 'none';
      return;
    }

    if (elements.serverPickerWrap) elements.serverPickerWrap.style.display = 'flex';

    // Verify current selection is in list
    const validIds = guilds.map(g => g.id);
    if (!validIds.includes(state.currentGuildId)) {
      state.currentGuildId = validIds[0] || '*';
      localStorage.setItem('troop_guild_id', state.currentGuildId);
    }

    guilds.forEach(g => {
      const opt = document.createElement('option');
      opt.value = g.id;
      opt.textContent = g.name + (!g.bot_installed ? ' (➕ Add Bot)' : '');
      if (g.id === state.currentGuildId) opt.selected = true;
      elements.serverSelect.appendChild(opt);
    });
  } catch (err) {
    console.warn('Failed to load guilds:', err);
  }
}

// Auth Lifecycle
async function checkAuth() {
  try {
    const data = await fetchApi('/api/auth/me');
    state.user = data;
    renderAuth();
    if (!data.has_discord_oauth && elements.authOauthWrap) {
      elements.authOauthWrap.style.display = 'none';
      if (elements.authOauthDivider) elements.authOauthDivider.style.display = 'none';
    }
    await loadBotInfo();
    if (data.authenticated) {
      await loadGuilds();
    }
  } catch (err) {
    renderAuth();
    await loadBotInfo();
  }
}

function renderAuth() {
  if (state.user.authenticated) {
    elements.userRoleBadge.textContent = state.user.role;
    elements.userRoleBadge.className = `user-badge ${state.user.role}`;
    elements.userDisplayName.textContent = state.user.name || 'Admin';
    elements.btnAuthAction.textContent = 'Logout';
  } else {
    elements.userRoleBadge.textContent = 'Guest';
    elements.userRoleBadge.className = 'user-badge';
    elements.userDisplayName.textContent = 'Not Logged In';
    elements.btnAuthAction.textContent = 'Login';
    if (elements.serverPickerWrap) elements.serverPickerWrap.style.display = 'none';
  }
}


function openAuthModal() {
  if (elements.authModal) {
    elements.authModal.classList.add('active');
    if (elements.authPasskeyInput) {
      elements.authPasskeyInput.value = '';
      elements.authPasskeyInput.focus();
    }
  }
}

function closeAuthModal() {
  if (elements.authModal) {
    elements.authModal.classList.remove('active');
  }
}

function openSurveyModal() {
  if (elements.surveyModal) elements.surveyModal.classList.add('active');
}

function closeSurveyModal() {
  if (elements.surveyModal) elements.surveyModal.classList.remove('active');
}

async function copySurveyScript() {
  const code = elements.surveyScriptCode ? elements.surveyScriptCode.innerText : '';
  if (!code) return;
  try {
    await navigator.clipboard.writeText(code);
    showToast('Google Apps Script copied to clipboard! 📋', 'success');
  } catch (e) {
    const textarea = document.createElement('textarea');
    textarea.value = code;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    textarea.remove();
    showToast('Google Apps Script copied to clipboard! 📋', 'success');
  }
}

// Navigation Tabs
function switchTab(tabId) {
  elements.navTabs.forEach((btn) => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });
  elements.tabPanes.forEach((pane) => {
    pane.classList.toggle('active', pane.id === `pane-${tabId}`);
  });

  // Close mobile nav menu when a tab is selected
  closeMobileMenu();

  if (tabId === 'overview') loadStats();
  if (tabId === 'roster') loadPlayers();
  if (tabId === 'rules') loadRules();
}

// Mobile Hamburger Menu
const hamburgerBtn = document.getElementById('hamburger-btn');
const headerCenter = document.getElementById('header-center');
const headerRight = document.querySelector('.header-right');

// Track original DOM position so we can restore on close
let _hrOriginalParent = headerRight ? headerRight.parentNode : null;
let _hrOriginalNextSibling = headerRight ? headerRight.nextSibling : null;

function isMobile() {
  return window.innerWidth <= 1024;
}

function openMobileMenu() {
  if (!headerCenter) return;
  headerCenter.classList.add('open');
  if (hamburgerBtn) hamburgerBtn.classList.add('active');

  // Move header-right into the dropdown so all items appear together
  if (isMobile() && headerRight && !headerCenter.contains(headerRight)) {
    headerCenter.appendChild(headerRight);
    headerRight.classList.add('mobile-in-dropdown');
  }
}

function closeMobileMenu() {
  if (!headerCenter) return;
  headerCenter.classList.remove('open');
  if (hamburgerBtn) hamburgerBtn.classList.remove('active');

  // Restore header-right to its original place in the header
  if (headerRight && headerRight.classList.contains('mobile-in-dropdown')) {
    headerRight.classList.remove('mobile-in-dropdown');
    if (_hrOriginalNextSibling && _hrOriginalParent && _hrOriginalParent.contains(_hrOriginalNextSibling)) {
      _hrOriginalParent.insertBefore(headerRight, _hrOriginalNextSibling);
    } else if (_hrOriginalParent) {
      _hrOriginalParent.appendChild(headerRight);
    }
  }
}

function toggleMobileMenu() {
  const isOpen = headerCenter && headerCenter.classList.contains('open');
  if (isOpen) {
    closeMobileMenu();
  } else {
    openMobileMenu();
  }
}

if (hamburgerBtn) {
  hamburgerBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleMobileMenu();
  });
}

// On resize to desktop: ensure header-right is restored and menu is closed
window.addEventListener('resize', () => {
  if (!isMobile()) {
    closeMobileMenu();
  }
});

// Close mobile menu when clicking outside the header
document.addEventListener('click', (e) => {
  const header = document.querySelector('.app-header');
  if (
    headerCenter && headerCenter.classList.contains('open') &&
    header && !header.contains(e.target) &&
    headerCenter && !headerCenter.contains(e.target)
  ) {
    closeMobileMenu();
  }
});

// Load Stats
async function loadStats() {
  try {
    const stats = await fetchApi('/api/stats');
    state.stats = stats;
    renderStats();
  } catch (err) {
    console.error('Failed to load stats:', err);
  }
}

function renderStats() {
  if (!state.stats) return;
  const s = state.stats;
  elements.statTotalPlayers.textContent = formatNumber(s.total_players);
  elements.statCompletePlayers.textContent = `${s.complete_players} Complete`;
  elements.statIncompletePlayers.textContent = `${s.incomplete_players} Incomplete`;
  elements.statTotalCapacity.textContent = formatNumber(s.total_capacity);

  const totalHelios = (s.helios_quantities.infantry || 0) + (s.helios_quantities.lancers || 0) + (s.helios_quantities.marksman || 0);
  elements.statTotalHelios.textContent = formatNumber(totalHelios);

  const avgFcOverall = (s.average_levels.infantry + s.average_levels.lancers + s.average_levels.marksman) / 3;
  elements.statAvgFc.textContent = formatFcLevel(avgFcOverall, 3);
  elements.statFcBreakdown.textContent = `Inf: ${formatFcLevel(s.average_levels.infantry, 3)} | Lan: ${formatFcLevel(s.average_levels.lancers, 3)} | Mrk: ${formatFcLevel(s.average_levels.marksman, 3)}`;

  // Breakdown bars
  elements.barInfStat.textContent = `${formatNumber(s.helios_quantities.infantry)} Helios | Avg ${formatFcLevel(s.average_levels.infantry, 3)}`;
  elements.barLanStat.textContent = `${formatNumber(s.helios_quantities.lancers)} Helios | Avg ${formatFcLevel(s.average_levels.lancers, 3)}`;
  elements.barMrkStat.textContent = `${formatNumber(s.helios_quantities.marksman)} Helios | Avg ${formatFcLevel(s.average_levels.marksman, 3)}`;


  const maxVal = Math.max(1, s.helios_quantities.infantry, s.helios_quantities.lancers, s.helios_quantities.marksman);
  elements.barInfFill.style.width = `${Math.max(15, (s.helios_quantities.infantry / maxVal) * 100)}%`;
  elements.barLanFill.style.width = `${Math.max(15, (s.helios_quantities.lancers / maxVal) * 100)}%`;
  elements.barMrkFill.style.width = `${Math.max(15, (s.helios_quantities.marksman / maxVal) * 100)}%`;
}

async function loadAllianceTags() {
  try {
    const tags = await fetchApi('/api/alliance-tags');
    state.allianceTags = tags || [];
    populateAllianceTagSelects();
  } catch (err) {
    console.error('Failed to load alliance tags:', err);
  }
}

function populateAllianceTagSelects() {
  const optionsHtml = '<option value="">All Alliance Tags</option>' +
    state.allianceTags.map(t => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join('');

  if (elements.rosterAllianceSelect) {
    elements.rosterAllianceSelect.innerHTML = optionsHtml;
    elements.rosterAllianceSelect.value = state.activeAllianceTag;
  }
  if (elements.simAllianceSelect) {
    elements.simAllianceSelect.innerHTML = optionsHtml;
  }
}

// Load Players
async function loadPlayers() {
  try {
    const q = encodeURIComponent(state.searchQuery);
    const filter = encodeURIComponent(state.activeFilter);
    const tag = encodeURIComponent(state.activeAllianceTag);
    const [players, attRes] = await Promise.all([
      fetchApi(`/api/players?q=${q}&filter=${filter}&alliance_tag=${tag}`),
      fetchApi('/api/attendance')
    ]);
    state.players = players;
    window.warRoomAttendance = new Set(attRes.checked_in_ids || []);

    const countEl = document.getElementById('war-online-count');
    if (countEl) countEl.textContent = window.warRoomAttendance.size;

    renderRoster();
    populateCaptainSelect();
  } catch (err) {
    elements.rosterTableBody.innerHTML = `<tr><td colspan="9" class="empty-cell text-danger">Failed to load players: ${err.message}</td></tr>`;
  }
}

function populateCaptainSelect() {
  const sel = elements.simCaptainSelect;
  if (sel) {
    const currentVal = sel.value;
    sel.innerHTML = '<option value="">Auto / Highest Power Player</option>';

    const players = state.players || [];
    players.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = `${p.name} (March Limit: ${formatNumber(p.march_limit)})`;
      sel.appendChild(opt);
    });

    sel.value = currentVal;
  }
  renderCaptainSelectionBlocks();
}

function renderCaptainSelectionBlocks() {
  const container = document.getElementById('sim-captains-container');
  if (!container) return;

  const formationType = state.sim.formation_type || 'rally';
  const rallyCountEl = document.getElementById('sim-rally-count');
  const count = formationType === 'garrison' ? 1 : parseInt(rallyCountEl?.value || '1', 10);
  const genSelect = document.getElementById('sim-gen-select');
  const selectedGen = parseInt(genSelect?.value || '7', 10) || 7;

  const catalog = state.heroCatalog || [];
  const validHeroes = catalog.filter(h => !h.gen_introduced || h.gen_introduced <= selectedGen);

  const infHeroes = validHeroes.filter(h => h.troop_type === 'infantry');
  const lanHeroes = validHeroes.filter(h => h.troop_type === 'lancer');
  const mrkHeroes = validHeroes.filter(h => h.troop_type === 'marksman');

  const makeHeroOptionsHtml = (troopType, heroList) => {
    let html = `<option value="">Auto (${troopType.toUpperCase()} Hero)</option>`;
    heroList.forEach(h => {
      const genLabel = h.gen_introduced ? ` [Gen ${h.gen_introduced}]` : '';
      const buffLabel = h.buff ? ` - ${h.buff}` : '';
      html += `<option value="${escapeHtml(h.name)}">${escapeHtml(h.name)}${genLabel}${escapeHtml(buffLabel)}</option>`;
    });
    return html;
  };

  const players = state.players || [];
  let playerOptionsHtml = '<option value="">Auto / Highest Power Player</option>';
  players.forEach(p => {
    const isOnline = window.warRoomAttendance ? window.warRoomAttendance.has(p.id) : true;
    if (isOnline) {
      playerOptionsHtml += `<option value="${p.id}">${escapeHtml(p.name)} (March: ${formatNumber(p.march_limit)})</option>`;
    }
  });

  let blocksHtml = '';

  for (let i = 1; i <= count; i++) {
    const blockTitle = formationType === 'garrison'
      ? 'Garrison Captain & 3 Heroes'
      : (count > 1 ? `Rally ${i} Captain & 3 Heroes` : 'Rally Captain & 3 Heroes');

    const prevCap = document.getElementById(`sim-captain-select-${i}`)?.value || '';
    const prevInf = document.getElementById(`sim-captain-hero-inf-${i}`)?.value || '';
    const prevLan = document.getElementById(`sim-captain-hero-lan-${i}`)?.value || '';
    const prevMrk = document.getElementById(`sim-captain-hero-mrk-${i}`)?.value || '';

    blocksHtml += `
      <div class="form-group captain-selection-block" style="background:rgba(255,255,255,0.02); padding:14px; border-radius:8px; border:1px solid var(--border-color); margin-bottom:16px;">
        <div class="label-with-meta" style="margin-bottom:10px;">
          <label class="form-label" style="color:var(--color-amber); font-weight:700; font-size:13px; margin:0;">👑 ${blockTitle}</label>
          <span class="form-section-hint">Infantry (Left) | Lancer (Mid) | Marksman (Right) — Gen ≤ ${selectedGen}</span>
        </div>
        
        <div style="margin-bottom:10px;">
          <select class="form-input sim-captain-select-input" id="sim-captain-select-${i}" data-index="${i}">
            ${playerOptionsHtml}
          </select>
        </div>

        <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:8px;">
          <div>
            <label style="font-size:11px; color:var(--troop-inf); font-weight:600; display:block; margin-bottom:4px;">🛡️ Infantry Hero (Left)</label>
            <select class="form-input sim-hero-select-inf" id="sim-captain-hero-inf-${i}">
              ${makeHeroOptionsHtml('infantry', infHeroes)}
            </select>
          </div>
          <div>
            <label style="font-size:11px; color:var(--troop-lan); font-weight:600; display:block; margin-bottom:4px;">⚡ Lancer Hero (Middle)</label>
            <select class="form-input sim-hero-select-lan" id="sim-captain-hero-lan-${i}">
              ${makeHeroOptionsHtml('lancer', lanHeroes)}
            </select>
          </div>
          <div>
            <label style="font-size:11px; color:var(--troop-mrk); font-weight:600; display:block; margin-bottom:4px;">🎯 Marksman Hero (Right)</label>
            <select class="form-input sim-hero-select-mrk" id="sim-captain-hero-mrk-${i}">
              ${makeHeroOptionsHtml('marksman', mrkHeroes)}
            </select>
          </div>
        </div>
      </div>
    `;
  }

  container.innerHTML = blocksHtml;

  for (let i = 1; i <= count; i++) {
    const capEl = document.getElementById(`sim-captain-select-${i}`);
    const infEl = document.getElementById(`sim-captain-hero-inf-${i}`);
    const lanEl = document.getElementById(`sim-captain-hero-lan-${i}`);
    const mrkEl = document.getElementById(`sim-captain-hero-mrk-${i}`);

    if (capEl && prevCap && capEl.querySelector(`option[value="${prevCap}"]`)) capEl.value = prevCap;
    if (infEl && prevInf && infEl.querySelector(`option[value="${prevInf}"]`)) infEl.value = prevInf;
    if (lanEl && prevLan && lanEl.querySelector(`option[value="${prevLan}"]`)) lanEl.value = prevLan;
    if (mrkEl && prevMrk && mrkEl.querySelector(`option[value="${prevMrk}"]`)) mrkEl.value = prevMrk;
  }
}


function renderRoster() {
  const tbody = elements.rosterTableBody;
  if (!state.players || state.players.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="empty-cell">No players found matching current search/filter.</td></tr>`;
    return;
  }

  tbody.innerHTML = state.players.map((p) => {
    const inf = p.troops.infantry;
    const lan = p.troops.lancers;
    const mrk = p.troops.marksman;
    const isChecked = window.warRoomAttendance ? window.warRoomAttendance.has(p.id) : false;

    const renderTroopPill = (t) => {
      if (t.level === null) return '<span class="text-muted">-</span>';
      const isHelios = t.helios;
      const qtyStr = isHelios && t.helios_quantity !== null ? ` (${formatNumber(t.helios_quantity)})` : '';
      return `<span class="pill-level ${isHelios ? 'helios' : ''}">${isHelios ? '🔥 ' : ''}${formatFcLevel(t.level)}${qtyStr}</span>`;
    };

    const statusBadge = p.is_complete
      ? '<span class="status-badge complete">Complete</span>'
      : '<span class="status-badge incomplete">Incomplete</span>';

    const tagBadge = p.alliance_tag ? `<span class="user-badge" style="margin-left: 4px; font-weight: 700;">${escapeHtml(p.alliance_tag)}</span>` : '';

    return `
      <tr data-id="${p.id}">
        <td style="text-align: center;">
          <input type="checkbox" class="roster-check" data-id="${p.id}" ${isChecked ? 'checked' : ''} style="width: 18px; height: 18px; cursor: pointer;">
        </td>
        <td>
          <div class="player-identity">
            <span class="player-main-name">${escapeHtml(p.name)} ${tagBadge}</span>
            <span class="player-sub-id">${escapeHtml(p.discord_user_id)}</span>
          </div>
        </td>
        <td><code>${escapeHtml(p.game_player_id)}</code></td>
        <td><strong>${formatNumber(p.march_limit)}</strong></td>
        <td>${renderTroopPill(inf)}</td>
        <td>${renderTroopPill(lan)}</td>
        <td>${renderTroopPill(mrk)}</td>
        <td>${statusBadge}</td>
        <td>
          <div class="table-actions">
            <button class="btn-icon" title="Edit Player" onclick="editPlayer(${p.id})">✏️</button>
            <button class="btn-icon delete" title="Delete Player" onclick="openDeleteModal(${p.id}, '${escapeHtml(p.name)}')">🗑️</button>
          </div>
        </td>
      </tr>
    `;
  }).join('');

  // Attach attendance listeners
  tbody.querySelectorAll('.roster-check').forEach(cb => {
    cb.addEventListener('change', async (e) => {
      const pid = parseInt(e.target.dataset.id, 10);
      const online = e.target.checked;
      try {
        const res = await fetchApi('/api/attendance/check-in', {
          method: 'POST',
          body: JSON.stringify({ player_ids: [pid], is_online: online })
        });
        const countEl = document.getElementById('war-online-count');
        if (countEl) countEl.textContent = res.total_online;
        if (!window.warRoomAttendance) window.warRoomAttendance = new Set();
        if (online) window.warRoomAttendance.add(pid); else window.warRoomAttendance.delete(pid);
      } catch (err) {
        showToast(err.message, 'error');
        e.target.checked = !online; // revert
      }
    });
  });
}


function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/[&<>"']/g, (m) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[m]));
}

// Add/Edit Player Modal
function openAddPlayerModal() {
  state.editingPlayerId = null;
  state.formHeroes = [];
  elements.playerModalTitle.textContent = 'Add Player to Roster';
  elements.playerForm.reset();
  elements.formPlayerId.value = '';
  elements.formInfLevel.value = 5;
  elements.formLanLevel.value = 5;
  elements.formMrkLevel.value = 5;
  renderHeroesGrid();
  elements.playerModal.classList.add('active');
}

window.editPlayer = async function (id) {
  try {
    const player = await fetchApi(`/api/players/${id}`);
    state.editingPlayerId = id;
    elements.playerModalTitle.textContent = `Edit Player: ${player.name}`;
    elements.formPlayerId.value = player.id;
    elements.formName.value = player.name;
    elements.formGameId.value = player.game_player_id;
    elements.formMarchLimit.value = player.march_limit;
    if (elements.formAllianceTag) elements.formAllianceTag.value = player.alliance_tag || '';
    elements.formDiscordId.value = player.discord_user_id;


    // Infantry
    elements.formInfHelios.checked = player.troops.infantry.helios;
    elements.formInfLevel.value = player.troops.infantry.level || 5;
    elements.formInfQty.value = player.troops.infantry.helios_quantity || '';

    // Lancers
    elements.formLanHelios.checked = player.troops.lancers.helios;
    elements.formLanLevel.value = player.troops.lancers.level || 5;
    elements.formLanQty.value = player.troops.lancers.helios_quantity || '';

    // Marksman
    elements.formMrkHelios.checked = player.troops.marksman.helios;
    elements.formMrkLevel.value = player.troops.marksman.level || 5;
    elements.formMrkQty.value = player.troops.marksman.helios_quantity || '';

    // Heroes
    state.formHeroes = (player.heroes || []).map(h => ({
      name: h.name,
      stars: h.stars || 1,
      skill_level: h.skill_level || 1,
    }));
    renderHeroesGrid();

    elements.playerModal.classList.add('active');
  } catch (err) {
    showToast(`Failed to load player: ${err.message}`, 'error');
  }
};

function closePlayerModal() {
  elements.playerModal.classList.remove('active');
  state.formHeroes = [];
}

// ============================================================
// Hero Form Management
// ============================================================

function renderHeroesGrid() {
  const grid = elements.heroesGrid;
  if (!grid) return;
  if (state.formHeroes.length === 0) {
    grid.innerHTML = '<div class="joiner-empty">No heroes tracked yet. Add one below.</div>';
    return;
  }
  grid.innerHTML = state.formHeroes.map((h, i) => `
    <div class="hero-card" data-index="${i}">
      <button type="button" class="hero-card-remove" onclick="removeHero(${i})" title="Remove">✕</button>
      <div class="hero-card-name">${escapeHtml(h.name)}</div>
      <div class="hero-card-fields">
        <div class="hero-card-field">
          <label>Stars ★</label>
          <input type="number" class="form-input" min="1" max="5" value="${h.stars}"
            oninput="updateHeroField(${i}, 'stars', this.value)">
        </div>
        <div class="hero-card-field">
          <label>Exp. Skill</label>
          <input type="number" class="form-input" min="1" max="5" value="${h.skill_level}"
            oninput="updateHeroField(${i}, 'skill_level', this.value)">
        </div>
      </div>
    </div>
  `).join('');
}

window.removeHero = function (index) {
  state.formHeroes.splice(index, 1);
  renderHeroesGrid();
};

window.updateHeroField = function (index, field, value) {
  const num = Math.max(1, Math.min(5, parseInt(value, 10) || 1));
  state.formHeroes[index][field] = num;
};

// Delete Player Modal
window.openDeleteModal = function (id, name) {
  state.deletingPlayerId = id;
  elements.deletePlayerName.textContent = name;
  elements.deleteModal.classList.add('active');
};

function closeDeleteModal() {
  elements.deleteModal.classList.remove('active');
  state.deletingPlayerId = null;
}

// Simulator Ratio Sync
function updateRatioBadge() {
  const sum = Number(state.sim.inf) + Number(state.sim.lan) + Number(state.sim.mrk);
  elements.ratioSumBadge.textContent = `Total: ${sum}%`;
  if (sum === 100) {
    elements.ratioSumBadge.className = 'ratio-sum-badge valid';
  } else {
    elements.ratioSumBadge.className = 'ratio-sum-badge invalid';
  }
}

function syncRatio(source, val) {
  val = Math.max(0, Math.min(100, Number(val) || 0));
  if (source === 'inf') {
    state.sim.inf = val;
    elements.sliderInf.value = val;
    elements.numInf.value = val;
  } else if (source === 'lan') {
    state.sim.lan = val;
    elements.sliderLan.value = val;
    elements.numLan.value = val;
  } else if (source === 'mrk') {
    state.sim.mrk = val;
    elements.sliderMrk.value = val;
    elements.numMrk.value = val;
  }
  updateRatioBadge();
}

function getCaptainPayloadData() {
  const formationType = state.sim.formation_type || 'rally';
  const rallyCountEl = document.getElementById('sim-rally-count');
  const count = formationType === 'garrison' ? 1 : parseInt(rallyCountEl?.value || '1', 10);

  if (count === 1) {
    const capIdVal = document.getElementById('sim-captain-select-1')?.value;
    const infHero = document.getElementById('sim-captain-hero-inf-1')?.value || '';
    const lanHero = document.getElementById('sim-captain-hero-lan-1')?.value || '';
    const mrkHero = document.getElementById('sim-captain-hero-mrk-1')?.value || '';

    return {
      captain_id: capIdVal ? parseInt(capIdVal, 10) : null,
      captain_heroes: [infHero, lanHero, mrkHero].filter(Boolean),
    };
  } else {
    const captainsList = [];
    for (let i = 1; i <= count; i++) {
      const capIdVal = document.getElementById(`sim-captain-select-${i}`)?.value;
      const infHero = document.getElementById(`sim-captain-hero-inf-${i}`)?.value || '';
      const lanHero = document.getElementById(`sim-captain-hero-lan-${i}`)?.value || '';
      const mrkHero = document.getElementById(`sim-captain-hero-mrk-${i}`)?.value || '';

      captainsList.push({
        captain_id: capIdVal ? parseInt(capIdVal, 10) : null,
        captain_heroes: [infHero, lanHero, mrkHero].filter(Boolean),
      });
    }

    return {
      rally_captains: captainsList,
    };
  }
}

async function runSimulation() {
  const formationType = state.sim.formation_type || 'rally';
  const captainData = getCaptainPayloadData();

  if (formationType === 'rally') {
    const rallyCount = parseInt(document.getElementById('sim-rally-count').value, 10);
    const generation = parseInt(document.getElementById('sim-gen-select').value, 10);
    const scope = document.getElementById('sim-scope-toggle')?.querySelector('.active')?.dataset.value || 'state';
    const allianceTag = elements.simAllianceSelect ? elements.simAllianceSelect.value : '';

    elements.btnRunSim.disabled = true;
    elements.btnRunSim.innerHTML = '<span>⏳</span> Calculating Multi-Rally...';

    try {
      const res = await fetchApi('/api/rallies/calculate', {
        method: 'POST',
        body: JSON.stringify({
          rally_count: rallyCount,
          generation: generation,
          event_scope: scope,
          alliance_tag: allianceTag,
          online_only: true,
          post_to_discord: false,
          rally_captains: captainData.rally_captains,
        }),
      });

      const wrap = document.getElementById('sim-params-wrap');
      if (wrap) wrap.className = 'sim-layout-split';
      const setupCard = document.querySelector('.setup-card');
      if (setupCard) setupCard.style.maxWidth = '100%';
      const colEl = document.getElementById('sim-results-column');
      if (colEl) colEl.style.display = 'block';

      renderMultiRallyInSim(res.rallies || []);
      showToast('Multi-Rally assignment complete!', 'success');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      elements.btnRunSim.disabled = false;
      elements.btnRunSim.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg><span id="btn-run-simulation-label">Calculate Multi-Rally</span>';
    }
    return;
  }

  // --- GARRISON / SINGLE-FORMATION CALCULATION ---
  const sum = Number(state.sim.inf) + Number(state.sim.lan) + Number(state.sim.mrk);
  if (sum !== 100) {
    showToast(`Ratio must sum to exactly 100% (currently ${sum}%)`, 'error');
    return;
  }

  const capacity = Number(elements.simCapacityInput.value);
  if (!capacity || capacity <= 0) {
    showToast('Capacity must be greater than 0', 'error');
    return;
  }

  elements.btnRunSim.disabled = true;
  elements.btnRunSim.innerHTML = '<span>⏳</span> Calculating...';

  try {
    const payload = {
      mode: state.sim.mode,
      formation_type: state.sim.formation_type,
      capacity: capacity,
      alliance_tag: elements.simAllianceSelect ? elements.simAllianceSelect.value : '',
      ratio: { infantry: state.sim.inf, lancers: state.sim.lan, marksman: state.sim.mrk },
      captain_id: captainData.captain_id,
      captain_heroes: captainData.captain_heroes,
      target_joiners: getSelectedHeroJoiners(),
    };

    const result = await fetchApi('/api/calculate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    state.sim.result = result;
    const wrap = document.getElementById('sim-params-wrap');
    if (wrap) wrap.className = 'sim-layout-split';
    const setupCard = document.querySelector('.setup-card');
    if (setupCard) setupCard.style.maxWidth = '100%';
    const colEl = document.getElementById('sim-results-column');
    if (colEl) colEl.style.display = 'block';
    const rallyResultsEl = document.getElementById('sim-rally-results');
    if (rallyResultsEl) rallyResultsEl.innerHTML = '';
    const simResultsPanel = document.getElementById('sim-results-card');
    if (simResultsPanel) simResultsPanel.style.display = 'block';

    renderSimResult();
    showToast('Garrison calculation complete!', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    elements.btnRunSim.disabled = false;
    elements.btnRunSim.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg><span id="btn-run-simulation-label">Run Garrison Calculation</span>';
  }
}

function renderMultiRallyInSim(rallies) {
  if (elements.simPlaceholder) elements.simPlaceholder.classList.add('hidden');
  if (elements.simContent) elements.simContent.classList.add('hidden');
  const simResultsPanel = document.getElementById('sim-results-card');
  if (simResultsPanel) simResultsPanel.style.display = 'none';

  const container = document.getElementById('sim-rally-results');
  if (!container) return;
  container.innerHTML = '';

  if (!rallies || rallies.length === 0) {
    container.innerHTML = '<div class="glass-card"><p style="color:var(--text-muted);">No online players available to form rallies. Make sure players are checked in from the Roster tab.</p></div>';
    return;
  }

  rallies.forEach(rally => {
    const card = document.createElement('div');
    card.className = 'glass-card';
    card.style.borderTop = `3px solid ${rally.role === 'main_strike' ? 'var(--color-amber)' : rally.role === 'garrison_defense' ? 'var(--color-cyan)' : 'var(--color-rose)'}`;
    card.style.marginBottom = '20px';

    const p1 = rally.players?.[0];
    const recCaptain = p1?.recommended_captain || '-';
    const joiners = p1?.recommended_joiners || [];
    const avgFcLabel = rally.avg_fc_level != null ? `<span style="background:rgba(0,242,254,0.12);border:1px solid var(--color-cyan);border-radius:6px;padding:2px 8px;font-size:12px;color:var(--color-cyan);font-weight:700;">Avg FC: ${formatFcLevel(rally.avg_fc_level, 3)}</span>` : '';

    let totalInf = 0, totalLan = 0, totalMrk = 0;
    (rally.players || []).forEach(p => {
      totalInf += (p.infantry_count || 0);
      totalLan += (p.lancer_count || 0);
      totalMrk += (p.marksman_count || 0);
    });
    const totalAssigned = totalInf + totalLan + totalMrk;

    const actualInfPct = totalAssigned > 0 ? Math.round((totalInf / totalAssigned) * 100) : 0;
    const actualLanPct = totalAssigned > 0 ? Math.round((totalLan / totalAssigned) * 100) : 0;
    const actualMrkPct = totalAssigned > 0 ? Math.round((totalMrk / totalAssigned) * 100) : 0;

    const targetInfPct = rally.ratio?.infantry || 0;
    const targetLanPct = rally.ratio?.lancer || 0;
    const targetMrkPct = rally.ratio?.marksman || 0;

    card.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:12px;flex-wrap:wrap;">
        <div style="display:flex;align-items:center;gap:10px;">
          <h3 style="margin:0;font-size:18px;">${rally.label}</h3>
          ${avgFcLabel}
        </div>
        <span style="background:rgba(255,255,255,0.06);border:1px solid var(--border-color);border-radius:6px;padding:3px 10px;font-size:12px;color:var(--color-amber);font-weight:600;">Status: EXACT | Players: ${rally.players.length}</span>
      </div>

      <!-- Metrics Grid -->
      <div class="metrics-grid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-bottom:16px;">
        <div class="metric-card">
          <div class="metric-val" style="color:var(--color-cyan);">100%</div>
          <div class="metric-lbl">Capacity Filled</div>
        </div>
        <div class="metric-card">
          <div class="metric-val">${formatNumber(totalAssigned)}</div>
          <div class="metric-lbl">Total Assigned</div>
        </div>
        <div class="metric-card">
          <div class="metric-val">${rally.players.length}</div>
          <div class="metric-lbl">Players Deployed</div>
        </div>
      </div>

      <!-- Target vs Actual Breakdown -->
      <div style="margin-bottom:16px;background:rgba(0,0,0,0.15);padding:12px;border-radius:8px;border:1px solid var(--border-color);">
        <div style="font-size:12px;font-weight:700;color:var(--text-secondary);margin-bottom:8px;">Target vs Actual Troop Breakdown</div>
        <div class="troop-bar-group" style="margin-bottom:6px;">
          <div class="troop-bar-header" style="font-size:11px;">
            <span>Infantry (Actual: ${formatNumber(totalInf)} / ${targetInfPct}%)</span>
            <span>${actualInfPct}% actual</span>
          </div>
          <div class="progress-track" style="height:6px;"><div class="progress-fill inf" style="width:${actualInfPct}%"></div></div>
        </div>
        <div class="troop-bar-group" style="margin-bottom:6px;">
          <div class="troop-bar-header" style="font-size:11px;">
            <span>Lancers (Actual: ${formatNumber(totalLan)} / ${targetLanPct}%)</span>
            <span>${actualLanPct}% actual</span>
          </div>
          <div class="progress-track" style="height:6px;"><div class="progress-fill lan" style="width:${actualLanPct}%"></div></div>
        </div>
        <div class="troop-bar-group">
          <div class="troop-bar-header" style="font-size:11px;">
            <span>Marksman (Actual: ${formatNumber(totalMrk)} / ${targetMrkPct}%)</span>
            <span>${actualMrkPct}% actual</span>
          </div>
          <div class="progress-track" style="height:6px;"><div class="progress-fill mrk" style="width:${actualMrkPct}%"></div></div>
        </div>
      </div>

      <!-- Top 4 Joiners (Hero Optimization) -->
      ${joiners.length > 0 ? `
      <div style="margin-bottom:16px;background:rgba(255,255,255,0.02);padding:12px;border-radius:8px;border:1px solid var(--border-color);">
        <div style="font-size:12px;font-weight:700;color:var(--color-amber);margin-bottom:8px;">⭐ Recommended Joiner Heroes (Skill Buffs)</div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;">
          ${joiners.slice(0,4).map((jHero, idx) => {
            const playerRec = rally.players[idx + 1];
            const pName = playerRec ? playerRec.player_name : 'Joiner';
            return `
              <div style="background:rgba(0,0,0,0.2);padding:8px;border-radius:6px;border:1px solid rgba(255,255,255,0.05);">
                <div style="font-size:10px;color:var(--color-cyan);font-weight:700;">Slot ${idx+1} Joiner</div>
                <div style="font-size:12px;font-weight:700;">${escapeHtml(pName)}</div>
                <div style="font-size:11px;color:var(--color-amber);">${escapeHtml(jHero)}</div>
              </div>`;
          }).join('')}
        </div>
      </div>` : ''}

      <!-- Player Assignments Table -->
      <div class="table-responsive">
        <table class="data-table">
          <thead><tr><th>Player</th><th>Infantry</th><th>Lancers</th><th>Marksman</th><th>Total March</th><th>Notes</th></tr></thead>
          <tbody>
            ${(rally.players || []).map((p, idx) => {
              let roleBadge = '';
              let heroNote = '';
              if (idx === 0) {
                roleBadge = `<span style="background:rgba(255,180,0,0.18); border:1px solid var(--color-amber); color:var(--color-amber); border-radius:4px; padding:2px 6px; font-size:11px; font-weight:700; margin-right:6px;">👑 Captain</span>`;
              } else if (idx <= 4) {
                roleBadge = `<span style="background:rgba(0,242,254,0.12); border:1px solid var(--color-cyan); color:var(--color-cyan); border-radius:4px; padding:2px 6px; font-size:11px; font-weight:600; margin-right:6px;">Slot ${idx} Joiner</span>`;
                const firstHero = p.recommended_joiners ? (p.recommended_joiners[idx - 1] || p.recommended_joiners[0]) : '';
                if (firstHero) heroNote = `<span style="font-size:11px; color:var(--color-cyan); font-weight:600;">[Hero 1: ${escapeHtml(firstHero)}]</span> `;
              } else {
                roleBadge = `<span style="background:rgba(255,255,255,0.05); color:var(--text-muted); border-radius:4px; padding:2px 6px; font-size:11px; margin-right:6px;">Joiner</span>`;
              }
              return `
                <tr>
                  <td>${roleBadge}<strong>${escapeHtml(p.player_name)}</strong> ${heroNote}</td>
                  <td style="color:var(--troop-inf); font-weight:600;">${p.infantry_count.toLocaleString()}</td>
                  <td style="color:var(--troop-lan); font-weight:600;">${p.lancer_count.toLocaleString()}</td>
                  <td style="color:var(--troop-mrk); font-weight:600;">${p.marksman_count.toLocaleString()}</td>
                  <td><strong>${p.march_limit.toLocaleString()}</strong></td>
                  <td>${p.tactical_note ? `<span style="color:var(--color-amber);font-size:12px;">${p.tactical_note}</span>` : ''}</td>
                </tr>`;
            }).join('')}
          </tbody>
        </table>
      </div>`;
    container.appendChild(card);
  });
}

function initSimTypeToggle() {
  const typeToggle = document.getElementById('sim-type-toggle');
  const modeToggle = document.getElementById('sim-mode-toggle');
  const rallyCountGroup = document.getElementById('sim-rally-count-group');
  const btnLabel = document.getElementById('btn-run-simulation-label');
  const simResultsPanel = document.getElementById('sim-results-card');
  const rallyResultsEl = document.getElementById('sim-rally-results');
  const scopeToggle = document.getElementById('sim-scope-toggle');

  // Wire scope toggle (state/alliance)
  if (scopeToggle) {
    scopeToggle.querySelectorAll('.segment-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        scopeToggle.querySelectorAll('.segment-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
      });
    });
  }

  function updateForType(type) {
    state.sim.formation_type = type;
    // Reset layout to full-width when switching type
    const wrap = document.getElementById('sim-params-wrap');
    if (wrap) wrap.className = 'sim-layout-full';
    const setupCard = document.querySelector('.setup-card');
    if (setupCard) setupCard.style.maxWidth = '860px';
    const colEl = document.getElementById('sim-results-column');
    if (colEl) colEl.style.display = 'none';

    if (type === 'rally') {
      if (rallyCountGroup) rallyCountGroup.style.display = 'block';
      if (btnLabel) btnLabel.textContent = 'Calculate Multi-Rally';
      if (simResultsPanel) simResultsPanel.style.display = 'none';
      if (rallyResultsEl) { rallyResultsEl.innerHTML = ''; }
      // Rally can be attack or defence — unlock mode
      if (modeToggle) modeToggle.querySelectorAll('.segment-btn').forEach(b => { b.disabled = false; b.style.opacity = '1'; });
    } else {
      // Garrison = defence only
      if (rallyCountGroup) rallyCountGroup.style.display = 'none';
      if (btnLabel) btnLabel.textContent = 'Run Garrison Calculation';
      if (simResultsPanel) simResultsPanel.style.display = 'none';
      if (rallyResultsEl) { rallyResultsEl.innerHTML = ''; }
      // Lock mode to defence
      if (modeToggle) {
        modeToggle.querySelectorAll('.segment-btn').forEach(b => {
          b.classList.toggle('active', b.dataset.value === 'defence');
          b.disabled = true;
          b.style.opacity = b.dataset.value === 'defence' ? '1' : '0.4';
        });
        state.sim.mode = 'defence';
      }
    }
    // Update online count badge
    const onlineCountEl = document.getElementById('sim-online-count');
    if (onlineCountEl && window.warRoomAttendance) {
      const count = window.warRoomAttendance.size;
      onlineCountEl.textContent = count > 0 ? ` (${count} online checked in)` : ' (0 checked in — go to Roster tab)';

    }
  }

  if (typeToggle) {
    typeToggle.querySelectorAll('.segment-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        typeToggle.querySelectorAll('.segment-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        updateForType(btn.dataset.value);
        renderCaptainSelectionBlocks();
      });
    });
  }
  // default: rally is active
  updateForType('rally');
  renderCaptainSelectionBlocks();
}

function renderSimResult() {
  const res = state.sim.result;
  if (!res) return;

  elements.simPlaceholder.classList.add('hidden');
  elements.simContent.classList.remove('hidden');

  elements.simResultTitle.textContent = `${res.mode.toUpperCase()} ${res.formation_type.toUpperCase()}`;
  elements.simResultMeta.textContent = `Status: ${res.status.toUpperCase()} | Players: ${res.players_count}`;
  elements.simFillPct.textContent = `${res.fill_percentage}%`;
  elements.simTotalAssigned.textContent = formatNumber(res.total_assigned);
  elements.simTargetCapacity.textContent = formatNumber(res.target_capacity || res.capacity);
  elements.simPlayersCount.textContent = formatNumber(res.players_count);

  // Garrison Gap Card
  const garrisonCard = document.getElementById('sim-garrison-gap-card');
  if (garrisonCard) {
    if (res.formation_type === 'garrison') {
      garrisonCard.classList.remove('hidden');
      const baseEl = document.getElementById('sim-garrison-base');
      const targetEl = document.getElementById('sim-garrison-target');
      const gapEl = document.getElementById('sim-garrison-gap');
      if (baseEl) baseEl.textContent = formatNumber(res.base_capacity || res.capacity);
      if (targetEl) targetEl.textContent = formatNumber(res.target_capacity || res.capacity);
      if (gapEl) gapEl.textContent = `+${formatNumber(res.garrison_gap || 0)} troops needed`;
    } else {
      garrisonCard.classList.add('hidden');
    }
  }

  // Comparison Bars
  const troopMeta = [
    { key: 'infantry', name: 'Infantry', class: 'inf' },
    { key: 'lancers', name: 'Lancers', class: 'lan' },
    { key: 'marksman', name: 'Marksman', class: 'mrk' },
  ];

  elements.simComparisonBars.innerHTML = troopMeta.map((t) => {
    const target = res.targets[t.key] || 0;
    const actual = res.actuals[t.key] || 0;
    const pct = target > 0 ? Math.min(100, Math.round((actual / target) * 100)) : 100;
    return `
      <div class="troop-bar-group">
        <div class="troop-bar-header">
          <span class="troop-name">${t.name} (Actual: ${formatNumber(actual)} / Target: ${formatNumber(target)})</span>
          <span class="troop-stat">${res.actual_ratios[t.key]}% actual</span>
        </div>
        <div class="progress-track">
          <div class="progress-fill ${t.class}" style="width: ${pct}%"></div>
        </div>
      </div>
    `;
  }).join('');

  // Assignments — group allocations by player, one row per player
  if (!res.allocations || res.allocations.length === 0) {
    elements.simAssignmentsTbody.innerHTML = '<tr><td colspan="5" class="empty-cell">No players allocated (ensure players have complete registrations).</td></tr>';
  } else {
    // Group by player_name
    const byPlayer = {};
    res.allocations.forEach(a => {
      if (!byPlayer[a.player_name]) byPlayer[a.player_name] = { infantry: 0, lancers: 0, marksman: 0, total: 0, player_id: a.player_id };
      const key = a.troop_type.toLowerCase();
      byPlayer[a.player_name][key] = (byPlayer[a.player_name][key] || 0) + a.amount;
      byPlayer[a.player_name].total += a.amount;
    });

    const joinerRecs = res.joiner_recommendations || [];

    const playerEntries = Object.entries(byPlayer);
    if (res.captain_id) {
      playerEntries.sort(([nameA, a], [nameB, b]) => {
        if (a.player_id === res.captain_id) return -1;
        if (b.player_id === res.captain_id) return 1;
        return 0;
      });
    }

    const rows = playerEntries.map(([name, t], idx) => {
      let roleBadge = '';
      let heroInfo = '';

      const isCaptain = res.captain_id ? (t.player_id === res.captain_id) : (idx === 0);

      if (isCaptain) {
        roleBadge = `<span style="background:rgba(255,180,0,0.18); border:1px solid var(--color-amber); color:var(--color-amber); border-radius:4px; padding:2px 6px; font-size:11px; font-weight:700; margin-right:6px;">👑 Captain</span>`;
        if (res.captain_hero_buffs && res.captain_hero_buffs.length > 0) {
          const capBuffs = res.captain_hero_buffs.map(b => `<strong>${escapeHtml(b.hero)}</strong> (${escapeHtml(b.buff)})`).join(' • ');
          heroInfo = `<div style="font-size:11px; color:var(--text-secondary); margin-top:3px;">Heroes: ${capBuffs}</div>`;
        }
      } else {
        const joinerIndex = isCaptain ? idx - 1 : idx;
        if (joinerIndex >= 0 && joinerIndex < 4) {
          const joinerRec = joinerRecs[joinerIndex];
          const heroName = joinerRec ? joinerRec.hero_name : (state.sim.heroes[joinerIndex] || '');
          const buffDesc = joinerRec ? joinerRec.buff_description : '';

          roleBadge = `<span style="background:rgba(0,242,254,0.12); border:1px solid var(--color-cyan); color:var(--color-cyan); border-radius:4px; padding:2px 6px; font-size:11px; font-weight:600; margin-right:6px;">Slot ${joinerIndex + 1} Joiner</span>`;
          if (heroName) {
            heroInfo = `<div style="font-size:11px; color:var(--text-secondary); margin-top:3px;">1st Hero: <strong>${escapeHtml(heroName)}</strong> ${buffDesc ? `<span style="color:var(--color-cyan);">(${escapeHtml(buffDesc)})</span>` : ''}</div>`;
          }
        } else {
          roleBadge = `<span style="background:rgba(255,255,255,0.05); color:var(--text-muted); border-radius:4px; padding:2px 6px; font-size:11px; margin-right:6px;">Joiner</span>`;
        }
      }

      return `
        <tr>
          <td>
            <div style="display:flex; align-items:center; flex-wrap:wrap;">
              ${roleBadge}<strong>${escapeHtml(name)}</strong>
            </div>
            ${heroInfo}
          </td>
          <td style="color:var(--troop-inf); font-weight:600;">${formatNumber(t.infantry)}</td>
          <td style="color:var(--troop-lan); font-weight:600;">${formatNumber(t.lancers)}</td>
          <td style="color:var(--troop-mrk); font-weight:600;">${formatNumber(t.marksman)}</td>
          <td><strong>${formatNumber(t.total)}</strong></td>
        </tr>`;
    }).join('');

    elements.simAssignmentsTbody.innerHTML = rows;
  }

  // Top 4 Joiners
  const joinersCard = elements.simJoinersCard;
  const joinersList = elements.simJoinersList;
  const joiners = res.joiner_recommendations || [];
  if (joinersCard && joinersList) {
    if (joiners.length > 0) {
      joinersCard.classList.remove('hidden');
      joinersList.innerHTML = joiners.map(j => `
        <div class="joiner-slot">
          <div class="joiner-slot-number">Slot ${j.slot}</div>
          <div class="joiner-slot-player">${escapeHtml(j.player_name)}</div>
          <div class="joiner-slot-hero">${escapeHtml(j.hero_name)}</div>
          <div class="joiner-slot-stats">
            <span class="joiner-star-badge">${'★'.repeat(j.stars)}${'☆'.repeat(5 - j.stars)}</span>
            <span class="joiner-skill-badge">Skill ${j.skill_level}</span>
          </div>
          <div class="joiner-slot-buff">${escapeHtml(j.buff_description)}</div>
        </div>
      `).join('');
    } else {
      // No hero data in roster — show subtle empty state instead of hiding
      joinersCard.classList.remove('hidden');
      joinersList.innerHTML = '<div class="joiner-empty">No hero data found. Add hero levels to players in the Roster tab to see joiner recommendations.</div>';
    }
  }
}

// Rules Configuration
async function loadRules() {
  try {
    const rules = await fetchApi('/api/rules');
    if (rules.attack_importance) {
      elements.ruleAttackOrder.value = rules.attack_importance.join(', ');
    }
    if (rules.defence_importance) {
      elements.ruleDefenceOrder.value = rules.defence_importance.join(', ');
    }
    if (rules.helios_bonus !== undefined) {
      elements.ruleHeliosBonus.value = rules.helios_bonus;
    }
    if (rules.fc_weight !== undefined) {
      elements.ruleFcWeight.value = rules.fc_weight;
    }
  } catch (err) {
    showToast(`Failed to load rules: ${err.message}`, 'error');
  }
}

// ============================================================
// Target Hero Slots & Presets (Simulator)
// ============================================================

async function loadHeroes() {
  try {
    const res = await fetch('/api/heroes').then(r => r.json());
    state.heroCatalog = res.heroes || [];
    state.heroPresets = res.presets || [];
    populateHeroSlotDropdowns();
    populateCaptainHeroDropdowns();
  } catch (err) {
    console.error('Failed to load heroes:', err);
  }
}

function populateCaptainHeroDropdowns() {
  const slotSelects = [
    elements.simCaptainHero1,
    elements.simCaptainHero2,
    elements.simCaptainHero3,
  ];

  if (!slotSelects[0]) return;

  const defaultHeroes = ['Jeronimo', 'Molly', 'Bahiti'];

  slotSelects.forEach((sel, idx) => {
    if (!sel) return;
    const cur = sel.value || defaultHeroes[idx];
    sel.innerHTML = '';

    if (state.heroCatalog && state.heroCatalog.length > 0) {
      state.heroCatalog.forEach(h => {
        const opt = document.createElement('option');
        opt.value = h.name;
        opt.textContent = `${h.name} (${h.buff})`;
        sel.appendChild(opt);
      });
    } else {
      ['Jeronimo', 'Molly', 'Bahiti', 'Flint', 'Alonso', 'Mia', 'Philly', 'Lynn', 'Norah', 'Wayne', 'Wu Ming', 'Gatot', 'Hendrik', 'Xura', 'Edith', 'Jessie', 'Jasser', 'Seoyoon', 'Sergey', 'Patrick', 'Ahmose'].forEach(name => {
        const opt = document.createElement('option');
        opt.value = name;
        opt.textContent = name;
        sel.appendChild(opt);
      });
    }

    sel.value = cur;
    if (!sel.value && sel.options.length > 0) sel.selectedIndex = 0;
    sel.onchange = () => updateCaptainHeroBuffNotes();
  });

  updateCaptainHeroBuffNotes();
}

function updateCaptainHeroBuffNotes() {
  const slotSelects = [
    elements.simCaptainHero1,
    elements.simCaptainHero2,
    elements.simCaptainHero3,
  ];
  const buffLabels = [
    elements.simCaptainBuff1,
    elements.simCaptainBuff2,
    elements.simCaptainBuff3,
  ];

  slotSelects.forEach((sel, i) => {
    if (!sel || !buffLabels[i]) return;
    const heroName = sel.value;
    const heroObj = state.heroCatalog ? state.heroCatalog.find(h => h.name.toLowerCase() === (heroName || '').toLowerCase()) : null;
    const buff = heroObj ? heroObj.buff : 'Expedition Skill Buff';
    buffLabels[i].textContent = buff;
  });
}

function getSelectedCaptainHeroes() {
  return [
    elements.simCaptainHero1?.value || '',
    elements.simCaptainHero2?.value || '',
    elements.simCaptainHero3?.value || '',
  ].filter(Boolean);
}

function populateHeroSlotDropdowns(maxGen) {
  const slotSelects = [
    elements.simHeroSlot1,
    elements.simHeroSlot2,
    elements.simHeroSlot3,
    elements.simHeroSlot4,
  ];

  if (!slotSelects[0]) return;

  // Determine numeric cap. 'Extreme' / null / undefined => show all (99)
  const genCap = (maxGen === null || maxGen === undefined)
    ? 99
    : (isNaN(Number(maxGen)) ? 99 : Number(maxGen));

  const groups = {
    attack: { label: '⚔️ Attack Buffers', items: [] },
    defence: { label: '🛡️ Defense Buffers', items: [] },
    caller: { label: '👑 Callers & Utilities', items: [] },
    custom: { label: '⭐ Roster Heroes', items: [] },
  };

  state.heroCatalog.forEach(h => {
    // Filter by generation if gen_introduced is set
    const heroGen = h.gen_introduced !== undefined ? Number(h.gen_introduced) : 1;
    if (heroGen > genCap) return; // skip heroes above this generation
    const r = h.role || 'custom';
    if (groups[r]) {
      groups[r].items.push(h);
    } else {
      groups.custom.items.push(h);
    }
  });

  slotSelects.forEach((sel, slotIdx) => {
    if (!sel) return;
    const currentVal = sel.value; // remember current selection
    sel.innerHTML = '';
    Object.values(groups).forEach(grp => {
      if (grp.items.length === 0) return;
      const optGroup = document.createElement('optgroup');
      optGroup.label = grp.label;
      grp.items.forEach(h => {
        const opt = document.createElement('option');
        opt.value = h.name;
        opt.textContent = `${h.name} (${h.buff})`;
        opt.dataset.buff = h.buff;
        optGroup.appendChild(opt);
      });
      sel.appendChild(optGroup);
    });

    // Restore selection if still available, else pick first
    const heroToSet = state.sim.heroes[slotIdx] || currentVal || 'Jessie';
    sel.value = heroToSet;
    if (!sel.value && sel.options.length > 0) {
      sel.selectedIndex = 0;
    }
  });

  updateHeroBuffLabels();
}

function updateHeroBuffLabels() {
  const slotSelects = [
    elements.simHeroSlot1,
    elements.simHeroSlot2,
    elements.simHeroSlot3,
    elements.simHeroSlot4,
  ];
  const buffLabels = [
    elements.simHeroBuff1,
    elements.simHeroBuff2,
    elements.simHeroBuff3,
    elements.simHeroBuff4,
  ];

  slotSelects.forEach((sel, i) => {
    if (!sel || !buffLabels[i]) return;
    const heroName = sel.value;
    state.sim.heroes[i] = heroName;
    const heroObj = state.heroCatalog.find(h => h.name.toLowerCase() === heroName.toLowerCase());
    const buff = heroObj ? heroObj.buff : 'Expedition Skill Buff';
    buffLabels[i].textContent = buff;
  });
}

function setHeroJoinerSlots(heroesList) {
  if (!Array.isArray(heroesList)) return;
  const slotSelects = [
    elements.simHeroSlot1,
    elements.simHeroSlot2,
    elements.simHeroSlot3,
    elements.simHeroSlot4,
  ];
  heroesList.slice(0, 4).forEach((hName, i) => {
    if (slotSelects[i]) {
      let found = false;
      for (const opt of slotSelects[i].options) {
        if (opt.value.toLowerCase() === hName.toLowerCase()) {
          slotSelects[i].value = opt.value;
          found = true;
          break;
        }
      }
      if (!found) {
        const newOpt = document.createElement('option');
        newOpt.value = hName;
        newOpt.textContent = hName;
        slotSelects[i].appendChild(newOpt);
        slotSelects[i].value = hName;
      }
    }
  });
  updateHeroBuffLabels();
}

function getSelectedHeroJoiners() {
  const slotSelects = [
    elements.simHeroSlot1,
    elements.simHeroSlot2,
    elements.simHeroSlot3,
    elements.simHeroSlot4,
  ];
  return slotSelects.map((s, i) => (s && s.value) ? s.value : (state.sim.heroes[i] || 'Jessie'));
}

// Formation Presets
async function loadPresets() {
  try {
    const presets = await fetch('/api/presets').then(r => r.json());
    state.presets = presets;
    populateGenDropdown();
  } catch (err) {
    console.error('Failed to load presets:', err);
  }
}

function populateGenDropdown() {
  const genSel = elements.simGenSelect;
  if (!genSel) return;
  const seen = new Set();
  const gens = [];
  state.presets.forEach(p => {
    const g = String(p.generation);
    if (!seen.has(g)) { seen.add(g); gens.push(g); }
  });
  gens.forEach(g => {
    const opt = document.createElement('option');
    opt.value = g;
    opt.textContent = isNaN(Number(g)) ? g : `Generation ${g}`;
    genSel.appendChild(opt);
  });
}

function onGenChange() {
  const gen = elements.simGenSelect.value;

  if (!gen) {
    // No gen selected → show all heroes
    populateHeroSlotDropdowns();
    renderCaptainSelectionBlocks();
    return;
  }

  // Filter hero dropdowns to only show heroes available in this generation
  populateHeroSlotDropdowns(gen);
  renderCaptainSelectionBlocks();
}

function onPresetChange() {
  const gen = elements.simGenSelect.value;
  const idx = parseInt(elements.simPresetSelect.value, 10);
  if (!gen || isNaN(idx)) {
    elements.simPresetGuide.classList.add('hidden');
    return;
  }
  const matches = state.presets.filter(p => String(p.generation) === gen);
  const preset = matches[idx];
  if (preset) applyPreset(preset);
}

function applyPreset(preset) {
  // Fill ratio sliders
  syncRatio('inf', preset.ratio.infantry);
  syncRatio('lan', preset.ratio.lancers);
  syncRatio('mrk', preset.ratio.marksman);

  // Auto-fill hero slots from generation preset
  if (Array.isArray(preset.joiners) && preset.joiners.length >= 4) {
    setHeroJoinerSlots(preset.joiners.slice(0, 4));
    if (elements.btnHeroPresets) {
      elements.btnHeroPresets.forEach(b => b.classList.remove('active'));
    }
  }
}


async function saveRules() {
  const attackOrder = elements.ruleAttackOrder.value.split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
  const defenceOrder = elements.ruleDefenceOrder.value.split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
  const heliosBonus = parseFloat(elements.ruleHeliosBonus.value);
  const fcWeight = parseFloat(elements.ruleFcWeight.value);

  const payload = {
    attack_importance: attackOrder,
    defence_importance: defenceOrder,
    helios_bonus: heliosBonus,
    fc_weight: fcWeight,
  };

  try {
    await fetchApi('/api/rules', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
    showToast('Optimizer rules successfully updated!', 'success');
  } catch (err) {
    showToast(`Failed to save rules: ${err.message}`, 'error');
  }
}

// Event Listeners Initialization
function initEventListeners() {
  // Tabs
  elements.navTabs.forEach((tab) => {
    tab.addEventListener('click', () => switchTab(tab.dataset.tab));
  });

  // Auth Button
  if (elements.btnAuthAction) {
    elements.btnAuthAction.addEventListener('click', async () => {
      if (state.user.authenticated) {
        await fetchApi('/api/auth/logout', { method: 'POST' });
        state.user = { authenticated: false, role: 'guest', name: null };
        renderAuth();
        showToast('Logged out successfully', 'info');
      } else {
        openAuthModal();
      }
    });
  }

  if (elements.authModal) {
    elements.authModal.addEventListener('click', (e) => {
      if (e.target === elements.authModal) closeAuthModal();
    });
  }

  if (elements.authCloseBtn) {
    elements.authCloseBtn.addEventListener('click', closeAuthModal);
  }
  if (elements.authForm) {
    elements.authForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const passkey = elements.authPasskeyInput ? elements.authPasskeyInput.value : '';
      try {
        const res = await fetchApi('/api/auth/login', {
          method: 'POST',
          body: JSON.stringify({ passkey }),
        });
        state.user = { authenticated: true, role: res.role, name: res.name };
        renderAuth();
        closeAuthModal();
        showToast(`Welcome back, ${res.name}!`, 'success');
        loadStats();
        loadPlayers();
      } catch (err) {
        showToast(err.message || 'Login failed', 'error');
      }
    });
  }

  if (elements.btnQuickCalculate) {
    elements.btnQuickCalculate.addEventListener('click', () => switchTab('simulator'));
  }
  if (elements.btnQuickAddPlayer) {
    elements.btnQuickAddPlayer.addEventListener('click', openAddPlayerModal);
  }
  if (elements.btnAddPlayer) {
    elements.btnAddPlayer.addEventListener('click', openAddPlayerModal);
  }

  // Survey Generator Modal
  if (elements.btnSurveyGenerator) {
    elements.btnSurveyGenerator.addEventListener('click', openSurveyModal);
  }
  if (elements.btnGuideSurvey) {
    elements.btnGuideSurvey.addEventListener('click', openSurveyModal);
  }
  if (elements.surveyModalClose) {
    elements.surveyModalClose.addEventListener('click', closeSurveyModal);
  }
  if (elements.surveyModalDone) {
    elements.surveyModalDone.addEventListener('click', closeSurveyModal);
  }
  if (elements.btnCopySurveyScript) {
    elements.btnCopySurveyScript.addEventListener('click', copySurveyScript);
  }

  // CSV Import
  if (elements.btnImportCsv && elements.csvFileInput) {
    elements.btnImportCsv.addEventListener('click', () => {
      elements.csvFileInput.click();
    });

    elements.csvFileInput.addEventListener('change', async () => {
      const file = elements.csvFileInput.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('file', file);

      showToast('Importing CSV roster...', 'info');
      try {
        const res = await fetch('/api/players/import', {
          method: 'POST',
          body: formData,
        });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.error || 'Failed to import CSV');
        }

        const msg = `Import complete: ${data.created} added, ${data.updated} updated${data.skipped > 0 ? `, ${data.skipped} skipped` : ''}`;
        showToast(msg, data.skipped > 0 ? 'warning' : 'success');
        if (data.errors && data.errors.length > 0) {
          console.warn('CSV Import notices:', data.errors);
        }
        loadStats();
        loadPlayers();
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        elements.csvFileInput.value = '';
      }
    });
  }

  // Search & Filter
  let searchDebounce;
  elements.rosterSearch.addEventListener('input', (e) => {
    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(() => {
      state.searchQuery = e.target.value;
      loadPlayers();
    }, 250);
  });

  elements.filterChips.forEach((chip) => {
    chip.addEventListener('click', () => {
      elements.filterChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      state.activeFilter = chip.dataset.filter;
      loadPlayers();
    });
  });

  // Alliance Tag Filter Listener
  if (elements.rosterAllianceSelect) {
    elements.rosterAllianceSelect.addEventListener('change', (e) => {
      state.activeAllianceTag = e.target.value;
      loadPlayers();
    });
  }

  // Player Form Submission
  elements.playerModalClose.addEventListener('click', closePlayerModal);
  elements.playerModalCancel.addEventListener('click', closePlayerModal);
  elements.playerForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Sync hero field values from DOM before reading state
    document.querySelectorAll('#heroes-grid .hero-card').forEach((card) => {
      const idx = parseInt(card.dataset.index, 10);
      if (!isNaN(idx) && state.formHeroes[idx]) {
        const inputs = card.querySelectorAll('input[type=number]');
        if (inputs[0]) state.formHeroes[idx].stars = Math.max(1, Math.min(5, parseInt(inputs[0].value, 10) || 1));
        if (inputs[1]) state.formHeroes[idx].skill_level = Math.max(1, Math.min(5, parseInt(inputs[1].value, 10) || 1));
      }
    });

    const payload = {
      name: elements.formName.value.trim(),
      game_player_id: elements.formGameId.value.trim(),
      march_limit: parseInt(elements.formMarchLimit.value, 10),
      alliance_tag: elements.formAllianceTag ? elements.formAllianceTag.value.trim() : null,
      discord_user_id: elements.formDiscordId.value.trim(),

      troops: {
        infantry: {
          helios: elements.formInfHelios.checked,
          level: parseInt(elements.formInfLevel.value, 10),
          helios_quantity: elements.formInfHelios.checked && elements.formInfQty.value ? parseInt(elements.formInfQty.value, 10) : null,
        },
        lancers: {
          helios: elements.formLanHelios.checked,
          level: parseInt(elements.formLanLevel.value, 10),
          helios_quantity: elements.formLanHelios.checked && elements.formLanQty.value ? parseInt(elements.formLanQty.value, 10) : null,
        },
        marksman: {
          helios: elements.formMrkHelios.checked,
          level: parseInt(elements.formMrkLevel.value, 10),
          helios_quantity: elements.formMrkHelios.checked && elements.formMrkQty.value ? parseInt(elements.formMrkQty.value, 10) : null,
        },
      },
      heroes: state.formHeroes.map(h => ({
        name: h.name,
        stars: h.stars,
        skill_level: h.skill_level,
      })),
    };

    try {
      if (state.editingPlayerId) {
        await fetchApi(`/api/players/${state.editingPlayerId}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        });
        showToast('Player updated successfully!', 'success');
      } else {
        await fetchApi('/api/players', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
        showToast('Player added to roster!', 'success');
      }
      closePlayerModal();
      loadPlayers();
      loadStats();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Hero add button
  if (elements.btnAddHero) {
    elements.btnAddHero.addEventListener('click', () => {
      const name = elements.heroAddName ? elements.heroAddName.value : '';
      if (!name) { showToast('Select a hero first', 'error'); return; }
      if (state.formHeroes.find(h => h.name === name)) {
        showToast(`${name} is already added`, 'error'); return;
      }
      state.formHeroes.push({ name, stars: 4, skill_level: 5 });
      renderHeroesGrid();
      if (elements.heroAddName) elements.heroAddName.value = '';
    });
  }

  // Delete Player
  elements.deleteModalClose.addEventListener('click', closeDeleteModal);
  elements.deleteModalCancel.addEventListener('click', closeDeleteModal);
  elements.deleteModalConfirm.addEventListener('click', async () => {
    if (!state.deletingPlayerId) return;
    try {
      await fetchApi(`/api/players/${state.deletingPlayerId}`, { method: 'DELETE' });
      showToast('Player deleted from roster', 'info');
      closeDeleteModal();
      loadPlayers();
      loadStats();
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Clear All Player Data
  if (elements.btnClearRoster) {
    elements.btnClearRoster.addEventListener('click', () => {
      // Show current server name in the modal
      const serverName = elements.serverSelect
        ? (elements.serverSelect.options[elements.serverSelect.selectedIndex]?.text || 'this server')
        : 'this server';
      if (elements.clearDataServerName) {
        elements.clearDataServerName.textContent = serverName;
      }
      if (elements.clearDataModal) {
        elements.clearDataModal.classList.add('active');
      }
    });
  }

  function closeClearDataModal() {
    if (elements.clearDataModal) elements.clearDataModal.classList.remove('active');
  }

  if (elements.clearDataModalClose) {
    elements.clearDataModalClose.addEventListener('click', closeClearDataModal);
  }
  if (elements.clearDataModalCancel) {
    elements.clearDataModalCancel.addEventListener('click', closeClearDataModal);
  }
  if (elements.clearDataModal) {
    elements.clearDataModal.addEventListener('click', (e) => {
      if (e.target === elements.clearDataModal) closeClearDataModal();
    });
  }
  if (elements.clearDataModalConfirm) {
    elements.clearDataModalConfirm.addEventListener('click', async () => {
      try {
        elements.clearDataModalConfirm.disabled = true;
        elements.clearDataModalConfirm.textContent = 'Wiping...';
        const data = await fetchApi('/api/players/clear', { method: 'DELETE' });
        showToast(`Cleared ${data.deleted_count ?? 'all'} player records from the roster.`, 'info');
        closeClearDataModal();
        loadPlayers();
        loadStats();
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        elements.clearDataModalConfirm.disabled = false;
        elements.clearDataModalConfirm.textContent = 'Yes, Wipe All Data';
      }
    });
  }

  // Simulator Sliders & Inputs
  elements.sliderInf.addEventListener('input', (e) => syncRatio('inf', e.target.value));
  elements.sliderLan.addEventListener('input', (e) => syncRatio('lan', e.target.value));
  elements.sliderMrk.addEventListener('input', (e) => syncRatio('mrk', e.target.value));
  elements.numInf.addEventListener('change', (e) => syncRatio('inf', e.target.value));
  elements.numLan.addEventListener('change', (e) => syncRatio('lan', e.target.value));
  elements.numMrk.addEventListener('change', (e) => syncRatio('mrk', e.target.value));

  // Simulator Presets
  document.querySelectorAll('.preset-pills .btn-preset[data-inf]').forEach((btn) => {
    btn.addEventListener('click', () => {
      syncRatio('inf', btn.dataset.inf);
      syncRatio('lan', btn.dataset.lan);
      syncRatio('mrk', btn.dataset.mrk);
    });
  });

  document.querySelectorAll('.preset-pills .btn-preset[data-capacity]').forEach((btn) => {
    btn.addEventListener('click', () => {
      elements.simCapacityInput.value = btn.dataset.capacity;
    });
  });

  // Mode & Formation Type Toggles
  elements.simModeBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      elements.simModeBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.sim.mode = btn.dataset.value;

      // When mode changes, auto-switch to corresponding preset if user was on standard default
      if (state.sim.mode === 'attack') {
        const activePreset = document.querySelector('.btn-hero-preset.active');
        if (!activePreset || activePreset.dataset.preset === 'fortress_defense') {
          const atkBtn = document.querySelector('.btn-hero-preset[data-preset="attack_all_out"]');
          if (atkBtn) atkBtn.click();
        }
      } else if (state.sim.mode === 'defence') {
        const activePreset = document.querySelector('.btn-hero-preset.active');
        if (!activePreset || activePreset.dataset.preset === 'attack_all_out') {
          const defBtn = document.querySelector('.btn-hero-preset[data-preset="fortress_defense"]');
          if (defBtn) defBtn.click();
        }
      }
    });
  });

  elements.simTypeBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      elements.simTypeBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.sim.formation_type = btn.dataset.value;
    });
  });

  // Hero Slot Select Change Listeners
  [elements.simHeroSlot1, elements.simHeroSlot2, elements.simHeroSlot3, elements.simHeroSlot4].forEach((sel) => {
    if (sel) {
      sel.addEventListener('change', () => {
        updateHeroBuffLabels();
        // Remove active class from preset buttons since user manually changed a slot
        elements.btnHeroPresets.forEach(b => b.classList.remove('active'));
      });
    }
  });

  // Hero Preset Buttons
  elements.btnHeroPresets.forEach(btn => {
    btn.addEventListener('click', () => {
      elements.btnHeroPresets.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const presetId = btn.dataset.preset;
      const preset = state.heroPresets.find(p => p.id === presetId);
      if (preset && preset.heroes) {
        setHeroJoinerSlots(preset.heroes);
      } else if (presetId === 'attack_all_out') {
        setHeroJoinerSlots(['Jessie', 'Jasser', 'Seoyoon', 'Norah']);
      } else if (presetId === 'fortress_defense') {
        setHeroJoinerSlots(['Patrick', 'Sergey', 'Ling Xue', 'Ahmose']);
      } else if (presetId === 'mixed_svs') {
        setHeroJoinerSlots(['Jessie', 'Seoyoon', 'Patrick', 'Sergey']);
      } else if (presetId === 'double_damage') {
        setHeroJoinerSlots(['Jessie', 'Jasser', 'Jessie', 'Seoyoon']);
      } else if (presetId === 'double_hp') {
        setHeroJoinerSlots(['Patrick', 'Sergey', 'Ling Xue', 'Patrick']);
      }
    });
  });

  // Hero Reset Button
  if (elements.btnHeroReset) {
    elements.btnHeroReset.addEventListener('click', () => {
      elements.btnHeroPresets.forEach(b => b.classList.remove('active'));
      if (state.sim.mode === 'attack') {
        const atkBtn = document.querySelector('.btn-hero-preset[data-preset="attack_all_out"]');
        if (atkBtn) atkBtn.classList.add('active');
        setHeroJoinerSlots(['Jessie', 'Jasser', 'Seoyoon', 'Norah']);
      } else {
        const defBtn = document.querySelector('.btn-hero-preset[data-preset="fortress_defense"]');
        if (defBtn) defBtn.classList.add('active');
        setHeroJoinerSlots(['Patrick', 'Sergey', 'Ling Xue', 'Ahmose']);
      }
    });
  }

  // Generation dropdown
  if (elements.simGenSelect) {
    elements.simGenSelect.addEventListener('change', onGenChange);
  }

  const rallyCountEl = document.getElementById('sim-rally-count');
  if (rallyCountEl) {
    rallyCountEl.addEventListener('change', () => {
      renderCaptainSelectionBlocks();
    });
  }

  // Server Selector
  if (elements.serverSelect) {
    elements.serverSelect.addEventListener('change', (e) => {
      const selectedId = e.target.value;
      const targetGuild = state.guilds.find(g => g.id === selectedId);
      if (targetGuild && !targetGuild.bot_installed && targetGuild.invite_url) {
        window.open(targetGuild.invite_url, '_blank');
        elements.serverSelect.value = state.currentGuildId;
        showToast(`Opening invite page for ${targetGuild.name}...`, 'info');
        return;
      }
      state.currentGuildId = selectedId;
      localStorage.setItem('troop_guild_id', selectedId);
      showToast(`Active server: ${targetGuild ? targetGuild.name : 'selected'}`, 'success');
      loadStats();
      loadPlayers();
    });
  }

  if (elements.btnRunSim) {
    elements.btnRunSim.addEventListener('click', runSimulation);
  }
  if (elements.btnSaveRules) {
    elements.btnSaveRules.addEventListener('click', saveRules);
  }
}

// ==========================================
// WAR ROOM LOGIC
// ==========================================

function setupWarRoomListeners() {
  const btnSelectAll = document.getElementById('btn-war-select-all');
  const btnClear = document.getElementById('btn-war-clear');
  const btnCalc = document.getElementById('btn-war-calculate');

  if (btnSelectAll) {
    btnSelectAll.addEventListener('click', async () => {
      const allIds = state.players.map(p => p.id);
      try {
        const res = await fetchApi('/api/attendance/select-all', {
          method: 'POST',
          body: JSON.stringify({ player_ids: allIds })
        });
        window.warRoomAttendance = new Set(allIds);
        document.getElementById('war-online-count').textContent = res.total_online;
        renderRoster(); // re-render checkboxes
        showToast('All currently listed players checked in.', 'success');
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  if (btnClear) {
    btnClear.addEventListener('click', async () => {
      try {
        const res = await fetchApi('/api/attendance/reset', { method: 'POST' });
        window.warRoomAttendance = new Set();
        document.getElementById('war-online-count').textContent = res.total_online;
        renderRoster(); // re-render checkboxes
        showToast('All check-ins cleared.', 'info');
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  if (btnCalc) {
    btnCalc.addEventListener('click', async () => {
      if (!window.warRoomAttendance || window.warRoomAttendance.size === 0) {
        showToast('Warning: No players checked in! Please check in players from the Roster tab first.', 'error');
        return;
      }

      const rallyCount = parseInt(document.getElementById('war-rallies').value, 10);
      const generation = parseInt(document.getElementById('war-generation').value, 10);
      const scope = document.getElementById('war-scope').value;

      const payload = {
        rally_count: rallyCount,
        generation: generation,
        event_scope: scope,
        online_only: true,
        post_to_discord: false
      };

      btnCalc.textContent = 'Calculating...';
      btnCalc.disabled = true;
      try {
        const res = await fetchApi('/api/rallies/calculate', {
          method: 'POST',
          body: JSON.stringify(payload)
        });
        renderWarResults(res.rallies || []);
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        btnCalc.textContent = 'Calculate Multi-Rally';
        btnCalc.disabled = false;
      }
    });
  }

  // Sub-tabs for Database vs War Room
  document.querySelectorAll('.sub-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.sub-tab').forEach(b => {
        b.classList.remove('active');
        b.style.background = 'transparent';
        b.style.color = 'var(--text-secondary)';
      });
      btn.classList.add('active');
      btn.style.background = 'var(--bg-card)';
      btn.style.color = 'var(--text-primary)';

      document.querySelectorAll('.sub-pane').forEach(p => p.style.display = 'none');
      const targetId = btn.getAttribute('data-sub');
      const target = document.getElementById(targetId);
      if (target) target.style.display = 'block';

      if (targetId === 'sub-war-room') {
        loadWarRoom();
      }
    });
  });
}

function renderWarResults(rallies) {
  const container = document.getElementById('war-results-container');
  if (!container) return;
  container.innerHTML = '';

  if (rallies.length === 0) {
    container.innerHTML = '<div class="glass-card"><p style="color:var(--text-muted);">No online players available to form rallies.</p></div>';
    return;
  }

  rallies.forEach(rally => {
    const card = document.createElement('div');
    card.className = 'glass-card';
    card.style.borderTop = `3px solid ${rally.role === 'main_strike' ? 'var(--color-amber)' : rally.role === 'garrison_defense' ? 'var(--color-cyan)' : 'var(--color-rose)'}`;

    // Create header with Hero Recommendations
    const p1 = rally.players[0];
    const recCaptain = p1?.recommended_captain || '-';
    const joiners = p1?.recommended_joiners?.join(', ') || '-';

    card.innerHTML = `
      <h3 style="margin-bottom: 8px;">${rally.label}</h3>
      <div style="display:flex; gap:16px; margin-bottom: 16px; font-size:13px;">
        <div><span style="color:var(--text-muted);">Recommended Captain:</span> <strong>${recCaptain}</strong></div>
        <div><span style="color:var(--text-muted);">Recommended Joiners:</span> <strong>${joiners}</strong></div>
        <div><span style="color:var(--text-muted);">Ratio:</span> <strong>${rally.ratio.infantry}% / ${rally.ratio.lancer}% / ${rally.ratio.marksman}%</strong></div>
      </div>
      <div class="table-responsive">
        <table class="data-table">
          <thead>
            <tr>
              <th>Player</th>
              <th>Infantry</th>
              <th>Lancers</th>
              <th>Marksman</th>
              <th>Total March</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            ${rally.players.map(p => `
              <tr>
                <td><strong>${escapeHtml(p.player_name)}</strong></td>
                <td style="color: var(--troop-inf);">${p.infantry_count.toLocaleString()}</td>
                <td style="color: var(--troop-lan);">${p.lancer_count.toLocaleString()}</td>
                <td style="color: var(--troop-mrk);">${p.marksman_count.toLocaleString()}</td>
                <td>${p.march_limit.toLocaleString()}</td>
                <td>${p.tactical_note ? `<span style="color:var(--color-amber); font-size:12px;">${p.tactical_note}</span>` : ''}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
    container.appendChild(card);
  });
}
// ==========================================

// Start
document.addEventListener('DOMContentLoaded', () => {
  initEventListeners();
  setupWarRoomListeners();
  initSimTypeToggle();
  loadPresets();
  loadHeroes();
  checkAuth().then(() => {
    loadStats();
    loadPlayers();
    loadAllianceTags();
  });
});


