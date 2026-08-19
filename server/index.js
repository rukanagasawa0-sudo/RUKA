'use strict';

const path = require('path');
const fs = require('fs');
const express = require('express');
const http = require('http');
const multer = require('multer');
const { customAlphabet } = require('nanoid');
const { Server } = require('socket.io');

const nanoid = customAlphabet('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', 6);
const instanceId = customAlphabet('abcdefghijklmnopqrstuvwxyz0123456789', 12);

const PORT = process.env.PORT || 3000;
const UPLOAD_DIR = path.join(__dirname, 'uploads');
fs.mkdirSync(UPLOAD_DIR, { recursive: true });

const app = express();
const server = http.createServer(app);
const io = new Server(server);

app.use(express.static(path.join(__dirname, '..', 'public')));
app.use('/uploads', express.static(UPLOAD_DIR));
app.use('/cards', express.static(path.join(__dirname, '..', 'cards')));
app.use(express.json({ limit: '2mb' }));

// --- card image upload (kept local to this server; never committed to git) ---
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const roomId = (req.params.roomId || 'common').toUpperCase();
    const dir = path.join(UPLOAD_DIR, roomId);
    fs.mkdirSync(dir, { recursive: true });
    cb(null, dir);
  },
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname).slice(0, 10);
    cb(null, `${instanceId()}${ext}`);
  },
});
const upload = multer({
  storage,
  limits: { fileSize: 8 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    cb(null, /^image\//.test(file.mimetype));
  },
});

app.post('/api/rooms/:roomId/upload', upload.single('image'), (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'no image' });
  const roomId = req.params.roomId.toUpperCase();
  res.json({ url: `/uploads/${roomId}/${req.file.filename}` });
});

// ---------------------------------------------------------------------------
// In-memory game state. This is a private, throwaway simulator for a small
// group of friends — no database, no auth. Restarting the server clears
// everything, which is fine for the intended use.
// ---------------------------------------------------------------------------

const DEFAULT_SETTINGS = { mainDeckSize: 40, openingHand: 5, startingLife: 8 };
const PHASES = ['auto', 'main', 'end'];

/** @type {Map<string, Room>} */
const rooms = new Map();

function makeRoom(hostName) {
  const id = nanoid();
  const room = {
    id,
    createdAt: Date.now(),
    cardPool: {}, // cardId -> {id, name, type, text, image}
    settings: { ...DEFAULT_SETTINGS },
    players: {}, // playerId -> Player
    order: [],
    instances: {}, // instanceId -> { cardId, ownerId }
    turnIndex: 0,
    phase: PHASES[0],
    turnNumber: 1,
    started: false,
    log: [],
  };
  rooms.set(id, room);
  return room;
}

function makePlayer(name, socketId) {
  return {
    id: instanceId(),
    name: name || 'プレイヤー',
    socketId,
    connected: true,
    deckList: [], // array of cardId, length === settings.mainDeckSize
    partnerCardId: null,
    caseCardId: null,
    ready: false,
    zones: { deck: [], hand: [], field: [], trash: [], partner: null, case: null },
    counters: { life: DEFAULT_SETTINGS.startingLife },
  };
}

function pushLog(room, text) {
  room.log.push({ t: Date.now(), text });
  if (room.log.length > 200) room.log.shift();
}

function shuffle(arr) {
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function cardDef(room, cardId) {
  return room.cardPool[cardId] || { id: cardId, name: '(未登録カード)', type: '?', text: '', image: null };
}

function publicCard(room, instId) {
  const inst = room.instances[instId];
  if (!inst) return null;
  return { instanceId: instId, ...cardDef(room, inst.cardId) };
}

function zoneAsCards(room, ids) {
  return ids.map((id) => publicCard(room, id)).filter(Boolean);
}

function slotAsCard(room, id) {
  return id ? publicCard(room, id) : null;
}

function otherPlayerId(room, playerId) {
  return room.order.find((id) => id !== playerId) || null;
}

function viewFor(room, viewerId) {
  const selfP = room.players[viewerId];
  const oppId = otherPlayerId(room, viewerId);
  const oppP = oppId ? room.players[oppId] : null;

  const selfView = selfP && {
    id: selfP.id,
    name: selfP.name,
    connected: selfP.connected,
    ready: selfP.ready,
    counters: selfP.counters,
    deckCount: selfP.zones.deck.length,
    hand: zoneAsCards(room, selfP.zones.hand),
    field: zoneAsCards(room, selfP.zones.field),
    trash: zoneAsCards(room, selfP.zones.trash),
    partner: slotAsCard(room, selfP.zones.partner),
    case: slotAsCard(room, selfP.zones.case),
  };

  const oppView = oppP && {
    id: oppP.id,
    name: oppP.name,
    connected: oppP.connected,
    ready: oppP.ready,
    counters: oppP.counters,
    deckCount: oppP.zones.deck.length,
    handCount: oppP.zones.hand.length,
    field: zoneAsCards(room, oppP.zones.field),
    trash: zoneAsCards(room, oppP.zones.trash),
    partner: slotAsCard(room, oppP.zones.partner),
    case: slotAsCard(room, oppP.zones.case),
  };

  return {
    roomId: room.id,
    settings: room.settings,
    started: room.started,
    phase: room.phase,
    phases: PHASES,
    turnNumber: room.turnNumber,
    turnPlayerId: room.order[room.turnIndex] || null,
    you: selfView || null,
    opponent: oppView || null,
    cardPoolCount: Object.keys(room.cardPool).length,
    log: room.log.slice(-40),
  };
}

function broadcastState(room) {
  for (const pid of room.order) {
    const p = room.players[pid];
    if (p && p.socketId) {
      io.to(p.socketId).emit('state', viewFor(room, pid));
    }
  }
}

function requireRoom(roomId) {
  const room = rooms.get((roomId || '').toUpperCase());
  return room || null;
}

io.on('connection', (socket) => {
  let currentRoomId = null;
  let currentPlayerId = null;

  socket.on('room:create', ({ name }, cb) => {
    const room = makeRoom(name);
    const player = makePlayer(name, socket.id);
    room.players[player.id] = player;
    room.order.push(player.id);
    currentRoomId = room.id;
    currentPlayerId = player.id;
    socket.join(room.id);
    pushLog(room, `${player.name} がルームを作成しました`);
    cb && cb({ ok: true, roomId: room.id, playerId: player.id });
    broadcastState(room);
  });

  socket.on('room:join', ({ roomId, name }, cb) => {
    const room = requireRoom(roomId);
    if (!room) return cb && cb({ ok: false, error: 'ルームが見つかりません' });
    if (room.order.length >= 2) return cb && cb({ ok: false, error: 'ルームは満員です（2人まで）' });
    const player = makePlayer(name, socket.id);
    room.players[player.id] = player;
    room.order.push(player.id);
    currentRoomId = room.id;
    currentPlayerId = player.id;
    socket.join(room.id);
    pushLog(room, `${player.name} が参加しました`);
    cb && cb({ ok: true, roomId: room.id, playerId: player.id });
    if (Object.keys(room.cardPool).length) {
      socket.emit('cardpool:full', { cards: Object.values(room.cardPool), settings: room.settings });
    }
    broadcastState(room);
  });

  socket.on('room:rejoin', ({ roomId, playerId }, cb) => {
    const room = requireRoom(roomId);
    const player = room && room.players[playerId];
    if (!room || !player) return cb && cb({ ok: false, error: '再接続できませんでした' });
    player.socketId = socket.id;
    player.connected = true;
    currentRoomId = room.id;
    currentPlayerId = player.id;
    socket.join(room.id);
    cb && cb({ ok: true, roomId: room.id, playerId: player.id });
    if (Object.keys(room.cardPool).length) {
      socket.emit('cardpool:full', { cards: Object.values(room.cardPool), settings: room.settings });
    }
    broadcastState(room);
  });

  socket.on('cardpool:set', ({ roomId, cards, settings }, cb) => {
    const room = requireRoom(roomId);
    if (!room) return cb && cb({ ok: false, error: 'ルームが見つかりません' });
    if (room.started) return cb && cb({ ok: false, error: '対戦中は変更できません' });
    if (!Array.isArray(cards)) return cb && cb({ ok: false, error: '不正なカードデータです' });
    room.cardPool = {};
    for (const c of cards) {
      if (!c || !c.id) continue;
      room.cardPool[c.id] = {
        id: String(c.id),
        name: String(c.name || c.id),
        type: String(c.type || 'card'),
        text: String(c.text || ''),
        image: c.image || null,
      };
    }
    if (settings && typeof settings === 'object') {
      room.settings = { ...room.settings, ...settings };
    }
    pushLog(room, `カードセットを読み込みました（${Object.keys(room.cardPool).length}種）`);
    cb && cb({ ok: true });
    io.to(room.id).emit('cardpool:full', { cards: Object.values(room.cardPool), settings: room.settings });
    broadcastState(room);
  });

  socket.on('deck:submit', ({ roomId, playerId, mainDeck, partnerCardId, caseCardId }, cb) => {
    const room = requireRoom(roomId);
    const player = room && room.players[playerId];
    if (!room || !player) return cb && cb({ ok: false, error: '不正なリクエストです' });
    if (room.started) return cb && cb({ ok: false, error: '対戦中は変更できません' });
    if (!Array.isArray(mainDeck) || mainDeck.length !== room.settings.mainDeckSize) {
      return cb && cb({ ok: false, error: `メインデッキは${room.settings.mainDeckSize}枚にしてください（現在${(mainDeck || []).length}枚）` });
    }
    for (const cid of mainDeck) {
      if (!room.cardPool[cid]) return cb && cb({ ok: false, error: `未登録のカードIDです: ${cid}` });
    }
    if (partnerCardId && !room.cardPool[partnerCardId]) return cb && cb({ ok: false, error: '未登録のパートナーカードです' });
    if (caseCardId && !room.cardPool[caseCardId]) return cb && cb({ ok: false, error: '未登録の事件カードです' });

    player.deckList = mainDeck.slice();
    player.partnerCardId = partnerCardId || null;
    player.caseCardId = caseCardId || null;
    player.ready = true;
    pushLog(room, `${player.name} がデッキを準備しました`);
    cb && cb({ ok: true });
    broadcastState(room);
  });

  socket.on('game:start', ({ roomId, playerId }, cb) => {
    const room = requireRoom(roomId);
    if (!room) return cb && cb({ ok: false, error: 'ルームが見つかりません' });
    if (room.order.length < 2) return cb && cb({ ok: false, error: '対戦相手を待っています' });
    if (!room.order.every((pid) => room.players[pid].ready)) {
      return cb && cb({ ok: false, error: '両者のデッキ準備が完了していません' });
    }
    if (room.started) return cb && cb({ ok: false, error: 'すでに開始しています' });

    room.instances = {};
    for (const pid of room.order) {
      const p = room.players[pid];
      const instIds = p.deckList.map((cardId) => {
        const id = instanceId();
        room.instances[id] = { cardId, ownerId: pid };
        return id;
      });
      shuffle(instIds);
      p.zones.deck = instIds;
      p.zones.hand = [];
      p.zones.field = [];
      p.zones.trash = [];
      p.counters.life = room.settings.startingLife;

      if (p.partnerCardId) {
        const pid2 = instanceId();
        room.instances[pid2] = { cardId: p.partnerCardId, ownerId: pid };
        p.zones.partner = pid2;
      }
      if (p.caseCardId) {
        const cid2 = instanceId();
        room.instances[cid2] = { cardId: p.caseCardId, ownerId: pid };
        p.zones.case = cid2;
      }
      for (let i = 0; i < room.settings.openingHand; i++) {
        const drawn = p.zones.deck.shift();
        if (drawn) p.zones.hand.push(drawn);
      }
    }
    room.turnIndex = 0;
    room.turnNumber = 1;
    room.phase = PHASES[0];
    room.started = true;
    pushLog(room, '対戦を開始しました');
    cb && cb({ ok: true });
    broadcastState(room);
  });

  function withRoomAndTurnPlayer(roomId, playerId) {
    const room = requireRoom(roomId);
    const player = room && room.players[playerId];
    return { room, player };
  }

  socket.on('game:draw', ({ roomId, playerId, count }) => {
    const { room, player } = withRoomAndTurnPlayer(roomId, playerId);
    if (!room || !player || !room.started) return;
    const n = Math.max(1, Math.min(10, Number(count) || 1));
    for (let i = 0; i < n; i++) {
      const drawn = player.zones.deck.shift();
      if (drawn) player.zones.hand.push(drawn);
    }
    pushLog(room, `${player.name} が${n}枚ドローしました`);
    broadcastState(room);
  });

  const ZONE_KEYS = ['deck', 'hand', 'field', 'trash', 'partner', 'case'];

  socket.on('game:move', ({ roomId, playerId, instanceId: instId, from, to, position }) => {
    const { room, player } = withRoomAndTurnPlayer(roomId, playerId);
    if (!room || !player || !room.started) return;
    if (!ZONE_KEYS.includes(from) || !ZONE_KEYS.includes(to)) return;
    const inst = room.instances[instId];
    if (!inst || inst.ownerId !== playerId) return;

    const removeFrom = (zoneKey) => {
      if (zoneKey === 'partner' || zoneKey === 'case') {
        if (player.zones[zoneKey] === instId) player.zones[zoneKey] = null;
      } else {
        const arr = player.zones[zoneKey];
        const idx = arr.indexOf(instId);
        if (idx >= 0) arr.splice(idx, 1);
      }
    };
    const addTo = (zoneKey) => {
      if (zoneKey === 'partner' || zoneKey === 'case') {
        if (player.zones[zoneKey]) {
          // bump existing card back to trash to keep the slot single-card
          player.zones.trash.push(player.zones[zoneKey]);
        }
        player.zones[zoneKey] = instId;
      } else if (zoneKey === 'deck') {
        if (position === 'bottom') player.zones.deck.push(instId);
        else player.zones.deck.unshift(instId);
      } else {
        player.zones[zoneKey].push(instId);
      }
    };

    removeFrom(from);
    addTo(to);
    const cd = cardDef(room, inst.cardId);
    pushLog(room, `${player.name}: 「${cd.name}」を ${from} → ${to}`);
    broadcastState(room);
  });

  socket.on('game:shuffleDeck', ({ roomId, playerId }) => {
    const { room, player } = withRoomAndTurnPlayer(roomId, playerId);
    if (!room || !player || !room.started) return;
    shuffle(player.zones.deck);
    pushLog(room, `${player.name} が山札をシャッフルしました`);
    broadcastState(room);
  });

  socket.on('game:counter', ({ roomId, playerId, targetPlayerId, counter, delta }) => {
    const room = requireRoom(roomId);
    if (!room || !room.started) return;
    const target = room.players[targetPlayerId];
    if (!target) return;
    const key = String(counter || 'life');
    const cur = Number(target.counters[key] || 0);
    target.counters[key] = cur + Number(delta || 0);
    const actor = room.players[playerId];
    pushLog(room, `${actor ? actor.name : '?'}: ${target.name} の ${key} を ${delta > 0 ? '+' : ''}${delta}`);
    broadcastState(room);
  });

  socket.on('game:phase:next', ({ roomId, playerId }) => {
    const room = requireRoom(roomId);
    if (!room || !room.started) return;
    if (room.order[room.turnIndex] !== playerId) return;
    const idx = PHASES.indexOf(room.phase);
    if (idx < PHASES.length - 1) {
      room.phase = PHASES[idx + 1];
      pushLog(room, `フェイズ: ${room.phase}`);
      broadcastState(room);
    }
  });

  socket.on('game:turn:end', ({ roomId, playerId }) => {
    const room = requireRoom(roomId);
    if (!room || !room.started) return;
    if (room.order[room.turnIndex] !== playerId) return;
    room.turnIndex = (room.turnIndex + 1) % room.order.length;
    if (room.turnIndex === 0) room.turnNumber += 1;
    room.phase = PHASES[0];
    const next = room.players[room.order[room.turnIndex]];
    pushLog(room, `ターン交代 → ${next ? next.name : '?'}`);
    broadcastState(room);
  });

  socket.on('chat:message', ({ roomId, playerId, text }) => {
    const room = requireRoom(roomId);
    const player = room && room.players[playerId];
    if (!room || !player || !text) return;
    pushLog(room, `[チャット] ${player.name}: ${String(text).slice(0, 300)}`);
    broadcastState(room);
  });

  socket.on('disconnect', () => {
    if (!currentRoomId || !currentPlayerId) return;
    const room = rooms.get(currentRoomId);
    const player = room && room.players[currentPlayerId];
    if (player) {
      player.connected = false;
      pushLog(room, `${player.name} が切断しました`);
      broadcastState(room);
    }
  });
});

server.listen(PORT, () => {
  console.log(`RUKA card sim listening on http://localhost:${PORT}`);
});
