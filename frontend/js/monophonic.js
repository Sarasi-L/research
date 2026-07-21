//frontend/js/monophonic.js

const urlParams = new URLSearchParams(window.location.search);
const uploadedFileName = urlParams.get('file');
let analysisResult = null;
let currentXmlUrl = null;

document.getElementById('sideFileName').textContent = uploadedFileName || 'No file';

function switchTab(name) {
  const tabs = ['overview','pitch','sargam'];
  document.querySelectorAll('.inner-tab').forEach((t,i) => {
    t.classList.toggle('active', tabs[i] === name);
  });
  document.querySelectorAll('.tab-content').forEach(c => {
    c.classList.toggle('active', c.id === 'tab-' + name);
  });
}

function setStep(n, state) {
  const el = document.getElementById('st' + n);
  el.classList.remove('active','done');
  el.classList.add(state);
}
function setStepsUpTo(n) {
  for (let i=1; i<=6; i++) {
    if (i < n) setStep(i,'done');
    else if (i === n) setStep(i,'active');
    else { const el = document.getElementById('st'+i); el.classList.remove('active','done'); }
  }
}

const loadingMessages = [
  'Detecting instrument profile…',
  'Extracting pitch contour…',
  'Segmenting note boundaries…',
  'Estimating tempo and beat grid…',
  'Detecting key signature…',
  'Generating notation…'
];

document.getElementById('analyzeBtn').onclick = async () => {
  if (!uploadedFileName) { alert('No audio file specified!'); return; }
  document.getElementById('idleState').style.display = 'none';
  document.getElementById('loadingState').style.display = 'flex';
  document.getElementById('overviewBody').style.display = 'none';
  document.getElementById('analyzeBtn').disabled = true;

  let stepIdx = 0;
  const stepInterval = setInterval(() => {
    if (stepIdx < 6) {
      setStepsUpTo(stepIdx + 1);
      document.getElementById('loadingStep').textContent = loadingMessages[stepIdx];
      stepIdx++;
    }
  }, 600);

  try {
    const res = await fetch(`http://127.0.0.1:8000/analyze/monophonic/?filename=${uploadedFileName}`, { method: 'POST' });
    if (!res.ok) throw new Error(await res.text());
    const result = await res.json();
    analysisResult = result;
    localStorage.setItem('monophonicAnalysis', JSON.stringify(result));
    clearInterval(stepInterval);
    for (let i=1; i<=6; i++) setStep(i,'done');
    setTimeout(() => renderResults(result), 400);
  } catch(err) {
    clearInterval(stepInterval);
    console.error(err);
    alert('Analysis failed: ' + err.message);
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('idleState').style.display = 'flex';
    document.getElementById('analyzeBtn').disabled = false;
  }
};

const iconMap = { piano:'🎹', guitar:'🎸', violin:'🎻', flute:'🪈', voice:'🎤', trumpet:'🎺', saxophone:'🎷', cello:'🎻', clarinet:'🪈', keyboard:'🎹' };

function renderResults(result) {
  document.getElementById('loadingState').style.display = 'none';
  document.getElementById('overviewBody').style.display = 'grid';
  document.getElementById('analyzeBtn').disabled = false;

  const instr     = result.instrument?.instrument || '—';
  const instrConf = result.instrument?.confidence || 0;
  const icon      = iconMap[instr.toLowerCase()] || '🎵';

  document.getElementById('ihIcon').textContent = icon;
  document.getElementById('ihName').textContent = instr.toUpperCase();
  document.getElementById('ihConf').textContent = (instrConf * 100).toFixed(1) + '%';
  setTimeout(() => { document.getElementById('ihFill').style.width = (instrConf*100) + '%'; }, 200);

  const tempo = result.tempo?.tempo || 0;
  document.getElementById('mTempo').textContent   = tempo.toFixed(0);
  document.getElementById('mKey').textContent     = result.key?.key || '—';
  document.getElementById('mMode').textContent    = result.key?.mode || '—';
  document.getElementById('mTime').textContent    = result.beats_per_measure + '/4';
  const noteCount = (result.note_segments || []).filter(n=>!n.is_rest).length;
  document.getElementById('mNotes').textContent   = noteCount;
  document.getElementById('mKeyConf').textContent = result.key?.confidence ? (result.key.confidence * 100).toFixed(0) + '%' : '—';

  const beatMs = tempo > 0 ? (60000 / tempo).toFixed(0) : '—';
  document.getElementById('mipBeatLen').textContent = beatMs;

  // Sidebar summary
  document.getElementById('sbResults').style.display = 'flex';
  document.getElementById('srInstr').textContent  = instr.toUpperCase();
  document.getElementById('srKey').textContent    = (result.key?.key || '—') + ' ' + (result.key?.mode || '');
  document.getElementById('srTempo').textContent  = tempo.toFixed(0) + ' BPM';
  document.getElementById('srTime').textContent   = result.beats_per_measure + '/4';
  document.getElementById('srNotes').textContent  = (result.note_segments || []).length;

  document.getElementById('tabOv').classList.add('has-data');
  document.getElementById('tabPi').classList.add('has-data');

  currentXmlUrl = 'http://127.0.0.1:8000' + result.musicxml_file;
  renderMusicXML(currentXmlUrl);
  buildPitchTab(result);
  if (result.sargam_notation) renderSargam(result.sargam_notation);
}

async function renderMusicXML(url) {
  const container = document.getElementById('notationContainer');
  container.innerHTML = '<span style="color:#999;font-size:12px;">Rendering notation…</span>';
  const osmd = new opensheetmusicdisplay.OpenSheetMusicDisplay(container, {
    drawingParameters: 'compact', autoResize: true,
    drawTitle: true, drawMeasureNumbers: true, drawPartNames: false
  });
  try {
    await osmd.load(url);
    osmd.render();
  } catch(err) {
    container.innerHTML = '<span style="color:#f44;font-size:12px;">Notation unavailable. Check server connection.</span>';
    console.error(err);
  }
}

// ── PDF DOWNLOAD ──
document.getElementById('dlPdfBtn').onclick = async () => {
  const btn = document.getElementById('dlPdfBtn');
  const container = document.getElementById('notationContainer');
  const svgs = container.querySelectorAll('svg');
  if (!svgs.length) { alert('Notation not yet rendered.'); return; }
  btn.textContent = '⏳ Generating…'; btn.disabled = true;
  try {
    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF({ orientation:'portrait', unit:'mm', format:'a4' });
    const pageW=210, pageH=297, margin=12, usableW=pageW-margin*2;
    let yOffset=margin, firstPage=true;
    const filename = (document.getElementById('sideFileName').textContent||'score').replace(/\.[^.]+$/,'');
    const key   = document.getElementById('mKey').textContent;
    const tempo = document.getElementById('mTempo').textContent;
    const instr = document.getElementById('ihName').textContent;
    pdf.setFontSize(14); pdf.setTextColor(20,20,20);
    pdf.text(filename+' — Sheet Music', margin, yOffset); yOffset+=7;
    pdf.setFontSize(9); pdf.setTextColor(100,100,100);
    pdf.text(`Instrument: ${instr}   Key: ${key}   Tempo: ${tempo} BPM`, margin, yOffset); yOffset+=8;
    for (let i=0; i<svgs.length; i++) {
      const svg=svgs[i];
      let svgW, svgH;
      const vb=svg.getAttribute('viewBox');
      if(vb){const p=vb.split(/[\s,]+/);svgW=parseFloat(p[2]);svgH=parseFloat(p[3]);}
      else{const bb=svg.getBoundingClientRect();svgW=bb.width||800;svgH=bb.height||400;}
      if(!svgW||!svgH) continue;
      const cloned=svg.cloneNode(true);
      cloned.setAttribute('width',svgW);cloned.setAttribute('height',svgH);cloned.setAttribute('xmlns','http://www.w3.org/2000/svg');
      const svgUrl=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(cloned)],{type:'image/svg+xml;charset=utf-8'}));
      const canvas=await new Promise((resolve,reject)=>{
        const img=new Image();
        img.onload=()=>{
          const scale=3,c=document.createElement('canvas');
          c.width=svgW*scale;c.height=svgH*scale;
          const ctx=c.getContext('2d');ctx.fillStyle='#ffffff';ctx.fillRect(0,0,c.width,c.height);
          ctx.scale(scale,scale);ctx.drawImage(img,0,0,svgW,svgH);
          URL.revokeObjectURL(svgUrl);resolve(c);
        };
        img.onerror=(e)=>{URL.revokeObjectURL(svgUrl);reject(e);};img.src=svgUrl;
      });
      const aspectRatio=svgH/svgW, totalImgH_mm=usableW*aspectRatio, pxPerMm=canvas.height/totalImgH_mm;
      let srcYpx=0;
      while(srcYpx<canvas.height){
        const spaceLeft_mm=pageH-yOffset-margin,stripH_mm=Math.min(spaceLeft_mm,pageH-margin*2);
        const stripH_px=Math.round(stripH_mm*pxPerMm);
        if(stripH_px<=0){pdf.addPage();yOffset=margin;continue;}
        const actualStripH_px=Math.min(stripH_px,canvas.height-srcYpx);
        const actualStripH_mm=actualStripH_px/pxPerMm;
        const strip=document.createElement('canvas');
        strip.width=canvas.width;strip.height=actualStripH_px;
        const sctx=strip.getContext('2d');sctx.fillStyle='#ffffff';sctx.fillRect(0,0,strip.width,strip.height);
        sctx.drawImage(canvas,0,srcYpx,canvas.width,actualStripH_px,0,0,strip.width,actualStripH_px);
        if(!firstPage&&spaceLeft_mm<10){pdf.addPage();yOffset=margin;}
        pdf.addImage(strip.toDataURL('image/png'),'PNG',margin,yOffset,usableW,actualStripH_mm);
        yOffset+=actualStripH_mm+2;srcYpx+=actualStripH_px;firstPage=false;
        if(srcYpx<canvas.height){pdf.addPage();yOffset=margin;}
      }
    }
    pdf.save(`${filename}_sheet_music.pdf`);
  } catch(err){console.error(err);alert('PDF generation failed: '+err.message);}
  finally{btn.textContent='⬇ Download PDF';btn.disabled=false;}
};

function buildPitchTab(result) {
  document.getElementById('pitchIdle').style.display = 'none';
  document.getElementById('pitchBody').style.display = 'flex';
  const notes=result.note_segments||[];
  const totalDur=notes.reduce((s,n)=>s+(n.end-n.start),0);
  const uniqueSet=new Set(notes.filter(n=>!n.is_rest).map(n=>n.note));
  const maxDur=Math.max(...notes.map(n=>n.end-n.start),0.001);
  const totalTime=notes.length?Math.max(...notes.map(n=>n.end)):1;
  document.getElementById('pitchInfoStrip').innerHTML=`
    <div class="info-box"><div class="ib-val">${notes.length}</div><div class="ib-lbl">Total Events</div></div>
    <div class="info-box"><div class="ib-val">${uniqueSet.size}</div><div class="ib-lbl">Unique Pitches</div></div>
    <div class="info-box"><div class="ib-val">${totalDur.toFixed(1)}s</div><div class="ib-lbl">Total Duration</div></div>
    <div class="info-box"><div class="ib-val">${notes.length?(totalDur/notes.length).toFixed(2)+'s':'—'}</div><div class="ib-lbl">Avg Note Len</div></div>`;
  document.getElementById('noteCount').textContent=`${notes.length} events · ${uniqueSet.size} unique`;
  document.getElementById('rollSub').textContent=`${notes.filter(n=>!n.is_rest).length} notes · ${notes.filter(n=>n.is_rest).length} rests · total ${totalDur.toFixed(1)}s`;
  const NOTE_COLORS={
    'C':{bg:'rgba(0,150,255,.25)',border:'rgba(0,150,255,.8)',pill:'#0096FF',text:'#fff'},
    'D':{bg:'rgba(45,212,191,.2)',border:'rgba(45,212,191,.8)',pill:'#2dd4bf',text:'#021'},
    'E':{bg:'rgba(34,197,94,.2)',border:'rgba(34,197,94,.8)',pill:'#22c55e',text:'#fff'},
    'F':{bg:'rgba(245,158,11,.2)',border:'rgba(245,158,11,.8)',pill:'#f59e0b',text:'#021'},
    'G':{bg:'rgba(129,140,248,.25)',border:'rgba(129,140,248,.8)',pill:'#818cf8',text:'#fff'},
    'A':{bg:'rgba(236,72,153,.2)',border:'rgba(236,72,153,.8)',pill:'#ec4899',text:'#fff'},
    'B':{bg:'rgba(251,146,60,.2)',border:'rgba(251,146,60,.8)',pill:'#fb923c',text:'#021'},
  };
  function getNoteClass(n){if(!n)return NOTE_COLORS['C'];const b=n.replace(/[#b♯♭0-9]/g,'')[0]||'C';return NOTE_COLORS[b]||NOTE_COLORS['C'];}
  function noteToMidi(n){if(!n)return 60;const map={C:0,'C#':1,Db:1,D:2,'D#':3,Eb:3,E:4,F:5,'F#':6,Gb:6,G:7,'G#':8,Ab:8,A:9,'A#':10,Bb:10,B:11};const m=n.match(/^([A-G][#b]?)(\d+)$/);if(!m)return 60;return(parseInt(m[2])+1)*12+(map[m[1]]??0);}
  const noteSegs=notes.filter(n=>!n.is_rest), restSegs=notes.filter(n=>n.is_rest);
  const midiNotes=noteSegs.map(n=>noteToMidi(n.note));
  const minMidi=midiNotes.length?Math.max(Math.min(...midiNotes)-2,21):48;
  const maxMidi=midiNotes.length?Math.min(Math.max(...midiNotes)+2,108):84;
  const midiRange=Math.max(maxMidi-minMidi+1,12);
  const rollContainer=document.querySelector('.roll-scroll');
  const canvas=document.getElementById('rollCanvas');
  const containerW=rollContainer.clientWidth||600;
  const ROW_H=22,LABEL_W=36,HEADER_H=24;
  const canvasH=midiRange*ROW_H+HEADER_H;
  const canvasW=Math.max(containerW,totalTime*60+LABEL_W+20);
  canvas.width=canvasW;canvas.height=canvasH;
  const ctx=canvas.getContext('2d');
  ctx.fillStyle='#0d0d3a';ctx.fillRect(0,0,canvasW,canvasH);
  const NOTE_NAMES=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];
  for(let midi=minMidi;midi<=maxMidi;midi++){
    const rowIdx=maxMidi-midi,y=HEADER_H+rowIdx*ROW_H,pc=midi%12;
    const isBlack=[1,3,6,8,10].includes(pc);
    ctx.fillStyle=isBlack?'rgba(255,255,255,.025)':'rgba(255,255,255,.045)';
    ctx.fillRect(LABEL_W,y,canvasW-LABEL_W,ROW_H);
    ctx.fillStyle='rgba(0,150,255,.08)';ctx.fillRect(LABEL_W,y+ROW_H-1,canvasW-LABEL_W,1);
    const noteName=NOTE_NAMES[pc],isC=pc===0;
    ctx.fillStyle=isC?'#38b6ff':isBlack?'rgba(255,255,255,.2)':'rgba(255,255,255,.35)';
    ctx.font=isC?'bold 9px JetBrains Mono,monospace':'8px JetBrains Mono,monospace';
    ctx.textAlign='right';
    ctx.fillText(noteName+(isC?Math.floor(midi/12)-1:''),LABEL_W-3,y+ROW_H/2+3.5);
  }
  const timeStep=totalTime>30?5:totalTime>15?2:1;
  const pxPerSec=(canvasW-LABEL_W-10)/totalTime;
  for(let t=0;t<=totalTime;t+=timeStep){
    const x=LABEL_W+t*pxPerSec;
    ctx.fillStyle='rgba(0,150,255,.12)';ctx.fillRect(x,HEADER_H,1,canvasH-HEADER_H);
    ctx.fillStyle='rgba(255,255,255,.3)';ctx.font='9px JetBrains Mono,monospace';ctx.textAlign='center';
    ctx.fillText(t+'s',x,15);
  }
  ctx.fillStyle='rgba(7,7,46,.9)';ctx.fillRect(0,0,canvasW,HEADER_H);
  ctx.fillStyle='rgba(0,150,255,.15)';ctx.fillRect(0,HEADER_H-1,canvasW,1);
  restSegs.forEach(n=>{
    const x=LABEL_W+n.start*pxPerSec,w=Math.max((n.end-n.start)*pxPerSec-2,2);
    ctx.fillStyle='rgba(255,255,255,.04)';ctx.fillRect(x,HEADER_H,w,canvasH-HEADER_H);
  });
  noteSegs.forEach(n=>{
    const midi=noteToMidi(n.note);
    if(midi<minMidi||midi>maxMidi)return;
    const rowIdx=maxMidi-midi,y=HEADER_H+rowIdx*ROW_H+2,h=ROW_H-4;
    const x=LABEL_W+n.start*pxPerSec,w=Math.max((n.end-n.start)*pxPerSec-3,4);
    const col=getNoteClass(n.note);
    ctx.fillStyle=col.bg.replace('.25','.4').replace('.2','.35');
    ctx.beginPath();ctx.roundRect?ctx.roundRect(x,y,w,h,3):ctx.rect(x,y,w,h);ctx.fill();
    ctx.fillStyle=col.border;ctx.fillRect(x,y,3,h);
    if(w>22){ctx.fillStyle='rgba(255,255,255,.9)';ctx.font='bold 9px JetBrains Mono,monospace';ctx.textAlign='left';ctx.fillText(n.note,x+5,y+h/2+3.5);}
  });
  const seenClasses=new Set();
  noteSegs.forEach(n=>{const b=(n.note||'').replace(/[#b♯♭0-9]/g,'')[0];if(b)seenClasses.add(b);});
  document.getElementById('rollLegend').innerHTML=[...seenClasses].slice(0,7).map(c=>{
    const col=NOTE_COLORS[c]||NOTE_COLORS['C'];
    return`<span style="display:flex;align-items:center;gap:4px;"><span class="rl-dot" style="background:${col.pill}"></span>${c}</span>`;
  }).join('');
  const cardsEl=document.getElementById('noteCardsBody');
  cardsEl.innerHTML='';
  notes.forEach((n,i)=>{
    const dur=n.end-n.start,barPct=(dur/maxDur*100).toFixed(0);
    const col=n.is_rest?null:getNoteClass(n.note);
    const noteBase=n.is_rest?'':(n.note||'').replace(/[0-9]/g,'');
    const noteOct=n.is_rest?'':(n.note||'').replace(/[^0-9]/g,'');
    const card=document.createElement('div');
    card.className='note-card'+(n.is_rest?' is-rest':'');
    if(n.is_rest){
      card.innerHTML=`<span class="nc-seq">${i+1}</span><div class="nc-pill" style="background:rgba(255,255,255,.05);border-color:rgba(255,255,255,.1);color:var(--muted);"><span>—</span><span class="nc-octave">rest</span></div><div class="nc-info"><div class="nc-label" style="color:var(--muted)">Rest</div><div class="nc-timing">${n.start.toFixed(2)}s → ${n.end.toFixed(2)}s</div><div class="nc-dur-wrap"><div class="nc-dur-bar" style="width:${barPct}%;background:rgba(255,255,255,.15)"></div></div></div><span class="nc-dur-val">${dur.toFixed(2)}s</span>`;
    } else {
      card.innerHTML=`<span class="nc-seq">${i+1}</span><div class="nc-pill" style="background:${col.bg};border-color:${col.border};color:${col.pill};"><span>${noteBase}</span><span class="nc-octave">${noteOct}</span></div><div class="nc-info"><div class="nc-label">${n.note} <span style="font-size:10px;color:var(--muted);font-weight:400;">· ${noteNameToFull(n.note)}</span></div><div class="nc-timing">${n.start.toFixed(2)}s → ${n.end.toFixed(2)}s</div><div class="nc-dur-wrap"><div class="nc-dur-bar" style="width:${barPct}%;background:${col.pill}"></div></div></div><span class="nc-dur-val">${dur.toFixed(2)}s</span>`;
    }
    cardsEl.appendChild(card);
  });
}

function noteNameToFull(note){
  if(!note)return'';
  const names={C:'Do','C#':'Do#',Db:'Re♭',D:'Re','D#':'Re#',Eb:'Mi♭',E:'Mi',F:'Fa','F#':'Fa#',Gb:'Sol♭',G:'Sol','G#':'Sol#',Ab:'La♭',A:'La','A#':'La#',Bb:'Si♭',B:'Si'};
  const m=note.match(/^([A-G][#b]?)(\d+)$/);if(!m)return'';return(names[m[1]]||m[1])+m[2];
}

const SARGAM_COLORS={'Sa':'#0096FF','Re♭':'#2dd4bf','Re':'#2dd4bf','Ga♭':'#818cf8','Ga':'#818cf8','Ma♯':'#f59e0b','Ma':'#f59e0b','Pa':'#22c55e','Dha♭':'#ef4444','Dha':'#ef4444','Ni♭':'#ec4899','Ni':'#ec4899'};

function tokenizeSargamLine(line){
  const tokens=[],parts=line.trim().split(/\s+/);
  for(const part of parts){
    if(!part)continue;
    if(part==='|'){tokens.push({type:'bar'});continue;}
    const octaveMatch=part.match(/^(.*?)('+|,+)$/);
    let base=part,octave='';
    if(octaveMatch){base=octaveMatch[1];octave=octaveMatch[2];}
    const keys=Object.keys(SARGAM_COLORS).sort((a,b)=>b.length-a.length);
    const matched=keys.find(k=>base===k||base.startsWith(k));
    tokens.push({type:'note',value:base,key:matched||null,octave});
  }
  return tokens;
}

function renderSargam(raw){
  if(!raw||!raw.trim())return;
  document.getElementById('sargamIdle').style.display='none';
  document.getElementById('sargamContent').style.display='block';
  document.getElementById('tabSg').classList.add('has-data');
  const lines=raw.split('\n').filter(l=>l.trim());
  const measures=(raw.match(/\|/g)||[]).length;
  const allTokens=raw.split(/\s+/).filter(w=>w&&w!=='|');
  document.getElementById('sargamStats').innerHTML=`
    <div class="info-box"><div class="ib-val">${allTokens.length}</div><div class="ib-lbl">Syllables</div></div>
    <div class="info-box"><div class="ib-val">${measures}</div><div class="ib-lbl">Measures</div></div>
    <div class="info-box"><div class="ib-val">${lines.length}</div><div class="ib-lbl">Lines</div></div>
    <div class="info-box"><div class="ib-val">Indian</div><div class="ib-lbl">System</div></div>`;
  let html='',lineNum=1;
  for(const line of lines){
    if(!line.trim())continue;
    html+=`<div class="sg-line"><span class="sg-line-num">${lineNum++}</span>`;
    for(const tok of tokenizeSargamLine(line)){
      if(tok.type==='bar'){html+='<span class="sg-bar">│</span>';continue;}
      const col=tok.key?SARGAM_COLORS[tok.key]:'rgba(255,255,255,0.35)';
      const octHtml=tok.octave?`<span class="sg-oct" style="color:${col}">${tok.octave}</span>`:'';
      html+=`<span class="sg-syllable" style="color:${col};border-bottom-color:${col}40">${tok.value}${octHtml}</span>`;
    }
    html+='</div>';
  }
  document.getElementById('sargamText').innerHTML=html;
}

// Restore from localStorage
const cached=(()=>{try{return JSON.parse(localStorage.getItem('monophonicAnalysis'));}catch{return null;}})();
if(cached&&cached.note_segments){
  analysisResult=cached;
  for(let i=1;i<=6;i++){document.getElementById('st'+i).classList.add('done');}
  document.getElementById('idleState').style.display='none';
  renderResults(cached);
}