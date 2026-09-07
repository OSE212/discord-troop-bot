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
  guilds: [],
  botInfo: null,
  sim: {
    mode: 'attack',
    formation_type: 'rally',
    inf: 50,
    lan: 20,
    mrk: 30,
    capacity: 1500000,
    result: null,
  },
  editingPlayerId: null,
  deletingPlayerId: null,
  // Hero tracking for the modal form
  formHeroes: [],   // [{name, stars, skill_level}]
  // Formation presets (loaded once)
  presets: [],
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
  filterChips: document.querySelectorAll('.filter-chip'),
  btnAddPlayer: document.getElementById('btn-add-player'),
  btnImportCsv: document.getElementById('btn-import-csv'),
  btnSurveyGenerator: document.getElementById('btn-survey-generator'),
  btnGuideSurvey: document.getElementById('btn-guide-survey'),
  csvFileInput: document.getElementById('csv-file-input'),
  btnQuickAddPlayer: document.getElementById('btn-quick-add-player'),
  btnQuickCalculate: document.getElementById('btn-quick-calculate'),
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
  simPresetSelect: document.getElementById('sim-preset-select'),
  simPresetGuide: document.getElementById('sim-preset-guide'),
  simPresetPlace: document.getElementById('sim-preset-place'),
  simPresetCallers: document.getElementById('sim-preset-callers'),
  simPresetJoiners: document.getElementById('sim-preset-joiners'),
  simPresetNotes: document.getElementById('sim-preset-notes'),
  simJoinersCard: document.getElementById('sim-joiners-card'),
  simJoinersList: document.getElementById('sim-joiners-list'),
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
      state.user = { authenticated: false, role: 'guest', name: null };
      renderAuth();
      openAuthModal();
      throw new Error('Authentication required');
    }
    const data = await res.json();
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
  elements.authModal.classList.add('active');
  elements.authPasskeyInput.value = '';
  elements.authPasskeyInput.focus();
}

function closeAuthModal() {
  elements.authModal.classList.remove('active');
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
const headerRight  = document.querySelector('.header-right');

function openMobileMenu() {
  if (headerCenter) headerCenter.classList.add('open');
  if (headerRight)  headerRight.classList.add('open');
  if (hamburgerBtn) hamburgerBtn.classList.add('active');
}

function closeMobileMenu() {
  if (headerCenter) headerCenter.classList.remove('open');
  if (headerRight)  headerRight.classList.remove('open');
  if (hamburgerBtn) hamburgerBtn.classList.remove('active');
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

// Close mobile menu when clicking outside the header
document.addEventListener('click', (e) => {
  const header = document.querySelector('.app-header');
  const menuPanel = headerCenter;
  if (
    menuPanel && menuPanel.classList.contains('open') &&
    header && !header.contains(e.target) &&
    menuPanel && !menuPanel.contains(e.target)
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

  const avgFcOverall = ((s.average_levels.infantry + s.average_levels.lancers + s.average_levels.marksman) / 3).toFixed(1);
  elements.statAvgFc.textContent = `FC ${avgFcOverall}`;
  elements.statFcBreakdown.textContent = `Inf: FC${s.average_levels.infantry} | Lan: FC${s.average_levels.lancers} | Mrk: FC${s.average_levels.marksman}`;

  // Breakdown bars
  elements.barInfStat.textContent = `${formatNumber(s.helios_quantities.infantry)} Helios | Avg FC ${s.average_levels.infantry}`;
  elements.barLanStat.textContent = `${formatNumber(s.helios_quantities.lancers)} Helios | Avg FC ${s.average_levels.lancers}`;
  elements.barMrkStat.textContent = `${formatNumber(s.helios_quantities.marksman)} Helios | Avg FC ${s.average_levels.marksman}`;

  const maxVal = Math.max(1, s.helios_quantities.infantry, s.helios_quantities.lancers, s.helios_quantities.marksman);
  elements.barInfFill.style.width = `${Math.max(15, (s.helios_quantities.infantry / maxVal) * 100)}%`;
  elements.barLanFill.style.width = `${Math.max(15, (s.helios_quantities.lancers / maxVal) * 100)}%`;
  elements.barMrkFill.style.width = `${Math.max(15, (s.helios_quantities.marksman / maxVal) * 100)}%`;
}

// Load Players
async function loadPlayers() {
  try {
    const q = encodeURIComponent(state.searchQuery);
    const filter = encodeURIComponent(state.activeFilter);
    const players = await fetchApi(`/api/players?q=${q}&filter=${filter}`);
    state.players = players;
    renderRoster();
  } catch (err) {
    elements.rosterTableBody.innerHTML = `<tr><td colspan="8" class="empty-cell text-danger">Failed to load players: ${err.message}</td></tr>`;
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

    const renderTroopPill = (t) => {
      if (t.level === null) return '<span class="text-muted">-</span>';
      const isHelios = t.helios;
      const qtyStr = isHelios && t.helios_quantity !== null ? ` (${formatNumber(t.helios_quantity)})` : '';
      return `<span class="pill-level ${isHelios ? 'helios' : ''}">${isHelios ? '🔥 ' : ''}FC${t.level}${qtyStr}</span>`;
    };

    const statusBadge = p.is_complete
      ? '<span class="status-badge complete">Complete</span>'
      : '<span class="status-badge incomplete">Incomplete</span>';

    return `
      <tr data-id="${p.id}">
        <td>
          <div class="player-identity">
            <span class="player-main-name">${escapeHtml(p.name)}</span>
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

window.removeHero = function(index) {
  state.formHeroes.splice(index, 1);
  renderHeroesGrid();
};

window.updateHeroField = function(index, field, value) {
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

// Simulator Calculation
async function runSimulation() {
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
      ratio: {
        infantry: state.sim.inf,
        lancers: state.sim.lan,
        marksman: state.sim.mrk,
      },
    };

    const result = await fetchApi('/api/calculate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    state.sim.result = result;
    renderSimResult();
    showToast('Formation calculation complete!', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    elements.btnRunSim.disabled = false;
    elements.btnRunSim.innerHTML = '<span>⚡</span> Run Calculation';
  }
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

  // Assignments
  if (!res.allocations || res.allocations.length === 0) {
    elements.simAssignmentsTbody.innerHTML = '<tr><td colspan="3" class="empty-cell">No players allocated (ensure players have complete registrations).</td></tr>';
  } else {
    elements.simAssignmentsTbody.innerHTML = res.allocations.map((a) => `
      <tr>
        <td><strong>${escapeHtml(a.player_name)}</strong></td>
        <td><span class="pill-level">${escapeHtml(a.troop_type.toUpperCase())}</span></td>
        <td><strong>${formatNumber(a.amount)}</strong></td>
      </tr>
    `).join('');
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
  const presetSel = elements.simPresetSelect;
  // Clear presets dropdown
  presetSel.innerHTML = '<option value="">— Pick formation —</option>';
  elements.simPresetGuide.classList.add('hidden');

  if (!gen) {
    presetSel.disabled = true;
    return;
  }

  const matches = state.presets.filter(p => String(p.generation) === gen);
  matches.forEach((p, i) => {
    const opt = document.createElement('option');
    opt.value = i;
    opt.textContent = `${p.name} (${p.ratio_str})`;
    presetSel.appendChild(opt);
  });
  presetSel.disabled = false;

  // Auto-select first preset
  if (matches.length > 0) {
    presetSel.selectedIndex = 1;
    applyPreset(matches[0]);
  }
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

  // Show guide card
  const guide = elements.simPresetGuide;
  guide.classList.remove('hidden');
  elements.simPresetPlace.textContent = preset.place;
  const callers = preset.callers;
  elements.simPresetCallers.textContent =
    `Callers — Inf: ${callers.infantry || '-'} | Lan: ${callers.lancer || '-'} | Mrk: ${callers.marksman || '-'}`;
  elements.simPresetJoiners.textContent =
    `Joiners ★: ${preset.joiners.join(' · ')}`;
  elements.simPresetNotes.textContent = preset.notes || '';
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

  elements.authCloseBtn.addEventListener('click', closeAuthModal);
  elements.authForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const passkey = elements.authPasskeyInput.value;
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
      showToast(err.message, 'error');
    }
  });

  elements.btnQuickCalculate.addEventListener('click', () => switchTab('simulator'));
  elements.btnQuickAddPlayer.addEventListener('click', openAddPlayerModal);
  elements.btnAddPlayer.addEventListener('click', openAddPlayerModal);

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
    });
  });

  elements.simTypeBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      elements.simTypeBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.sim.formation_type = btn.dataset.value;
    });
  });

  // Generation preset dropdowns
  if (elements.simGenSelect) {
    elements.simGenSelect.addEventListener('change', onGenChange);
  }
  if (elements.simPresetSelect) {
    elements.simPresetSelect.addEventListener('change', onPresetChange);
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

  elements.btnRunSim.addEventListener('click', runSimulation);
  elements.btnSaveRules.addEventListener('click', saveRules);
}

// Start
document.addEventListener('DOMContentLoaded', () => {
  initEventListeners();
  loadPresets();
  checkAuth().then(() => {
    loadStats();
    loadPlayers();
  });
});

