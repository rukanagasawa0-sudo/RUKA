'use strict';

const socket = io();

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

const ZONE_LABEL = {
  deck: '山札', hand: '手札', field: 'フィールド', trash: 'トラッシュ',
  partner: 'パートナー枠', case: '事件枠',
};

// ---- persisted identity (so a page reload / second tab can rejoin) ----
const store = {
  get: (k) => { try { return JSON.parse(localStorage.getItem(k)); } catch { return null; } },
  set: (k, v) => localStorage.setItem(k, JSON.stringify(v)),
};

let me = store.get('ruka:me') || null; // { roomId, playerId, name }
let cardPool = []; // full pool with images/text, for deck builder
let poolSettings = { mainDeckSize: 40, openingHand: 5, startingLife: 8 };
let deckCounts = {}; // cardId -> qty in main deck
let partnerPick = '';
let casePick = '';
let latestState = null;

function showScreen(id) {
  $$('.screen').forEach((s) => s.classList.add('hidden'));
  $(id).classList.remove('hidden');
}

// ------------------------------- connection badge -------------------------------
socket.on('connect', () => {
  $('#connBadge').textContent = '接続中';
  $('#connBadge').className = 'badge online';
  if (me && me.roomId && me.playerId) {
    socket.emit('room:rejoin', { roomId: me.roomId, playerId: me.playerId }, (res) => {
      if (res && res.ok) {
        $('#roomCodeLabel').textContent = me.roomId;
        showScreen(latestState && latestState.started ? '#screen-board' : '#screen-setup');
      } else {
        me = null; store.set('ruka:me', null);
        showScreen('#screen-lobby');
      }
    });
  }
});
socket.on('disconnect', () => {
  $('#connBadge').textContent = '切断されました（再接続を試みています…）';
  $('#connBadge').className = 'badge offline';
});

// ------------------------------- lobby -------------------------------
$('#btnCreate').addEventListener('click', () => {
  const name = $('#nameInput').value.trim() || 'プレイヤー';
  socket.emit('room:create', { name }, (res) => {
    if (!res.ok) return ($('#lobbyError').textContent = res.error || 'エラー');
    me = { roomId: res.roomId, playerId: res.playerId, name };
    store.set('ruka:me', me);
    $('#roomCodeLabel').textContent = res.roomId;
    showScreen('#screen-setup');
  });
});

$('#btnJoin').addEventListener('click', () => {
  const name = $('#nameInput').value.trim() || 'プレイヤー';
  const code = $('#joinCode').value.trim().toUpperCase();
  if (!code) return ($('#lobbyError').textContent = 'ルームコードを入力してください');
  socket.emit('room:join', { roomId: code, name }, (res) => {
    if (!res.ok) return ($('#lobbyError').textContent = res.error || 'エラー');
    me = { roomId: res.roomId, playerId: res.playerId, name };
    store.set('ruka:me', me);
    $('#roomCodeLabel').textContent = res.roomId;
    showScreen('#screen-setup');
  });
});

// ------------------------------- card pool loading -------------------------------
function applyPoolPayload(payload) {
  if (payload.settings) poolSettings = { ...poolSettings, ...payload.settings };
  cardPool = payload.cards || [];
  renderDeckBuilder();
}

$('#btnLoadSample').addEventListener('click', async () => {
  const res = await fetch('/cards/sample-cards.json');
  const data = await res.json();
  sendPool(data);
});

$('#cardJsonFile').addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const data = JSON.parse(reader.result);
      sendPool(data);
    } catch (err) {
      $('#poolStatus').textContent = 'JSONの読み込みに失敗しました: ' + err.message;
    }
  };
  reader.readAsText(file);
});

function sendPool(data) {
  socket.emit('cardpool:set', { roomId: me.roomId, cards: data.cards || [], settings: data.settings || {} }, (res) => {
    $('#poolStatus').textContent = res.ok
      ? `カードデータを読み込みました（${(data.cards || []).length}種）`
      : ('エラー: ' + res.error);
  });
}

socket.on('cardpool:full', (payload) => applyPoolPayload(payload));

// ------------------------------- image upload -------------------------------
$('#imageUpload').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file || !me) return;
  const form = new FormData();
  form.append('image', file);
  $('#uploadResult').textContent = 'アップロード中…';
  try {
    const res = await fetch(`/api/rooms/${me.roomId}/upload`, { method: 'POST', body: form });
    const data = await res.json();
    if (data.url) {
      $('#uploadResult').textContent = `アップロード完了 → このURLをJSONの "image" に貼ってください: ${data.url}`;
    } else {
      $('#uploadResult').textContent = 'アップロード失敗: ' + (data.error || '不明なエラー');
    }
  } catch (err) {
    $('#uploadResult').textContent = 'アップロード失敗: ' + err.message;
  }
});

// ------------------------------- deck builder -------------------------------
function renderDeckBuilder() {
  const el = $('#deckBuilder');
  if (!cardPool.length) {
    el.innerHTML = '<p class="hint">先に①でカードデータを読み込んでください。</p>';
    return;
  }
  const mainPool = cardPool.filter((c) => c.type !== 'partner' && c.type !== 'case');
  const partnerPool = cardPool.filter((c) => c.type === 'partner');
  const casePool = cardPool.filter((c) => c.type === 'case');

  const rows = mainPool.map((c) => {
    const qty = deckCounts[c.id] || 0;
    return `
      <div class="pool-row" data-id="${c.id}">
        <div>
          <div class="pname">${escapeHtml(c.name)}</div>
          <div class="ptype">${escapeHtml(c.type)}</div>
        </div>
        <div class="stepper">
          <button data-act="dec">−</button>
          <span class="qty">${qty}</span>
          <button data-act="inc">＋</button>
        </div>
      </div>`;
  }).join('');

  const total = Object.values(deckCounts).reduce((a, b) => a + b, 0);

  const partnerOpts = partnerPool.map((c) => `<option value="${c.id}" ${partnerPick === c.id ? 'selected' : ''}>${escapeHtml(c.name)}</option>`).join('');
  const caseOpts = casePool.map((c) => `<option value="${c.id}" ${casePick === c.id ? 'selected' : ''}>${escapeHtml(c.name)}</option>`).join('');

  el.innerHTML = `
    <div class="deck-summary">メインデッキ: <b>${total} / ${poolSettings.mainDeckSize}</b> 枚</div>
    <div class="slotpicker">
      <label>パートナーカード
        <select id="partnerSelect"><option value="">(なし)</option>${partnerOpts}</select>
      </label>
      <label>事件カード
        <select id="caseSelect"><option value="">(なし)</option>${caseOpts}</select>
      </label>
    </div>
    <div class="pool-list">${rows}</div>
  `;

  $('#partnerSelect').addEventListener('change', (e) => { partnerPick = e.target.value; });
  $('#caseSelect').addEventListener('change', (e) => { casePick = e.target.value; });

  el.querySelectorAll('.pool-row').forEach((row) => {
    const id = row.dataset.id;
    row.querySelector('[data-act="inc"]').addEventListener('click', () => {
      deckCounts[id] = (deckCounts[id] || 0) + 1;
      renderDeckBuilder();
    });
    row.querySelector('[data-act="dec"]').addEventListener('click', () => {
      deckCounts[id] = Math.max(0, (deckCounts[id] || 0) - 1);
      if (!deckCounts[id]) delete deckCounts[id];
      renderDeckBuilder();
    });
  });
}

$('#btnSubmitDeck').addEventListener('click', () => {
  const mainDeck = [];
  for (const [id, qty] of Object.entries(deckCounts)) {
    for (let i = 0; i < qty; i++) mainDeck.push(id);
  }
  socket.emit('deck:submit', {
    roomId: me.roomId, playerId: me.playerId,
    mainDeck, partnerCardId: partnerPick || null, caseCardId: casePick || null,
  }, (res) => {
    if (res.ok) {
      $('#deckError').style.color = 'var(--good)';
      $('#deckError').textContent = 'デッキ準備完了！相手を待っています。';
    } else {
      $('#deckError').style.color = 'var(--accent2)';
      $('#deckError').textContent = res.error;
    }
  });
});

$('#btnStart').addEventListener('click', () => {
  socket.emit('game:start', { roomId: me.roomId, playerId: me.playerId }, (res) => {
    $('#startError').textContent = res.ok ? '' : res.error;
  });
});

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

// ------------------------------- shared state handler -------------------------------
socket.on('state', (state) => {
  latestState = state;

  if (!state.started) {
    renderSetupPlayers(state);
    showScreen('#screen-setup');
    return;
  }

  showScreen('#screen-board');
  renderBoard(state);
  renderLog(state);
});

function renderSetupPlayers(state) {
  const you = state.you, opp = state.opponent;
  const parts = [];
  if (you) parts.push(`<div class="zone">あなた: ${escapeHtml(you.name)} ${you.ready ? '✅準備完了' : '準備中'}</div>`);
  if (opp) parts.push(`<div class="zone">相手: ${escapeHtml(opp.name)} ${opp.ready ? '✅準備完了' : '準備中'}</div>`);
  else parts.push('<div class="zone hint">相手の参加を待っています…</div>');
  $('#playersInSetup').innerHTML = parts.join('');
  $('#btnStart').disabled = !(you && you.ready && opp && opp.ready);
}

function renderLog(state) {
  const el = $('#log');
  const wasAtBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - 10;
  el.innerHTML = state.log.map((l) => `<div>${escapeHtml(l.text)}</div>`).join('');
  if (wasAtBottom) el.scrollTop = el.scrollHeight;
}

// ------------------------------- board rendering -------------------------------
function makeCardEl(card, zone, isSelf) {
  const div = document.createElement('div');
  div.className = 'gcard' + (card.image ? '' : ' notext');
  if (card.image) {
    const img = document.createElement('img');
    img.src = card.image;
    img.alt = card.name;
    div.appendChild(img);
  }
  const badge = document.createElement('div');
  badge.className = 'typebadge';
  badge.textContent = card.type || '';
  div.appendChild(badge);
  const label = document.createElement('div');
  label.className = 'label';
  label.textContent = card.name;
  div.appendChild(label);
  if (card.text) div.title = card.text;

  if (isSelf) {
    div.addEventListener('click', (e) => openCardMenu(e, card, zone));
  }
  return div;
}

function renderZoneCards(elId, cards, zone, isSelf) {
  const container = document.querySelector(`#${elId} .cards`);
  if (!container) return;
  container.innerHTML = '';
  cards.forEach((c) => container.appendChild(makeCardEl(c, zone, isSelf)));
}

function renderSlot(elId, card, zone, isSelf) {
  const container = document.querySelector(`#${elId} .slot`);
  if (!container) return;
  container.innerHTML = '';
  if (card) container.appendChild(makeCardEl(card, zone, isSelf));
}

function renderCounters(elId, playerId, counters) {
  const el = $(elId);
  el.innerHTML = Object.entries(counters).map(([k, v]) => `
    <div class="counter-pill">
      <button data-counter="${k}" data-delta="-1" data-target="${playerId}">−</button>
      <span>${escapeHtml(k)} ${v}</span>
      <button data-counter="${k}" data-delta="1" data-target="${playerId}">＋</button>
    </div>
  `).join('');
  el.querySelectorAll('button').forEach((b) => {
    b.addEventListener('click', () => {
      socket.emit('game:counter', {
        roomId: me.roomId, playerId: me.playerId,
        targetPlayerId: b.dataset.target, counter: b.dataset.counter, delta: Number(b.dataset.delta),
      });
    });
  });
}

function renderBoard(state) {
  const you = state.you, opp = state.opponent;
  if (!you) return;

  $('#selfName').textContent = you.name + (you.connected === false ? '（切断中）' : '');
  renderCounters('#selfCounters', you.id, you.counters);
  $('#selfDeckCount').textContent = you.deckCount;
  renderZoneCards('selfHand', you.hand, 'hand', true);
  renderZoneCards('selfField', you.field, 'field', true);
  renderZoneCards('selfTrash', you.trash, 'trash', true);
  renderSlot('selfPartner', you.partner, 'partner', true);
  renderSlot('selfCase', you.case, 'case', true);

  if (opp) {
    $('#oppName').textContent = opp.name + (opp.connected === false ? '（切断中）' : '');
    renderCounters('#oppCounters', opp.id, opp.counters);
    $('#oppDeckCount').textContent = opp.deckCount;
    $('#oppHandCount').textContent = opp.handCount;
    renderZoneCards('oppField', opp.field, 'field', false);
    renderZoneCards('oppTrash', opp.trash, 'trash', false);
    renderSlot('oppPartner', opp.partner, 'partner', false);
    renderSlot('oppCase', opp.case, 'case', false);
  }

  const isMyTurn = state.turnPlayerId === you.id;
  $('#turnLabel').textContent = `ターン${state.turnNumber} — ${isMyTurn ? 'あなたの番' : (opp ? opp.name + 'の番' : '相手の番')}`;
  $('#phaseLabel').textContent = state.phase;
  $('#btnNextPhase').disabled = !isMyTurn;
  $('#btnEndTurn').disabled = !isMyTurn;
}

// deck actions
$('[data-draw="1"]').addEventListener('click', () => {
  socket.emit('game:draw', { roomId: me.roomId, playerId: me.playerId, count: 1 });
});
$('#btnShuffle').addEventListener('click', () => {
  socket.emit('game:shuffleDeck', { roomId: me.roomId, playerId: me.playerId });
});
$('#btnNextPhase').addEventListener('click', () => {
  socket.emit('game:phase:next', { roomId: me.roomId, playerId: me.playerId });
});
$('#btnEndTurn').addEventListener('click', () => {
  socket.emit('game:turn:end', { roomId: me.roomId, playerId: me.playerId });
});

// ------------------------------- card context menu -------------------------------
function openCardMenu(evt, card, fromZone) {
  evt.stopPropagation();
  const menu = $('#cardMenu');
  const targets = ['hand', 'field', 'trash', 'partner', 'case', 'deck'].filter((z) => z !== fromZone);

  const buttons = [];
  for (const z of targets) {
    if (z === 'deck') {
      buttons.push({ label: '山札の上へ戻す', to: 'deck', position: 'top' });
      buttons.push({ label: '山札の下へ戻す', to: 'deck', position: 'bottom' });
    } else {
      buttons.push({ label: `${ZONE_LABEL[z]}へ移動`, to: z });
    }
  }

  menu.innerHTML = `<div class="hint" style="padding:2px 6px 6px;max-width:180px;">${escapeHtml(card.name)}</div>` +
    buttons.map((b, i) => `<button data-i="${i}">${b.label}</button>`).join('') +
    `<button data-close="1">閉じる</button>`;

  menu.style.left = Math.min(evt.clientX, window.innerWidth - 200) + 'px';
  menu.style.top = Math.min(evt.clientY, window.innerHeight - 200) + 'px';
  menu.classList.remove('hidden');

  menu.querySelectorAll('button[data-i]').forEach((btn) => {
    const b = buttons[Number(btn.dataset.i)];
    btn.addEventListener('click', () => {
      socket.emit('game:move', {
        roomId: me.roomId, playerId: me.playerId,
        instanceId: card.instanceId, from: fromZone, to: b.to, position: b.position,
      });
      closeCardMenu();
    });
  });
  menu.querySelector('[data-close]').addEventListener('click', closeCardMenu);
}
function closeCardMenu() { $('#cardMenu').classList.add('hidden'); }
document.addEventListener('click', closeCardMenu);

// ------------------------------- chat -------------------------------
$('#chatForm').addEventListener('submit', (e) => {
  e.preventDefault();
  const input = $('#chatInput');
  const text = input.value.trim();
  if (!text || !me) return;
  socket.emit('chat:message', { roomId: me.roomId, playerId: me.playerId, text });
  input.value = '';
});
