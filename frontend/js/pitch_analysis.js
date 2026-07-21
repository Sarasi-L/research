//frontend/js/pitch_analysis.js

const data = (() => { try { return JSON.parse(localStorage.getItem('monophonicAnalysis')); } catch { return null; } })();
const urlFile = (new URLSearchParams(location.search)).get('file');
let allNotes = [];
let currentFilter = 'all';

function goBack() {
  window.location.href = 'monophonic.html' + (urlFile ? '?file=' + encodeURIComponent(urlFile) : '');
}

function switchView(name) {
  ['contour','notes','roll'].forEach((v,i) => {
    document.getElementById('view-'+v).classList.toggle('active', v===name);
    document.getElementById('stab'+(i+1)).classList.toggle('active', v===name);
  });
  if (name==='roll' && data) setTimeout(renderPianoRoll, 30);
  if (name==='contour') setTimeout(() => Plotly.Plots.resize('pitchChart'), 20);
}

function filterNotes(type) {
  currentFilter = type;
  ['fAll','fNotes','fRests'].forEach(id => document.getElementById(id).classList.remove('active'));
  document.getElementById({all:'fAll',notes:'fNotes',rests:'fRests'}[type]).classList.add('active');
  renderNoteCards(allNotes, type);
}

function noteToMidi(note) {
  if (!note || note==='Rest') return null;
  const names = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];
  const m = note.match(/^([A-G]#?)(\d+)$/);
  if (!m) return null;
  const pc = names.indexOf(m[1]);
  return pc < 0 ? null : pc + (parseInt(m[2])+1)*12;
}

if (!data) {
  document.getElementById('noData').style.display = 'flex';
  document.querySelectorAll('.view-content').forEach(v => v.style.display='none');
  document.querySelector('.sub-tabs').style.display = 'none';
} else {
  buildAll(data);
}

function buildAll(data) {
  allNotes = data.note_segments || [];
  const pitchData = (data.pitch_curve || []).filter(p => p.frequency > 0);
  const noteOnly = allNotes.filter(n => !n.is_rest);
  const totalDur = allNotes.reduce((s,n) => s+(n.end-n.start), 0);
  const uniqueNotes = new Set(noteOnly.map(n => n.note)).size;
  const maxF = pitchData.length ? Math.max(...pitchData.map(p=>p.frequency)) : 0;
  const minF = pitchData.length ? Math.min(...pitchData.map(p=>p.frequency)) : 0;

  document.getElementById('phFile').textContent = urlFile || (data.instrument?.instrument || 'Analysis');
  document.getElementById('sumInstr').textContent = (data.instrument?.instrument||'—').toUpperCase();
  document.getElementById('sumKey').textContent = (data.key?.key||'—')+' '+(data.key?.mode||'');
  document.getElementById('sumTempo').textContent = (data.tempo?.tempo?.toFixed(0)||'—')+' BPM';
  document.getElementById('sumTime').textContent = data.beats_per_measure+'/4';
  document.getElementById('sumNotes').textContent = allNotes.length;

  document.getElementById('statsBar').innerHTML = `
    <div class="sb-cell"><div class="sbc-val">${allNotes.length}</div><div class="sbc-lbl">Total Events</div></div>
    <div class="sb-cell"><div class="sbc-val g">${noteOnly.length}</div><div class="sbc-lbl">Note Events</div></div>
    <div class="sb-cell"><div class="sbc-val a">${uniqueNotes}</div><div class="sbc-lbl">Unique Pitches</div></div>
    <div class="sb-cell"><div class="sbc-val p">${totalDur.toFixed(1)}s</div><div class="sbc-lbl">Total Duration</div></div>
    <div class="sb-cell"><div class="sbc-val c">${pitchData.length}</div><div class="sbc-lbl">Voiced Frames</div></div>`;

  document.getElementById('legendFrames').textContent = `${pitchData.length} frames · ${minF.toFixed(0)}–${maxF.toFixed(0)} Hz · pYIN`;
  document.getElementById('ntInfo').textContent = `${allNotes.length} events · ${noteOnly.length} notes · ${allNotes.length-noteOnly.length} rests`;

  // Sidebar note distribution
  const freq = {};
  noteOnly.forEach(n => { freq[n.note]=(freq[n.note]||0)+1; });
  const sorted = Object.entries(freq).sort((a,b)=>b[1]-a[1]).slice(0,12);
  const maxCount = sorted[0]?.[1]||1;
  const distColors = ['#0096FF','#38b6ff','#2dd4bf','#818cf8','#f59e0b','#22c55e','#ec4899'];
  document.getElementById('noteDistChart').innerHTML = sorted.map(([note,count],i) => `
    <div class="nd-row">
      <div class="nd-note">${note}</div>
      <div class="nd-track"><div class="nd-fill" style="width:${(count/maxCount*100).toFixed(0)}%;background:${distColors[i%distColors.length]}"></div></div>
      <div class="nd-count">${count}</div>
    </div>`).join('');

  // Freq ruler
  const noteFreqs=[
    {n:'C3',f:130.8},{n:'D3',f:146.8},{n:'E3',f:164.8},{n:'F3',f:174.6},
    {n:'G3',f:196},{n:'A3',f:220},{n:'B3',f:246.9},{n:'C4',f:261.6},
    {n:'D4',f:293.7},{n:'E4',f:329.6},{n:'F4',f:349.2},{n:'G4',f:392},
    {n:'A4',f:440},{n:'B4',f:493.9},{n:'C5',f:523.3},{n:'D5',f:587.3},
    {n:'E5',f:659.3},{n:'F5',f:698.5},{n:'G5',f:784},{n:'A5',f:880}
  ];
  document.getElementById('freqRuler').innerHTML = noteFreqs.map((nf,i) =>
    (i>0?'<div class="fr-sep"></div>':'')+
    `<div class="fr-item"><div class="fr-note">${nf.n}</div><div class="fr-freq">${nf.f}Hz</div></div>`
  ).join('');

  // ── PLOTLY PITCH CONTOUR ──
  const times = pitchData.map(p=>p.time);
  const freqs = pitchData.map(p=>p.frequency);
  const onsetShapes = allNotes.filter(n=>!n.is_rest).map(n=>({
    type:'line', x0:n.start, x1:n.start, yref:'paper', y0:0, y1:1,
    line:{color:'rgba(34,197,94,0.22)',width:1,dash:'dot'}
  }));

  Plotly.newPlot('pitchChart', [{
    x: times, y: freqs,
    mode: 'lines',
    name: 'F0 (Hz)',
    fill: 'tozeroy',
    fillcolor: 'rgba(0,150,255,0.07)',
    line: { color: '#0096FF', width: 2 },
    hovertemplate: 't = %{x:.3f}s<br>F0 = %{y:.1f} Hz<extra></extra>'
  }], {
    shapes: onsetShapes,
    xaxis:{
      title:'Time (seconds)',
      titlefont:{color:'rgba(255,255,255,.28)',size:10,family:'JetBrains Mono'},
      tickfont:{color:'rgba(255,255,255,.4)',size:10,family:'JetBrains Mono'},
      gridcolor:'rgba(0,150,255,.08)',
      zerolinecolor:'rgba(0,150,255,.15)',
      linecolor:'rgba(0,150,255,.2)'
    },
    yaxis:{
      title:'Frequency (Hz)',
      titlefont:{color:'rgba(255,255,255,.28)',size:10,family:'JetBrains Mono'},
      tickfont:{color:'rgba(255,255,255,.4)',size:10,family:'JetBrains Mono'},
      gridcolor:'rgba(0,150,255,.08)',
      zerolinecolor:'rgba(0,150,255,.15)',
      linecolor:'rgba(0,150,255,.2)'
    },
    paper_bgcolor:'rgba(0,0,0,0)',
    plot_bgcolor:'rgba(0,0,0,0)',
    margin:{t:14,b:48,l:56,r:16},
    font:{family:'JetBrains Mono,monospace',color:'rgba(255,255,255,.4)'},
    showlegend:false,
    hovermode:'x unified',
    hoverlabel:{
      bgcolor:'rgba(7,7,46,.95)',
      bordercolor:'rgba(0,150,255,.45)',
      font:{color:'#38b6ff',size:11,family:'JetBrains Mono'}
    }
  }, {responsive:true, displayModeBar:false});

  renderNoteCards(allNotes, 'all');
}

// ── NOTE CARDS ──
const CARD_COLORS = ['#0096FF','#38b6ff','#2dd4bf','#818cf8','#f59e0b','#22c55e','#ec4899','#fb923c'];

function renderNoteCards(notes, filter) {
  const filtered = notes.filter(n => {
    if (filter==='notes') return !n.is_rest;
    if (filter==='rests') return n.is_rest;
    return true;
  });
  const maxDur = Math.max(...notes.map(n=>n.end-n.start), 0.001);
  const grid = document.getElementById('notesGrid');
  grid.innerHTML = '';

  filtered.forEach((n, i) => {
    const dur = n.end - n.start;
    const noteName = n.is_rest ? 'Rest' : (n.note||'—');
    const midi = noteToMidi(noteName);
    const octave = midi!==null ? `Oct ${Math.floor(midi/12)-1}` : '';
    const barPct = (dur/maxDur*100).toFixed(0);
    const col = n.is_rest ? 'rgba(255,255,255,.15)' : CARD_COLORS[i%CARD_COLORS.length];
    const delay = Math.min(i*15, 500);

    const card = document.createElement('div');
    card.className = 'note-card ' + (n.is_rest?'is-rest':'is-note');
    card.style.animationDelay = delay+'ms';
    if (!n.is_rest) {
      card.style.borderColor = col+'44';
      card.style.setProperty('--nc-col', col);
    }
    card.innerHTML = `
      <style>.note-card.is-note:nth-child(${i+1})::before{background:${col}}</style>
      <div class="nc-top">
        <div class="nc-name${n.is_rest?' rest':''}" style="${n.is_rest?'':'color:'+col}">${noteName}</div>
        <span class="nc-chip ${n.is_rest?'rest':'note'}">${n.is_rest?'REST':'NOTE'}</span>
      </div>
      <div class="nc-octave">${octave||'&nbsp;'}</div>
      <div class="nc-dur-row">
        <div class="nc-dur-track">
          <div class="nc-dur-fill" style="width:${barPct}%;background:${n.is_rest?'rgba(255,255,255,.1)':col}"></div>
        </div>
      </div>
      <div class="nc-timing">
        <div class="nc-t">
          <div class="nc-t-lbl">Start</div>
          <div class="nc-t-val">${n.start.toFixed(2)}s</div>
        </div>
        <div class="nc-t" style="text-align:right">
          <div class="nc-t-lbl">Dur</div>
          <div class="nc-t-val">${dur.toFixed(2)}s</div>
        </div>
      </div>
      <div class="nc-idx">#${i+1}</div>`;
    grid.appendChild(card);
  });
}

// ── PIANO ROLL ──
function renderPianoRoll() {
  if (!data) return;
  const notes = data.note_segments || [];
  const canvas = document.getElementById('rollCanvas');
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width;
  canvas.height = rect.height;
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0,0,canvas.width,canvas.height);
  ctx.fillStyle = '#07072e';
  ctx.fillRect(0,0,canvas.width,canvas.height);

  const noteEvents = notes.filter(n => !n.is_rest && noteToMidi(n.note)!==null);
  if (!noteEvents.length) {
    ctx.fillStyle='rgba(255,255,255,.2)';ctx.font='14px Outfit';ctx.textAlign='center';
    ctx.fillText('No note events to display',canvas.width/2,canvas.height/2);return;
  }

  const midiNums = noteEvents.map(n=>noteToMidi(n.note));
  const minMidi = Math.min(...midiNums)-1;
  const maxMidi = Math.max(...midiNums)+2;
  const totalTime = Math.max(...notes.map(n=>n.end));
  const startTime = Math.min(...notes.map(n=>n.start));
  const PAD_L=46,PAD_R=14,PAD_T=14,PAD_B=28;
  const W=canvas.width-PAD_L-PAD_R;
  const H=canvas.height-PAD_T-PAD_B;
  const midiRange=maxMidi-minMidi||1;
  const timeRange=totalTime-startTime||1;
  const noteNames=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];

  for (let m=Math.ceil(minMidi);m<=Math.floor(maxMidi);m++) {
    const y=PAD_T+H-((m-minMidi)/midiRange)*H;
    const nn=noteNames[m%12];
    const isBlack=['C#','D#','F#','G#','A#'].includes(nn);
    if (isBlack){ctx.fillStyle='rgba(0,0,0,.15)';ctx.fillRect(PAD_L,y-H/midiRange/2,W,H/midiRange);}
    ctx.strokeStyle=nn==='C'?'rgba(0,150,255,.2)':'rgba(0,150,255,.07)';
    ctx.lineWidth=nn==='C'?1:.5;
    ctx.beginPath();ctx.moveTo(PAD_L,y);ctx.lineTo(PAD_L+W,y);ctx.stroke();
    ctx.fillStyle=nn==='C'?'rgba(56,182,255,.75)':'rgba(148,163,184,.3)';
    ctx.font=(nn==='C'?'bold ':'')+' 9px JetBrains Mono';
    ctx.textAlign='right';
    ctx.fillText(nn+(Math.floor(m/12)-1),PAD_L-5,y+3);
  }
  for (let i=0;i<=8;i++){
    const t=startTime+(timeRange/8)*i;
    const x=PAD_L+((t-startTime)/timeRange)*W;
    ctx.strokeStyle='rgba(0,150,255,.07)';ctx.lineWidth=1;
    ctx.beginPath();ctx.moveTo(x,PAD_T);ctx.lineTo(x,PAD_T+H);ctx.stroke();
    ctx.fillStyle='rgba(148,163,184,.35)';ctx.font='9px JetBrains Mono';ctx.textAlign='center';
    ctx.fillText(t.toFixed(1)+'s',x,PAD_T+H+16);
  }
  const rowH=Math.max(4,(H/midiRange)-1);
  noteEvents.forEach((n,i)=>{
    const midi=noteToMidi(n.note);
    const x=PAD_L+((n.start-startTime)/timeRange)*W;
    const bw=Math.max(3,((n.end-n.start)/timeRange)*W-1);
    const y=PAD_T+H-((midi-minMidi)/midiRange)*H-rowH/2;
    const col=CARD_COLORS[i%CARD_COLORS.length];
    ctx.shadowBlur=6;ctx.shadowColor=col;
    const grad=ctx.createLinearGradient(x,y,x+bw,y);
    grad.addColorStop(0,col);grad.addColorStop(1,col+'88');
    ctx.fillStyle=grad;ctx.globalAlpha=0.88;
    ctx.beginPath();ctx.roundRect(x,y,bw,rowH,2);ctx.fill();
    ctx.globalAlpha=1;ctx.shadowBlur=0;
  });
}

const CARD_COLORS_GLOBAL=CARD_COLORS;