//frontend/js/index.js

const LS_KEY = 'notescribe_last_result';
let currentFile = null;
let detectedResult = null;

const audioFileInput = document.getElementById('audioFile');
const dropZone       = document.getElementById('dropZone');
const analyzeBtn     = document.getElementById('analyzeBtn');
const fileLoaded     = document.getElementById('fileLoaded');

dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => {
  e.preventDefault(); dropZone.classList.remove('drag-over');
  const f = e.dataTransfer.files[0];
  if (f) selectFile(f);
});
audioFileInput.addEventListener('change', e => { if (e.target.files[0]) selectFile(e.target.files[0]); });

function selectFile(file) {
  currentFile = file;
  analyzeBtn.disabled = false;
  setWf(1);
  fileLoaded.style.display = 'block';
  document.getElementById('flName').textContent = file.name;
  document.getElementById('flMeta').textContent = (file.size / (1024*1024)).toFixed(2) + ' MB · ' + file.type;
  document.getElementById('idleState').style.display = 'flex';
  document.getElementById('resultPanel').style.display = 'none';
  document.getElementById('phBadge').style.display = 'none';
}

function setWf(active) {
  for (let i = 1; i <= 4; i++) {
    const el = document.getElementById('wf' + i);
    el.classList.remove('active', 'done');
    if (i < active) el.classList.add('done');
    else if (i === active) el.classList.add('active');
  }
}

function setProgress(active) {
  const msgs = ['Uploading file…', 'Reading audio signal…', 'Detecting audio type…'];
  for (let i = 1; i <= 3; i++) {
    const card = document.getElementById('pc' + i);
    const bar  = document.getElementById('pb' + i);
    card.classList.remove('running', 'done');
    if (i < active) { card.classList.add('done'); bar.style.width = '100%'; }
    else if (i === active) {
      card.classList.add('running');
      setTimeout(() => { bar.style.width = '75%'; }, 100);
      document.getElementById('progSub').textContent = msgs[i - 1];
    } else { bar.style.width = '0%'; }
  }
}

analyzeBtn.onclick = async () => {
  if (!currentFile) return;
  const formData = new FormData();
  formData.append('file', currentFile);

  document.getElementById('idleState').style.display    = 'none';
  document.getElementById('resultPanel').style.display  = 'none';
  const pp = document.getElementById('progressPanel');
  pp.style.display = 'flex'; pp.style.flexDirection = 'column';
  analyzeBtn.disabled = true;
  setWf(2); setProgress(1);
  setTimeout(() => { document.getElementById('pb1').style.width = '100%'; }, 150);
  setTimeout(() => { setProgress(2); setWf(3); }, 1000);
  setTimeout(() => { setProgress(3); setWf(4); }, 2100);

  try {
    const res = await fetch('http://127.0.0.1:8000/upload/', { method: 'POST', body: formData });
    if (!res.ok) throw new Error(await res.text());
    const result = await res.json();
    detectedResult = result;

    setTimeout(() => {
      document.getElementById('pc3').classList.add('done');
      document.getElementById('pc3').classList.remove('running');
      document.getElementById('pb3').style.width = '100%';

      localStorage.setItem(LS_KEY, JSON.stringify({
        filename: result.filename, type: result.type,
        confidence: result.confidence, timestamp: Date.now()
      }));

      setTimeout(() => {
        pp.style.display = 'none';
        showResult(result);
        updateNavTabs(result.type, result.filename);
      }, 500);
    }, 1200);

  } catch (err) {
    console.error(err);
    alert('Upload error: ' + err.message);
    document.getElementById('progressPanel').style.display = 'none';
    document.getElementById('idleState').style.display = 'flex';
    analyzeBtn.disabled = false;
    setWf(1);
  }
};

function showResult(result) {
  const isMono = result.type === 'monophonic';
  const pct = (result.confidence * 100).toFixed(1);

  document.getElementById('rhName').textContent = result.filename;
  document.getElementById('rhInfo').textContent = `Analyzed · ${isMono ? 'Monophonic' : 'Polyphonic'} · ${pct}% confidence`;
  const rhBadge = document.getElementById('rhBadge');
  rhBadge.textContent = isMono ? 'MONOPHONIC' : 'POLYPHONIC';
  rhBadge.className = 'rh-badge ' + (isMono ? 'mono' : 'poly');

  const phBadge = document.getElementById('phBadge');
  phBadge.textContent = isMono ? 'MONOPHONIC' : 'POLYPHONIC';
  phBadge.className = 'ph-badge ' + (isMono ? 'mono' : 'poly');
  phBadge.style.display = 'inline-block';

  document.getElementById('typeIcon').textContent = isMono ? '🎵' : '🎹';
  document.getElementById('typeName').textContent = isMono ? 'Monophonic' : 'Polyphonic';
  document.getElementById('typeSub').textContent  = isMono ? 'Single melody line' : 'Multi-layer voices';
  document.getElementById('typeDesc').textContent = isMono
    ? 'A single note sounds at any given moment, only one pitch plays at a time. Ideal for solo instruments such as flute, violin, trumpet, cello, clarinet, or unaccompanied vocal lines. This makes pitch and timing detection highly reliable, producing clean, accurate notation with minimal errors.'
    : 'Multiple notes and voices sound simultaneously across one or more instruments. Each voice is carefully separated and analysed independently - covering piano chords, guitar strumming, string ensembles, or full band recordings before being combined into a complete, layered score.';
  document.getElementById('statType').textContent = isMono ? 'MONO' : 'POLY';
  document.getElementById('statConf').textContent = pct + '%';
  document.getElementById('statPipe').textContent = isMono ? 'Solo' : 'Multi';

  document.getElementById('confBig').textContent = pct + '%';
  setTimeout(() => { document.getElementById('confFill').style.width = pct + '%'; }, 100);
  const confNum = parseFloat(pct);
  document.getElementById('tier1').classList.toggle('active', confNum >= 80);
  document.getElementById('tier2').classList.toggle('active', confNum >= 50 && confNum < 80);
  document.getElementById('tier3').classList.toggle('active', confNum < 50);

  document.getElementById('piTitle').textContent = isMono ? 'Monophonic Analysis' : 'Polyphonic Analysis';
  document.getElementById('piDesc').textContent  = isMono
    ? 'Extracts individual note pitches, durations, tempo and key signature to produce a clean single-staff score.'
    : 'Separates audio into individual instrument voices, then analyses each independently before combining into a full score.';

  const steps = isMono
    ? ['Pitch Detection', 'Tempo & Beat Detection', 'Key Signature Detection', 'Sheet Music Generation']
    : ['Audio Separation', 'Instrument Detection', 'Voice Transcription', 'Score Construction'];
  document.getElementById('piSteps').innerHTML = steps.map((s, i) =>
    `<div class="pi-step"><div class="pi-step-num">${i+1}</div>${s}</div>`
  ).join('');

  const tags = isMono
    ? ['Pitch Tracking', 'Tempo', 'Key Detection', 'Notation']
    : ['Separation', 'Multi-Instrument', 'Transcription', 'Score'];
  document.getElementById('piTags').innerHTML = tags.map(t => `<span class="pi-tag">${t}</span>`).join('');

  ['rn0','rn1','rn2'].forEach(id => {
    document.getElementById(id).classList.add('highlight');
  });
  const rn3 = document.getElementById('rn3');
  rn3.classList.add(isMono ? 'highlight' : 'highlight-amber');
  document.getElementById('rnDestIcon').textContent = isMono ? '🎵' : '🎼';
  document.getElementById('rnDestName').textContent = isMono ? 'Monophonic Analysis' : 'Polyphonic Analysis';
  document.getElementById('rn4').classList.add('highlight');

  document.getElementById('sicStatus').textContent = '✓ Done';
  document.getElementById('sicStatus').style.color = 'var(--green)';
  document.getElementById('sicType').textContent   = isMono ? 'Monophonic' : 'Polyphonic';
  document.getElementById('sicConf').textContent   = pct + '%';
  document.getElementById('sicFile').textContent   = result.filename;

  const rp = document.getElementById('resultPanel');
  rp.style.display = 'flex'; rp.style.flexDirection = 'column';
  analyzeBtn.disabled = false;
}

function updateNavTabs(type, filename) {
  const isMono = type === 'monophonic';
  const step2  = document.getElementById('navStep2');
  const step3  = document.getElementById('navStep3');
  if (isMono) {
    step2.href = 'monophonic.html?file=' + encodeURIComponent(filename);
    step2.classList.remove('locked'); step2.style.pointerEvents = ''; step2.style.opacity = '1';
    step3.classList.add('locked');    step3.style.pointerEvents = 'none'; step3.style.opacity = '.35';
  } else {
    step3.href = 'polyphonic.html?file=' + encodeURIComponent(filename);
    step3.classList.remove('locked'); step3.style.pointerEvents = ''; step3.style.opacity = '1';
    step2.classList.add('locked');    step2.style.pointerEvents = 'none'; step2.style.opacity = '.35';
  }
}

document.getElementById('proceedBtn').onclick = () => {
  const saved = getSaved();
  if (!saved) return;
  const dest = saved.type === 'monophonic' ? 'monophonic.html' : 'polyphonic.html';
  window.location.href = dest + '?file=' + encodeURIComponent(saved.filename);
};
document.getElementById('newFileBtn').onclick = () => clearSession();

function clearSession() {
  localStorage.removeItem(LS_KEY);
  currentFile = null; detectedResult = null;
  audioFileInput.value = '';
  fileLoaded.style.display = 'none';
  analyzeBtn.disabled = true;
  document.getElementById('resultPanel').style.display = 'none';
  document.getElementById('idleState').style.display   = 'flex';
  document.getElementById('phBadge').style.display     = 'none';
  setWf(0);
  ['navStep2','navStep3'].forEach(id => {
    const el = document.getElementById(id);
    el.classList.add('locked'); el.style.pointerEvents = 'none'; el.style.opacity = '.35';
  });
  document.getElementById('sicStatus').textContent = '—';
  document.getElementById('sicStatus').style.color = '';
  document.getElementById('sicType').textContent   = '—';
  document.getElementById('sicConf').textContent   = '—';
  document.getElementById('sicFile').textContent   = '—';
}

function getSaved() {
  try { return JSON.parse(localStorage.getItem(LS_KEY)); } catch { return null; }
}

(function restoreFromStorage() {
  const saved = getSaved();
  if (!saved || !saved.filename) return;
  detectedResult = saved;
  showResult({ filename: saved.filename, type: saved.type, confidence: saved.confidence });
  const ago = timeSince(saved.timestamp);
  document.getElementById('rhInfo').textContent = `Last session · ${saved.type} · ${ago}`;
  updateNavTabs(saved.type, saved.filename);
  analyzeBtn.disabled = false;
  setWf(4);
  document.getElementById('idleState').style.display = 'none';
  fileLoaded.style.display = 'block';
  document.getElementById('flName').textContent = saved.filename;
  document.getElementById('flMeta').textContent = `Cached · ${saved.type}`;
})();

function timeSince(ts) {
  if (!ts) return 'previously';
  const mins = Math.floor((Date.now() - ts) / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return mins + ' min ago';
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return hrs + 'h ago';
  return Math.floor(hrs / 24) + 'd ago';
}