const $ = (selector) => document.querySelector(selector);
const state = { root: '', files: [], operations: [], busy: false };

async function api(path, options = {}) {
  const headers = options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' };
  const response = await fetch(path, { headers, ...options });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Something went wrong');
  return data;
}

$('#chooseFolder').addEventListener('click', () => $('#folderUpload').click());
$('#folderUpload').addEventListener('change', async event => {
  const files = [...event.target.files];
  if (!files.length || state.busy) return;
  state.busy = true;
  setProgress(`Uploading a safe working copy of ${files.length} files…`);
  const form = new FormData();
  files.forEach(file => {
    form.append('files', file, file.name);
    form.append('relative_paths', file.webkitRelativePath || file.name);
  });
  try {
    const result = await api('/api/upload', { method: 'POST', body: form });
    $('#folder').value = result.folder;
    $('#recursive').checked = true;
    setProgress(`Uploaded ${result.files_uploaded} files. Select Scan folder to analyze the working copy.`);
  } catch (error) { setProgress(`Upload failed: ${error.message}`); }
  finally { state.busy = false; event.target.value = ''; }
});

function setProgress(message = '') {
  $('#progress').hidden = !message;
  $('#progress').textContent = message;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
}

async function checkHealth() {
  const el = $('#modelStatus');
  try {
    const result = await api('/api/health');
    const labels = { ready: 'Gemma ready', model_unavailable: 'Gemma model unavailable', ollama_unavailable: 'Ollama unavailable' };
    el.className = `model-status ${result.status === 'ready' ? 'ready' : 'error'}`;
    el.innerHTML = `<span></span>${labels[result.status]}`;
  } catch { el.className = 'model-status error'; el.innerHTML = '<span></span>Status unavailable'; }
}

$('#scanForm').addEventListener('submit', async event => {
  event.preventDefault();
  if (state.busy) return;
  state.busy = true;
  try {
    setProgress('Scanning files…');
    const scan = await api('/api/scan', { method: 'POST', body: JSON.stringify({ folder: $('#folder').value, recursive: $('#recursive').checked }) });
    state.root = scan.root; state.files = scan.files;
    if (!scan.files.length) throw new Error('No files found in this folder.');
    setProgress('Extracting content and analyzing with Gemma…');
    const analysis = await api('/api/analyze', { method: 'POST', body: JSON.stringify({ folder: state.root, files: scan.files.map(file => file.path) }) });
    state.operations = analysis.operations;
    renderResults();
    setProgress('');
  } catch (error) { setProgress(`Could not build a plan: ${error.message}`); }
  finally { state.busy = false; }
});

function renderResults() {
  const categories = new Set(state.operations.map(item => item.category));
  const review = state.operations.filter(item => item.needs_review).length;
  $('#stats').innerHTML = [[state.files.length,'Files scanned'],[state.operations.length,'Classified'],[review,'Need review'],[categories.size,'Categories']].map(([n,label]) => `<div class="stat"><strong>${n}</strong><small>${label}</small></div>`).join('');
  $('#operations').innerHTML = state.operations.map((item, index) => `<article class="operation">
    <input type="checkbox" aria-label="Approve ${escapeHtml(item.suggested_filename)}" data-index="${index}">
    <div><h3>${escapeHtml(item.source.split(/[\\/]/).pop())}</h3><div class="destination-fields">
      <label>Category<input data-field="category" data-index="${index}" value="${escapeHtml(item.category)}" maxlength="60"></label>
      <label>Subcategory<input data-field="subcategory" data-index="${index}" value="${escapeHtml(item.subcategory)}" maxlength="60"></label>
      <label>Filename<input data-field="suggested_filename" data-index="${index}" value="${escapeHtml(item.suggested_filename)}" maxlength="180"></label>
    </div><p class="reason">${escapeHtml(item.reason)}</p></div>
    <span class="confidence ${item.confidence}">${item.confidence.toUpperCase()}</span>
  </article>`).join('');
  $('#results').hidden = false;
  $('#results').scrollIntoView({ behavior: 'smooth' });
  document.querySelectorAll('.operation input').forEach(input => input.addEventListener('change', updateApproved));
  document.querySelectorAll('.destination-fields input').forEach(input => input.addEventListener('input', event => {
    state.operations[Number(event.target.dataset.index)][event.target.dataset.field] = event.target.value.trim();
  }));
  updateApproved();
}

function updateApproved() {
  const checked = [...document.querySelectorAll('.operation input:checked')];
  $('#approvedCount').textContent = `${checked.length} approved`;
  $('#execute').disabled = !checked.length || state.busy;
}

$('#selectAll').addEventListener('click', () => { document.querySelectorAll('.operation input').forEach(el => el.checked = true); updateApproved(); });
$('#clearAll').addEventListener('click', () => { document.querySelectorAll('.operation input').forEach(el => el.checked = false); updateApproved(); });
$('#execute').addEventListener('click', async () => {
  const selected = [...document.querySelectorAll('.operation input:checked')].map(el => state.operations[Number(el.dataset.index)]);
  state.busy = true; updateApproved();
  try {
    const operations = selected.map(({source, category, subcategory, suggested_filename}) => ({source, category, subcategory, suggested_filename}));
    const result = await api('/api/execute', { method: 'POST', body: JSON.stringify({ folder: state.root, operations }) });
    alert(`Organized ${result.stats.moved} files. Renamed ${result.stats.renamed}. Deleted 0.`);
    $('#results').hidden = true;
  } catch (error) { alert(`Organization stopped: ${error.message}`); }
  finally { state.busy = false; updateApproved(); }
});
$('#undo').addEventListener('click', async () => {
  try { const result = await api('/api/undo', { method: 'POST', body: '{}' }); alert(`Restored ${result.restored} files. Deleted 0.`); }
  catch (error) { alert(`Undo unavailable: ${error.message}`); }
});
checkHealth();
