//frontend/js/polyphonic.js

// ── STATE ──
const urlFile = new URLSearchParams(location.search).get('file');
let analysisResult = null;
let audioPlayers   = {};
let currentPlaying = null;
const BASE_URL     = 'http://127.0.0.1:8000';

let notationXMLUrl = null;
let osmdInstance = null;

let midiUrl = null;
let midiPlayer = null;

// Accent colors per stem
const STEM_COLORS = {
  drums:  { col:'#f59e0b', bg:'rgba(245,158,11,.1)',  border:'rgba(245,158,11,.3)'  },
  bass:   { col:'#22c55e', bg:'rgba(34,197,94,.1)',   border:'rgba(34,197,94,.3)'   },
  vocals: { col:'#ec4899', bg:'rgba(236,72,153,.1)',  border:'rgba(236,72,153,.3)'  },
  other:  { col:'#818cf8', bg:'rgba(129,140,248,.1)', border:'rgba(129,140,248,.3)' },
  piano:  { col:'#0096FF', bg:'rgba(0,150,255,.1)',   border:'rgba(0,150,255,.3)'   },
};
const STEM_ICONS   = { drums:'🥁', bass:'🎸', vocals:'🎤', other:'🎹', piano:'🎹' };
const DEFAULT_THEME = { col:'#38b6ff', bg:'rgba(56,182,255,.1)', border:'rgba(56,182,255,.3)' };

const STEP_MESSAGES = [
  'Running Demucs stem separation…',
  'Detecting instruments per stem…',
  'Checking for piano-only source…',
  'Running transcription pipeline…',
  'Generating MusicXML score…',
  'Building Sargam notation…',
];

// ── INIT ──
document.getElementById('sideFileName').textContent = urlFile || 'No file loaded';

// ── INNER TAB SWITCH ──
function switchInnerTab(name) {

  const map = { stems:'1', notation:'2', sargam:'3' };

  ['stems','notation','sargam'].forEach(t => {
    document.getElementById('tab-'+t).classList.toggle('active', t===name);
    document.getElementById('itab'+map[t]).classList.toggle('active', t===name);
  });

  // Render OSMD ONLY when notation tab becomes visible
  if (name === 'notation' && notationXMLUrl && !osmdInstance) {

    setTimeout(() => {
      renderMusicXML(notationXMLUrl);
    }, 200);

  }
}

// ── PIPELINE STEP HELPERS ──
function setStep(n, state) {
  const el = document.getElementById('st'+n);
  el.classList.remove('active','done');
  if (state) el.classList.add(state);
}
function setStepsUpTo(n) {
  for (let i = 1; i <= 6; i++) {
    if      (i < n)  setStep(i, 'done');
    else if (i === n) setStep(i, 'active');
    else              setStep(i, '');
  }
}
function allStepsDone() {
  for (let i = 1; i <= 6; i++) setStep(i, 'done');
}

// ── SHOW ERROR BANNER ──
function showErrorBanner(message) {
  const ss = document.getElementById('stemsScroll');
  ss.style.display = 'flex';
  ss.style.flexDirection = 'column';
  ss.innerHTML = `
    <div class="error-banner">
      <div class="eb-icon">⚠️</div>
      <div class="eb-body">
        <div class="eb-title">Analysis Failed</div>
        ${message}
      </div>
    </div>`;
}

// ── ANALYZE ──
document.getElementById('analyzeBtn').onclick = async () => {
  if (!urlFile) {
    alert('No audio file specified. Return to Upload & Detect.');
    return;
  }

  const btn = document.getElementById('analyzeBtn');
  btn.disabled = true;
  document.getElementById('runSpinner').style.display = 'block';
  document.getElementById('runBtnText').textContent = 'Analyzing…';

  // Reset UI
  document.getElementById('idleState').style.display    = 'none';
  document.getElementById('stemsScroll').style.display  = 'none';
  const ls = document.getElementById('loadingState');
  ls.style.display = 'flex';
  ls.style.flexDirection = 'column';
  document.getElementById('loadingFill').style.width = '0%';

  // Reset notation tab
  // Reset notation tab
  document.getElementById('notationIdle').style.display  = 'flex';
  document.getElementById('sheetContainer').style.display = 'none';
  document.getElementById('sheetContainer').innerHTML = '';
  document.getElementById('dlXmlView').style.display  = 'none';
  document.getElementById('dlXmlDown').style.display  = 'none';
  document.getElementById('playMidiBtn').style.display = 'none';
  // ✅ Reset these so new analysis renders fresh
  osmdInstance   = null;
  notationXMLUrl = null;
  midiUrl        = null;

  // Reset sargam tab
  document.getElementById('sargamIdle').style.display    = 'block';
  document.getElementById('sargamContent').style.display = 'none';

  // Animate pipeline steps
  let stepIdx = 0;
  const progStep = 100 / 6;
  const stepInterval = setInterval(() => {
    if (stepIdx < 6) {
      setStepsUpTo(stepIdx + 1);
      document.getElementById('loadingStep').textContent = STEP_MESSAGES[stepIdx];
      document.getElementById('loadingFill').style.width = ((stepIdx + 1) * progStep) + '%';
      stepIdx++;
    }
  }, 900);

  try {
    const res = await fetch(
      `${BASE_URL}/analyze/polyphonic/?filename=${encodeURIComponent(urlFile)}`,
      { method: 'POST' }
    );

    if (!res.ok) {
      const errText = await res.text();
      throw new Error(`Server error ${res.status}: ${errText}`);
    }

    analysisResult = await res.json();

    clearInterval(stepInterval);
    allStepsDone();
    document.getElementById('loadingFill').style.width = '100%';
    document.getElementById('loadingStep').textContent = 'Analysis complete ✓';

    // Cache result safely
    try {
      localStorage.setItem('polyphonicAnalysis', JSON.stringify(analysisResult));
      localStorage.setItem('polyphonicFile', urlFile);
    } catch(e) { /* storage not available */ }

    setTimeout(() => {
      document.getElementById('loadingState').style.display = 'none';
      renderResults(analysisResult);
    }, 500);

  } catch (err) {
    clearInterval(stepInterval);
    console.error('[Analysis error]', err);
    document.getElementById('loadingState').style.display = 'none';
    showErrorBanner(err.message);
    btn.disabled = false;
    document.getElementById('runSpinner').style.display = 'none';
    document.getElementById('runBtnText').textContent = '▶ Separate & Analyze';
  }
};

// ── RENDER RESULTS ──
function renderResults(result) {
  const btn = document.getElementById('analyzeBtn');
  btn.disabled = false;
  document.getElementById('runSpinner').style.display = 'none';
  document.getElementById('runBtnText').textContent = '↺ Re-analyze';

  document.getElementById('loadingState').style.display = 'none';

  const ss = document.getElementById('stemsScroll');
  ss.style.display = 'flex';
  ss.style.flexDirection = 'column';
  ss.innerHTML = '';
  audioPlayers = {};

  const stemNames   = Object.keys(result.stems || {});
  const allInstrs   = [];
  Object.values(result.instruments || {}).forEach(arr =>
    arr.forEach(i => { const n = i.instrument || i.instrument_name || ''; if (n) allInstrs.push(n); })
  );
  const uniqueInstrs = [...new Set(allInstrs)];
  const isPiano      = !!result.piano_only;

  // ── Header badges ──
  // ── Header badges ──
  const phRight = document.getElementById('phRight');
  if (phRight) phRight.style.display = 'flex';
  const phStemBadge = document.getElementById('phStemBadge');
  if (phStemBadge) phStemBadge.textContent = stemNames.length + ' stems';
  const phPipelineBadge = document.getElementById('phPipelineBadge');
  if (phPipelineBadge) phPipelineBadge.textContent = isPiano ? 'Piano Pipeline' : 'Multi-Instrument';
  const stemCountBadge = document.getElementById('stemCountBadge');
  if (stemCountBadge) stemCountBadge.textContent = stemNames.length;
  const fcStemCount = document.getElementById('fcStemCount');
  if (fcStemCount) { fcStemCount.style.display = 'inline'; fcStemCount.textContent = stemNames.length + ' STEMS'; }

  // ── Sidebar summary ──
  const sbSummary = document.getElementById('sbSummary');
  if (sbSummary) sbSummary.style.display = 'block';
  const srPipeline = document.getElementById('srPipeline');
  if (srPipeline) srPipeline.textContent = isPiano ? 'Piano' : 'Multi-instr';
  const srStems = document.getElementById('srStems');
  if (srStems) srStems.textContent = stemNames.length + ' stems';
  const srInstrs = document.getElementById('srInstrs');
  // AFTER
  if (srInstrs) srInstrs.innerHTML = uniqueInstrs.slice(0,4).join('<br>') || '—';
  const srNotation = document.getElementById('srNotation');
  if (srNotation) srNotation.textContent = result.musicxml_file ? '✓ Ready' : '—';

  // ── Menu bar export ──
  if (result.musicxml_file) {
    const menuXML = document.getElementById('menuExportXML');
    if (menuXML) { menuXML.style.display = 'inline'; menuXML.onclick = () => window.open(BASE_URL + result.musicxml_file, '_blank'); }
  }

  // ── Pipeline banner ──
  const banner = document.createElement('div');
  banner.className = 'pipeline-banner';
  banner.innerHTML = `
    <div class="pb-icon">${isPiano ? '' : ''}</div>
    <div class="pb-body">
      <div class="pb-title">${isPiano ? 'Piano-Only Pipeline' : 'Multi-Instrument Pipeline'}</div>
      <div class="pb-sub">${isPiano
        ? 'Piano detected as primary source. Single-instrument optimized transcription with left/right hand separation.'
        : 'Multiple instruments detected across stems. Per-stem transcription and ensemble score generation.'
      }</div>
    </div>
    <div class="pb-badge ${isPiano ? 'piano' : 'multi'}">${isPiano ? 'PIANO' : 'ENSEMBLE'}</div>`;
  ss.appendChild(banner);

  // ── Stat strip ──
  const strip = document.createElement('div');
  strip.className = 'stat-strip';
  strip.innerHTML = `
    <div class="stat-box"><div class="stat-val">${stemNames.length}</div><div class="stat-lbl">Stems</div></div>
    <div class="stat-box"><div class="stat-val g">${uniqueInstrs.length}</div><div class="stat-lbl">Instruments</div></div>
    <div class="stat-box"><div class="stat-val a">${isPiano ? 'Piano' : 'Multi'}</div><div class="stat-lbl">Pipeline</div></div>
    <div class="stat-box"><div class="stat-val p">${result.musicxml_file ? 'Yes' : 'No'}</div><div class="stat-lbl">Notation</div></div>`;
  ss.appendChild(strip);

  // ── Stem cards ──
  const sbNav = document.getElementById('sbStemsNav');
  sbNav.innerHTML = '';

  stemNames.forEach((stemName, idx) => {
    const audioUrl    = `${BASE_URL}${result.stems[stemName]}`;
    const instruments = result.instruments?.[stemName] || [];
    const icon        = STEM_ICONS[stemName]  || '🎵';
    const theme       = STEM_COLORS[stemName] || DEFAULT_THEME;

    const card = buildStemCard(stemName, audioUrl, instruments, icon, theme, idx);
    ss.appendChild(card);

    // Sidebar quick-play nav
    const navBtn = document.createElement('div');
    navBtn.className = 'sb-stem-btn';
    navBtn.id = 'sbNav_' + stemName;
    navBtn.innerHTML = `
      <span class="sbs-icon">${icon}</span>
      <span class="sbs-name" style="color:${theme.col}">${stemName}</span>
      <div class="sbs-led"></div>`;
    navBtn.onclick = () => {
      switchInnerTab('stems');
      setTimeout(() => { const p = audioPlayers[stemName]; if (p) p.toggle(); }, 50);
    };
    sbNav.appendChild(navBtn);
  });

  // ── Notation tab ──
  if (result.musicxml_file) {
    const xmlUrl = `${BASE_URL}${result.musicxml_file}`;
    document.getElementById('ntTitle').textContent = isPiano ? ' Piano Sheet Music' : ' Multi-Instrument Score';
    document.getElementById('ntSub').textContent   = '';

    const dlV = document.getElementById('dlXmlView');
    const dlD = document.getElementById('dlXmlDown');
    dlV.href = xmlUrl; dlV.style.display = 'inline-flex';
    dlD.style.display = 'inline-flex';
    dlD.onclick = downloadSheetAsPDF;
    // Hide idle, show container
    document.getElementById('notationIdle').style.display   = 'none';
    const sc = document.getElementById('sheetContainer');
    sc.style.display = 'flex';
    sc.style.flexDirection = 'column';

    // Store URL for lazy rendering
    // Store URL for lazy rendering
    notationXMLUrl = xmlUrl;

    // ✅ If notation tab is already active, render immediately
    if (document.getElementById('tab-notation').classList.contains('active')) {
      setTimeout(() => renderMusicXML(notationXMLUrl), 200);
    }

    // ✅ Setup MIDI player if MIDI file exists
    if (result.midi_file) {
      midiUrl = `${BASE_URL}${result.midi_file}`;
      document.getElementById('playMidiBtn').style.display = 'inline-flex';
      console.log('MIDI URL set:', midiUrl);
    }
  }

  // ── Sargam tab ──
  if (result.sargam_notation) {
    renderSargam(result.sargam_notation);
  }
} // ✅ CLOSE renderResults() function properly




// ── BUILD STEM CARD ──
function buildStemCard(stemName, audioUrl, instruments, icon, theme, idx) {
  const card = document.createElement('div');
  card.className = 'stem-card';
  card.id = 'card_' + stemName;
  card.style.animationDelay = (idx * 90) + 'ms';

  const badgeHtml = instruments.length
    ? instruments.map(i => {
        const name = i.instrument || i.instrument_name || '—';
        const conf = ((i.confidence || 0) * 100).toFixed(0);
        return `<span class="sc-instr">${name} ${conf}%</span>`;
      }).join('')
    : '<span style="font-size:10px;color:var(--muted)">No instrument detected</span>';

  const confHtml = instruments.map(i => {
    const name = i.instrument || i.instrument_name || '—';
    const conf = Math.min(100, ((i.confidence || 0) * 100));
    return `
      <div class="sc-conf-row">
        <span class="scr-name">${name}</span>
        <div class="scr-track"><div class="scr-fill" style="width:${conf.toFixed(0)}%;background:${theme.col}"></div></div>
        <span class="scr-pct">${conf.toFixed(0)}%</span>
      </div>`;
  }).join('');

  card.innerHTML = `
    <div class="sc-head">
      <div class="sc-icon" style="background:${theme.bg};border-color:${theme.border}">${icon}</div>
      <div class="sc-info">
        <div class="sc-name" style="color:${theme.col}">${stemName}</div>
        <div class="sc-badges">${badgeHtml}</div>
      </div>
      <div class="sc-status" id="status_${stemName}">Stopped</div>
    </div>
    ${confHtml ? `<div>${confHtml}</div>` : ''}
    <div class="sc-player">
      <button class="play-btn" id="playBtn_${stemName}" style="background:${theme.col}">▶</button>
      <div class="player-mid">
        <div class="prog-track" id="ptrack_${stemName}">
          <div class="prog-fill" id="pfill_${stemName}" style="background:linear-gradient(90deg,${theme.col},${theme.col}88)"></div>
        </div>
        <div class="time-row">
          <span id="tcur_${stemName}">0:00</span>
          <span id="tdur_${stemName}">—</span>
        </div>
      </div>
      <div class="vol-row">
        <span class="vol-icon">🔊</span>
        <input type="range" class="vol-slider" min="0" max="1" step="0.05" value="1" id="vol_${stemName}">
      </div>
    </div>
    <audio id="audio_${stemName}" src="${audioUrl}" preload="metadata" crossorigin="anonymous"></audio>`;

  setTimeout(() => wirePlayer(stemName, theme.col), 0);
  return card;
}

// ── WIRE AUDIO PLAYER ──
function wirePlayer(stemName) {
  const audio    = document.getElementById('audio_' + stemName);
  const playBtn  = document.getElementById('playBtn_' + stemName);
  const pfill    = document.getElementById('pfill_' + stemName);
  const ptrack   = document.getElementById('ptrack_' + stemName);
  const tcur     = document.getElementById('tcur_' + stemName);
  const tdur     = document.getElementById('tdur_' + stemName);
  const vol      = document.getElementById('vol_' + stemName);
  const card     = document.getElementById('card_' + stemName);
  const statusEl = document.getElementById('status_' + stemName);
  const navBtn   = document.getElementById('sbNav_' + stemName);
  if (!audio) return;

  function fmt(s) {
    if (!isFinite(s)) return '0:00';
    const m = Math.floor(s / 60), sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, '0')}`;
  }

  function pauseAllOthers() {
    Object.entries(audioPlayers).forEach(([k, p]) => {
      if (k !== stemName && !p.audio.paused) p.pause();
    });
  }

  const play   = () => { pauseAllOthers(); audio.play().catch(e => console.warn('Play failed:', e)); };
  const pause  = () => audio.pause();
  const toggle = () => (audio.paused ? play() : pause());

  audioPlayers[stemName] = { audio, play, pause, toggle };

  playBtn.onclick = toggle;

  audio.addEventListener('play', () => {
    playBtn.textContent = '⏸';
    card.classList.add('active');
    statusEl.textContent = 'Playing';
    if (navBtn) navBtn.classList.add('playing');
    currentPlaying = stemName;
  });

  audio.addEventListener('pause', () => {
    playBtn.textContent = '▶';
    card.classList.remove('active');
    statusEl.textContent = audio.ended ? 'Stopped' : 'Paused';
    if (navBtn) navBtn.classList.remove('playing');
    if (currentPlaying === stemName) currentPlaying = null;
  });

  audio.addEventListener('ended', () => {
    playBtn.textContent = '▶';
    card.classList.remove('active');
    statusEl.textContent = 'Stopped';
    pfill.style.width = '0%';
    tcur.textContent = '0:00';
    if (navBtn) navBtn.classList.remove('playing');
  });

  audio.addEventListener('timeupdate', () => {
    if (!audio.duration) return;
    pfill.style.width = ((audio.currentTime / audio.duration) * 100) + '%';
    tcur.textContent  = fmt(audio.currentTime);
  });

  audio.addEventListener('loadedmetadata', () => {
    tdur.textContent = fmt(audio.duration);
  });

  audio.addEventListener('error', (e) => {
    statusEl.textContent = 'Error';
    console.error(`[Audio error] ${stemName}:`, e);
  });

  ptrack.addEventListener('click', e => {
    if (!audio.duration) return;
    const r = ptrack.getBoundingClientRect();
    audio.currentTime = ((e.clientX - r.left) / r.width) * audio.duration;
  });

  vol.addEventListener('input', () => {
    audio.volume = parseFloat(vol.value);
  });
}

// ── MUSICXML RENDER ──
async function renderMusicXML(url) {
  const container = document.getElementById('sheetContainer');
  container.innerHTML = "Rendering notation...";

  try {
    osmdInstance = new opensheetmusicdisplay.OpenSheetMusicDisplay(container, {
      backend: "svg",
      drawingParameters: "compact",
      autoResize: true,
      followCursor: true,          // auto-scroll to keep cursor visible
    });

    await osmdInstance.load(url);
    await osmdInstance.render();

    // ── Initialize cursor ──
    osmdInstance.cursor.show();
    osmdInstance.cursor.reset();

    console.log("OSMD render success");
  } catch (err) {
    console.error("OSMD render error:", err);
    container.innerHTML = "<div style='padding:16px;color:red'>Failed to render notation</div>";
  }
}

// ── SARGAM RENDER ──
const SARGAM_COLORS = {
  'Sa':   '#0096FF',
  'Re♭':  '#2dd4bf', 'Re':  '#2dd4bf',
  'Ga♭':  '#818cf8', 'Ga':  '#818cf8',
  'Ma♯':  '#f59e0b', 'Ma':  '#f59e0b',
  'Pa':   '#22c55e',
  'Dha♭': '#ef4444', 'Dha': '#ef4444',
  'Ni♭':  '#ec4899', 'Ni':  '#ec4899',
};

// Tokenize one line into [{ type:'note'|'bar'|'rest', value, octave }]
function tokenizeSargamLine(line) {
  const tokens = [];
  const parts  = line.trim().split(/\s+/);

  for (const part of parts) {
    if (!part) continue;

    if (part === '|') {
      tokens.push({ type: 'bar' });
      continue;
    }

    // Detect trailing octave markers  '  or  ,  (may be repeated)
    const octaveMatch = part.match(/^(.*?)('+|,+)$/);
    let base   = part;
    let octave = '';
    if (octaveMatch) {
      base   = octaveMatch[1];
      octave = octaveMatch[2];
    }

    // Match against known syllables (longest first)
    const keys = Object.keys(SARGAM_COLORS).sort((a, b) => b.length - a.length);
    const matched = keys.find(k => base === k || base.startsWith(k));

    tokens.push({
      type:   'note',
      value:  base,
      key:    matched || null,
      octave: octave,
    });
  }

  return tokens;
}

function renderSargam(raw) {
  if (!raw || !raw.trim()) return;

  document.getElementById('sargamIdle').style.display    = 'none';
  document.getElementById('sargamContent').style.display = 'block';

  const lines    = raw.split('\n').filter(l => l.trim());
  const measures = (raw.match(/\|/g) || []).length;
  const allTokens = raw.split(/\s+/).filter(w => w && w !== '|');

  // ── Stats ──
  document.getElementById('sargamStats').innerHTML = `
    <div class="stat-box"><div class="stat-val">${allTokens.length}</div><div class="stat-lbl">Syllables</div></div>
    <div class="stat-box"><div class="stat-val g">${measures}</div><div class="stat-lbl">Measures</div></div>
    <div class="stat-box"><div class="stat-val a">${lines.length}</div><div class="stat-lbl">Lines</div></div>
    <div class="stat-box"><div class="stat-val p">Indian</div><div class="stat-lbl">System</div></div>`;

  // ── Render lines ──
  let html = '';
  let lineNum = 1;

  for (const line of lines) {
    if (!line.trim()) continue;

    html += `<div class="sg-line">
      <span class="sg-line-num">${lineNum++}</span>`;

    const tokens = tokenizeSargamLine(line);

    for (const tok of tokens) {
      if (tok.type === 'bar') {
        html += '<span class="sg-bar">│</span>';
        continue;
      }

      const col = tok.key ? SARGAM_COLORS[tok.key] : 'rgba(255,255,255,0.35)';

      // Octave superscript
      const octHtml = tok.octave
        ? `<span class="sg-oct" style="color:${col}">${tok.octave}</span>`
        : '';

      html += `<span class="sg-syllable" style="color:${col};border-bottom-color:${col}40">${tok.value}${octHtml}</span>`;
    }

    html += '</div>';
  }

  document.getElementById('sargamText').innerHTML = html;
}

// ── RESTORE FROM CACHE ──
// ── RESTORE FROM CACHE ──
(function tryRestore() {
  try {
    // DEV: always clear cache so fresh HTML changes take effect
    localStorage.removeItem('polyphonicAnalysis');
    localStorage.removeItem('polyphonicFile');

    const cachedFile = localStorage.getItem('polyphonicFile');
    if (urlFile && cachedFile && cachedFile !== urlFile) {
      localStorage.removeItem('polyphonicAnalysis');
      localStorage.removeItem('polyphonicFile');
      return;
    }
    const raw = localStorage.getItem('polyphonicAnalysis');
    if (!raw) return;
    const cached = JSON.parse(raw);
    if (!cached || !cached.stems) return;

    analysisResult = cached;
    allStepsDone();
    document.getElementById('idleState').style.display = 'none';
    renderResults(cached);
  } catch(e) {
    console.warn('[Cache restore skipped]', e.message);
  }
})();

// ── MIDI PLAYBACK ──
// ── CURSOR SYNC STATE ──
let cursorAnimFrame   = null;
let cursorNoteTimings = []; // [{timeSeconds, iterator}] built at load time
let midiStartTime     = null;

function buildCursorTimings(midi) {
  // Build a flat list of { time } from all MIDI notes, deduplicated and sorted
  const times = new Set();
  midi.tracks.forEach(track => {
    track.notes.forEach(note => {
      times.add(parseFloat(note.time.toFixed(3)));
    });
  });
  return [...times].sort((a, b) => a - b);
}

function stopCursorSync() {
  if (cursorAnimFrame) {
    cancelAnimationFrame(cursorAnimFrame);
    cursorAnimFrame = null;
  }
}

function resetCursor() {
  if (osmdInstance && osmdInstance.cursor) {
    osmdInstance.cursor.reset();
    osmdInstance.cursor.show();
  }
}

function hideCursor() {
  if (osmdInstance && osmdInstance.cursor) {
    osmdInstance.cursor.hide();
  }
}

// Highlight the cursor element with a glow effect
function styleCursor() {
  // OSMD renders cursor as an SVG rect — find and style it
  const container = document.getElementById('sheetContainer');
  const cursors = container.querySelectorAll('.osmd-cursor, [class*="cursor"]');
  cursors.forEach(el => {
    el.style.opacity = '0.75';
    el.style.fill = '#0096FF';
    el.style.filter = 'drop-shadow(0 0 6px #0096FF)';
  });
  // Also try SVG rect approach
  const rects = container.querySelectorAll('svg rect[fill]');
  rects.forEach(r => {
    const fill = r.getAttribute('fill');
    if (fill && (fill.includes('blue') || fill.includes('#'))) {
      r.setAttribute('fill', '#0096FF');
      r.style.filter = 'drop-shadow(0 0 8px rgba(0,150,255,0.8))';
      r.style.opacity = '0.6';
    }
  });
}

document.getElementById("playMidiBtn").onclick = async () => {
  if (!midiUrl) {
    alert('MIDI file not available');
    return;
  }

  const btn = document.getElementById("playMidiBtn");

  // ── STOP if already playing ──
  if (midiPlayer && Tone.Transport.state === 'started') {
    Tone.Transport.stop();
    Tone.Transport.cancel();
    stopCursorSync();
    resetCursor();
    btn.textContent = '▶ Play Score';
    midiPlayer = null;
    return;
  }

  try {
    btn.textContent = 'Loading...';
    btn.disabled = true;

    // ── Ensure notation tab is visible and OSMD is rendered ──
    if (!osmdInstance && notationXMLUrl) {
      switchInnerTab('notation');
      await new Promise(r => setTimeout(r, 1800));
    }
    // Switch to notation tab so cursor is visible
    switchInnerTab('notation');

    const response = await fetch(midiUrl);
    if (!response.ok) throw new Error(`Failed to load MIDI: ${response.status}`);

    const arrayBuffer = await response.arrayBuffer();
    const midi = new Midi(arrayBuffer);

    await Tone.start();
    Tone.Transport.cancel();

    // ── Build note timings for cursor sync ──
    const noteTimings = buildCursorTimings(midi);

    // ── Reset cursor to start ──
    if (osmdInstance && osmdInstance.cursor) {
      osmdInstance.cursor.reset();
      osmdInstance.cursor.show();
      styleCursor();
    }

    // ── Schedule all synth notes ──
    midiPlayer = [];
    midi.tracks.forEach(track => {
      if (!track.notes.length) return;
      const synth = new Tone.PolySynth(Tone.Synth, {
        oscillator: { type: 'triangle' },
        envelope: { attack: 0.02, decay: 0.1, sustain: 0.5, release: 0.8 }
      }).toDestination();
      synth.volume.value = -6;

      track.notes.forEach(note => {
        Tone.Transport.schedule(time => {
          synth.triggerAttackRelease(note.name, note.duration, time, note.velocity);
        }, note.time);
      });
      midiPlayer.push(synth);
    });

    // ── Schedule cursor advances at each unique note onset ──
    if (osmdInstance && osmdInstance.cursor) {
      noteTimings.forEach((t, idx) => {
        Tone.Transport.schedule(() => {
          // Must run on next animation frame to safely touch DOM
          requestAnimationFrame(() => {
            if (!osmdInstance || !osmdInstance.cursor) return;
            try {
              if (idx === 0) {
                osmdInstance.cursor.reset();
              } else {
                osmdInstance.cursor.next();
              }
              styleCursor();

              // Auto-scroll sheetContainer to keep cursor in view
              const container = document.getElementById('sheetContainer');
              const cursorEl  = container.querySelector('.osmd-cursor-img, [class*="cursor"] image, svg image');
              if (cursorEl) {
                const rect = cursorEl.getBoundingClientRect();
                const cRect = container.getBoundingClientRect();
                if (rect.bottom > cRect.bottom - 40 || rect.top < cRect.top + 40) {
                  container.scrollBy({ top: rect.height * 2, behavior: 'smooth' });
                }
              }
            } catch(e) { /* cursor may be at end */ }
          });
        }, t);
      });
    }

    // ── Get total duration ──
    const duration = Math.max(...midi.tracks.map(t =>
      t.notes.length ? Math.max(...t.notes.map(n => n.time + n.duration)) : 0
    ));

    Tone.Transport.start();
    btn.textContent = '⏸ Stop';
    btn.disabled = false;

    // ── Auto-stop when done ──
    setTimeout(() => {
      if (Tone.Transport.state === 'started') {
        Tone.Transport.stop();
        Tone.Transport.cancel();
        stopCursorSync();
        btn.textContent = '▶ Play Score';
        midiPlayer = null;
        // Leave cursor at last position — reset on next play
      }
    }, duration * 1000 + 800);

  } catch (error) {
    console.error('MIDI playback error:', error);
    alert('Error playing MIDI: ' + error.message);
    btn.textContent = '▶ Play Score';
    btn.disabled = false;
  }
};

async function downloadSheetAsPDF() {
  // Auto-render sheet if not yet visited
  if (!osmdInstance && notationXMLUrl) {
    switchInnerTab('notation');
    await new Promise(r => setTimeout(r, 1800));
  }

  const container = document.getElementById('sheetContainer');
  const svgs = container.querySelectorAll('svg');

  if (!svgs.length) {
    alert('Please open the Sheet Music Notation tab first so it renders, then download.');
    return;
  }

  const btn = document.getElementById('dlXmlDown');
  btn.textContent = '⏳ Generating…';
  btn.disabled = true;

  try {
    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });

    const pageW    = 210;
    const pageH    = 297;
    const margin   = 12;
    const usableW  = pageW - margin * 2;
    const usableH  = pageH - margin * 2;

    let yOffset  = margin;
    let firstPage = true;

    for (let i = 0; i < svgs.length; i++) {
      const svg = svgs[i];

      // ── Get real SVG dimensions ──
      let svgW, svgH;
      const vb = svg.getAttribute('viewBox');
      if (vb) {
        const parts = vb.split(/[\s,]+/);
        svgW = parseFloat(parts[2]);
        svgH = parseFloat(parts[3]);
      } else {
        const bb = svg.getBoundingClientRect();
        svgW = bb.width  || svg.width?.baseVal?.value  || 800;
        svgH = bb.height || svg.height?.baseVal?.value || 400;
      }
      if (!svgW || !svgH) continue;

      // ── Render SVG to a high-DPI canvas ──
      const cloned = svg.cloneNode(true);
      cloned.setAttribute('width',  svgW);
      cloned.setAttribute('height', svgH);
      cloned.setAttribute('xmlns', 'http://www.w3.org/2000/svg');

      const svgData = new XMLSerializer().serializeToString(cloned);
      const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
      const svgUrl  = URL.createObjectURL(svgBlob);

      // Draw full SVG onto one big canvas
      const canvas = await new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => {
          const scale = 3;
          const c = document.createElement('canvas');
          c.width  = svgW * scale;
          c.height = svgH * scale;
          const ctx = c.getContext('2d');
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(0, 0, c.width, c.height);
          ctx.scale(scale, scale);
          ctx.drawImage(img, 0, 0, svgW, svgH);
          URL.revokeObjectURL(svgUrl);
          resolve(c);
        };
        img.onerror = (e) => { URL.revokeObjectURL(svgUrl); reject(e); };
        img.src = svgUrl;
      });

      // ── Total rendered height in mm ──
      const aspectRatio  = svgH / svgW;
      const totalImgH_mm = usableW * aspectRatio;

      // ── How many px in the canvas = 1 mm of PDF ──
      const pxPerMm = canvas.height / totalImgH_mm;

      // ── Slice the canvas into page-height strips ──
      let srcYpx = 0; // current read position in canvas pixels

      while (srcYpx < canvas.height) {

        // How much vertical space is left on the current page (mm)?
        const spaceLeft_mm = pageH - yOffset - margin;

        // How tall a strip can we fit? (mm → px)
        const stripH_mm  = Math.min(spaceLeft_mm, usableH);
        const stripH_px  = Math.round(stripH_mm * pxPerMm);

        if (stripH_px <= 0) {
          // No space at all — force new page
          pdf.addPage();
          yOffset = margin;
          continue;
        }

        // Clamp to remaining canvas height
        const actualStripH_px = Math.min(stripH_px, canvas.height - srcYpx);
        const actualStripH_mm = actualStripH_px / pxPerMm;

        // Cut the strip out of the canvas
        const strip = document.createElement('canvas');
        strip.width  = canvas.width;
        strip.height = actualStripH_px;
        const sctx = strip.getContext('2d');
        sctx.fillStyle = '#ffffff';
        sctx.fillRect(0, 0, strip.width, strip.height);
        sctx.drawImage(canvas,
          0, srcYpx,                    // source x, y
          canvas.width, actualStripH_px, // source w, h
          0, 0,                          // dest x, y
          strip.width, actualStripH_px   // dest w, h
        );

        // Add new page if not the very first placement
        if (!firstPage && spaceLeft_mm < 10) {
          pdf.addPage();
          yOffset = margin;
        }

        pdf.addImage(
          strip.toDataURL('image/png'),
          'PNG',
          margin, yOffset,
          usableW, actualStripH_mm
        );

        yOffset   += actualStripH_mm + 2;
        srcYpx    += actualStripH_px;
        firstPage  = false;

        // If we still have more canvas to render, add a new page
        if (srcYpx < canvas.height) {
          pdf.addPage();
          yOffset = margin;
        }
      }
    }

    const filename = (document.getElementById('sideFileName').textContent || 'score')
      .replace(/\.[^.]+$/, '');
    pdf.save(`${filename}_sheet_music.pdf`);

  } catch (err) {
    console.error('PDF generation error:', err);
    alert('PDF generation failed: ' + err.message);
  } finally {
    btn.textContent = '⬇ Download PDF';
    btn.disabled = false;
  }
}

async function downloadSargamAsPDF() {
  const btn = document.getElementById('dlSargamPdf');
  btn.textContent = '⏳ Generating…';
  btn.disabled = true;

  try {
    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });

    const pageW   = 210;
    const pageH   = 297;
    const margin  = 12;
    const usableW = pageW - margin * 2;
    const usableH = pageH - margin * 2;

    // ── Capture the full sargam card as a canvas ──
    const target = document.getElementById('sargamContent');

    const canvas = await html2canvas(target, {
      backgroundColor: '#0a0a2e',   // match your sargam-card bg
      scale: 2,                      // 2x for crisp text
      useCORS: true,
      logging: false,
      windowWidth: target.scrollWidth,
      windowHeight: target.scrollHeight
    });

    // ── mm per canvas pixel ──
    const totalH_mm  = usableW * (canvas.height / canvas.width);
    const pxPerMm    = canvas.height / totalH_mm;

    let yOffset   = margin;
    let srcYpx    = 0;
    let firstPage = true;

    // ── Add title header on first page ──
    const filename = (document.getElementById('sideFileName').textContent || 'score')
      .replace(/\.[^.]+$/, '');

    pdf.setFontSize(14);
    pdf.setTextColor(30, 30, 30);
    pdf.text('Sargam Notation — ' + filename, margin, yOffset);
    yOffset += 7;

    pdf.setFontSize(9);
    pdf.setTextColor(120, 120, 120);
    pdf.text('Sa Re Ga Ma Pa Dha Ni  ·  Indian Classical System', margin, yOffset);
    yOffset += 8;

    // ── Slice canvas into page-height strips ──
    while (srcYpx < canvas.height) {

      const spaceLeft_mm = pageH - yOffset - margin;
      const stripH_mm    = Math.min(spaceLeft_mm, usableH);
      const stripH_px    = Math.round(stripH_mm * pxPerMm);

      if (stripH_px <= 0) {
        pdf.addPage();
        yOffset = margin;
        continue;
      }

      const actualStripH_px = Math.min(stripH_px, canvas.height - srcYpx);
      const actualStripH_mm = actualStripH_px / pxPerMm;

      // Cut strip
      const strip = document.createElement('canvas');
      strip.width  = canvas.width;
      strip.height = actualStripH_px;
      const sctx = strip.getContext('2d');
      sctx.fillStyle = '#0a0a2e';
      sctx.fillRect(0, 0, strip.width, strip.height);
      sctx.drawImage(canvas,
        0, srcYpx,
        canvas.width, actualStripH_px,
        0, 0,
        strip.width, actualStripH_px
      );

      if (!firstPage && spaceLeft_mm < 10) {
        pdf.addPage();
        yOffset = margin;
      }

      pdf.addImage(
        strip.toDataURL('image/png'),
        'PNG',
        margin, yOffset,
        usableW, actualStripH_mm
      );

      yOffset   += actualStripH_mm + 2;
      srcYpx    += actualStripH_px;
      firstPage  = false;

      if (srcYpx < canvas.height) {
        pdf.addPage();
        yOffset = margin;
      }
    }

    pdf.save(`${filename}_sargam_notation.pdf`);

  } catch (err) {
    console.error('Sargam PDF error:', err);
    alert('PDF generation failed: ' + err.message);
  } finally {
    btn.textContent = '⬇ Download PDF';
    btn.disabled = false;
  }
}

// Wire the button once DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('dlSargamPdf');
  if (btn) btn.onclick = downloadSargamAsPDF;
});