/* Validation and feedback module for index page */

const MESSAGES = {
  INPUT_EMPTY: { text: 'Inserisci almeno un verso prima di continuare.', blocks:{analyze:true, copy:true, publish:true}, severity:'warning' },
  INPUT_WHITESPACE: { text: 'Il testo contiene solo spazi o righe vuote.', blocks:{analyze:true, copy:true, publish:true}, severity:'warning' },
  INPUT_TOO_LONG: { text: 'Testo molto lungo: potresti ridurlo per analisi più veloce.', blocks:{}, severity:'warning' },
  INPUT_EXCESSIVE_LINES: { text: 'Molti versi: analisi più lenta.', blocks:{}, severity:'warning' },
  LINE_TOO_LONG: { text: 'Alcuni versi sono molto lunghi: verifica che sia voluto.', blocks:{}, severity:'info' },
  UNUSUAL_CHARS: { text: 'Caratteri speciali rilevati: controlla sillabazione.', blocks:{}, severity:'info' },
  RESULTS_OBSOLETE: { text: 'Hai modificato il testo dopo l\'ultima analisi.', blocks:{}, severity:'info' },
  FREE_VERSE_PATTERN_NOTE: { text: 'Versi liberi: nessun vincolo metrico classico.', blocks:{}, severity:'info' },
  COPY_EMPTY: { text: 'Nulla da copiare: scrivi prima la poesia.', blocks:{copy:true}, severity:'warning' },
  PUBLISH_NO_TEXT: { text: 'Non puoi pubblicare una poesia vuota.', blocks:{publish:true, analyze:true}, severity:'warning' },
  PUBLISH_NO_AUTHOR_ASSIGNED: { text: 'Autore vuoto: userò “Poeta Anonimo”.', blocks:{}, severity:'info' }
};

let state = {
  lastAnalyzedHash: null,
  dirtySinceAnalysis: false,
  authorAutoNoticeShown: false
};

function hashInput(str){
  // djb2
  let h = 5381; for (let i=0;i<str.length;i++){ h = ((h<<5)+h) + str.charCodeAt(i); }
  return (h>>>0).toString(16);
}

function markAnalysisCompleted(text){
  state.lastAnalyzedHash = hashInput(text);
  state.dirtySinceAnalysis = false;
}

function noteInputChanged(){
  state.dirtySinceAnalysis = true;
}

function makeIssue(code){
  const def = MESSAGES[code];
  return { code, severity: def.severity, message: def.text, blockingActions: def.blocks };
}

function validateCurrentInput(ctx){
  const { text, poemType, action, publishChecked, authorValue } = ctx;
  const issues = [];
  const raw = text || '';
  const trimmedNoCR = raw.replace(/\r+/g,'');
  const pure = trimmedNoCR.trim();

  if (!pure){ issues.push(makeIssue('INPUT_EMPTY')); }
  else if (!pure.replace(/\s+/g,'')){ issues.push(makeIssue('INPUT_WHITESPACE')); }

  const lines = trimmedNoCR.split('\n').filter(l=>true);
  if (raw.length > 4000) issues.push(makeIssue('INPUT_TOO_LONG'));
  if (lines.length > 70) issues.push(makeIssue('INPUT_EXCESSIVE_LINES'));
  if (lines.some(l=>l.length>200)) issues.push(makeIssue('LINE_TOO_LONG'));
  if (/[^A-Za-zÀ-ÖØ-öø-ÿ0-9'’?!.,;:\-\s]/.test(raw)) issues.push(makeIssue('UNUSUAL_CHARS'));
  if (state.dirtySinceAnalysis && state.lastAnalyzedHash) issues.push(makeIssue('RESULTS_OBSOLETE'));
  if (poemType === 'versi_liberi') issues.push(makeIssue('FREE_VERSE_PATTERN_NOTE'));

  if (publishChecked && !pure) issues.push(makeIssue('PUBLISH_NO_TEXT'));
  if (publishChecked && !authorValue.trim()) {
    if (!state.authorAutoNoticeShown) {
      issues.push(makeIssue('PUBLISH_NO_AUTHOR_ASSIGNED'));
    }
  }
  if (action === 'copy' && !pure) issues.push(makeIssue('COPY_EMPTY'));

  return issues;
}

function getBlockingStatus(issues){
  return issues.reduce((acc,i)=>{
    if (i.blockingActions?.analyze) acc.analyze = true;
    if (i.blockingActions?.copy) acc.copy = true;
    if (i.blockingActions?.publish) acc.publish = true;
    return acc;
  }, { analyze:false, copy:false, publish:false });
}

function renderIssues(issues){
  const container = document.getElementById('validationMessages');
  if (!container) return;
  container.innerHTML = '';

  // Separa errori da warning/info: errori non vanno più nel container
  const errors = issues.filter(i=> i.severity === 'error');
  const nonErrors = issues.filter(i=> i.severity !== 'error');

  if (!nonErrors.length) {
    container.style.display='none';
  } else {
    container.style.display='block';
    const sorted = nonErrors.sort((a,b)=> severityRank(a.severity)-severityRank(b.severity));
    const top = sorted.slice(0,4);
    const frag = document.createDocumentFragment();
    top.forEach(issue => {
      const div = document.createElement('div');
      div.className = `validation-msg validation-${issue.severity}`;
      div.setAttribute('data-code', issue.code);
      div.innerHTML = `<span class=\"val-icon\">${iconFor(issue.severity)}</span> <span>${issue.message}</span>`;
      frag.appendChild(div);
    });
    container.appendChild(frag);
  }

  // Mostra toast se ci sono errori (anche se nascosti dalla lista)
  if (errors.length) {
    triggerErrorToast(errors[0]);
  }
}

function triggerErrorToast(issue){
  const toastEl = document.getElementById('errorToast');
  const msgEl = document.getElementById('errorToastMessage');
  if (!toastEl || !msgEl) return;
  msgEl.textContent = issue.message;
  // Mostra toast se bootstrap è disponibile (lazy load safe)
  const show = () => {
    try { new bootstrap.Toast(toastEl).show(); } catch(e) { /* silent */ }
  };
  if (window.bootstrap && window.bootstrap.Toast) show(); else {
    let tries = 0; const iv = setInterval(()=>{ if (window.bootstrap && window.bootstrap.Toast){ clearInterval(iv); show(); } else if(++tries>20){ clearInterval(iv);} },100);
  }
}

function severityRank(sev){
  return sev === 'error' ? 0 : sev === 'warning' ? 1 : 2;
}

function iconFor(sev){
  switch(sev){
    case 'error': return '<i class="bi bi-x-octagon-fill"></i>';
    case 'warning': return '<i class="bi bi-exclamation-triangle-fill"></i>';
    default: return '<i class="bi bi-info-circle-fill"></i>';
  }
}

function attachValidationHandlers(elements){
  const { poemText, poemTypeSelect, publishCheckbox } = elements;
  if (poemText){
    poemText.addEventListener('input', () => {
      noteInputChanged();
      const issues = validateCurrentInput({
        text: poemText.value,
        poemType: poemTypeSelect?.value,
        action: 'typing',
        publishChecked: publishCheckbox?.checked,
        authorValue: document.getElementById('poemAuthor')?.value || ''
      });
      renderIssues(issues.filter(i=>i.code!=='COPY_EMPTY'));
    });
  }
}

export {
  validateCurrentInput,
  getBlockingStatus,
  renderIssues,
  markAnalysisCompleted,
  noteInputChanged,
  attachValidationHandlers
};
