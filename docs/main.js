const COMPANY_COLORS = [
  '#2563EB', '#7C3AED', '#0E9F6E', '#D97706',
  '#DC2626', '#0891B2', '#059669', '#B45309',
];

function colorForCompany(name) {
  let hash = 0;
  for (const c of (name || '?')) hash = (hash * 31 + c.charCodeAt(0)) & 0xffffffff;
  return COMPANY_COLORS[Math.abs(hash) % COMPANY_COLORS.length];
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return '';
  const diffDays = Math.floor((Date.now() - d.getTime()) / 86400000);
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 14) return '1 week ago';
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function esc(str) {
  return (str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function safeUrl(url) {
  try {
    const p = new URL(url || '');
    return (p.protocol === 'https:' || p.protocol === 'http:') ? url : '#';
  } catch { return '#'; }
}

function buildCard(job) {
  const initial = (job.company || '?')[0].toUpperCase();
  const color   = colorForCompany(job.company);
  const tags    = (job.tags || []).filter(t => t !== 'other');

  const tagHtml = [
    ...tags.map(t => `<span class="tag tag-${esc(t)}">${esc(t === 'insights' ? 'Insights' : t.toUpperCase())}</span>`),
    job.remote ? '<span class="tag tag-remote">Remote</span>' : '',
  ].filter(Boolean).join('');

  return `
<article class="job-card">
  <div class="card-top">
    <div class="company-initial" style="background:${color}">${initial}</div>
    <div class="card-title-block">
      <div class="card-title">${esc(job.title)}</div>
      <div class="card-company">${esc(job.company)}</div>
    </div>
  </div>
  <div class="card-location">📍 ${esc(job.location || 'Location not specified')}</div>
  ${tagHtml ? `<div class="card-tags">${tagHtml}</div>` : ''}
  <div class="card-footer">
    <span class="card-date">${esc(formatDate(job.posted))}</span>
    <a href="${esc(safeUrl(job.url))}" target="_blank" rel="noopener noreferrer" class="view-btn">View Job →</a>
  </div>
</article>`.trim();
}

let allJobs    = [];
let activeTag  = 'all';
let searchQuery = '';

function render() {
  const grid     = document.getElementById('job-grid');
  const empty    = document.getElementById('empty-state');
  const countEl  = document.getElementById('job-count');

  const filtered = allJobs.filter(job => {
    const matchesTag =
      activeTag === 'all'    ? true :
      activeTag === 'remote' ? job.remote :
      (job.tags || []).includes(activeTag);

    if (!matchesTag) return false;
    if (!searchQuery) return true;

    const haystack = [job.title, job.company, job.location, job.description]
      .join(' ').toLowerCase();
    return searchQuery.split(/\s+/).every(w => haystack.includes(w));
  });

  if (filtered.length === 0) {
    grid.innerHTML = '';
    empty.classList.remove('hidden');
    countEl.textContent = 'No positions found';
  } else {
    empty.classList.add('hidden');
    grid.innerHTML = filtered.map(buildCard).join('');
    const n = filtered.length;
    countEl.textContent = `${n.toLocaleString()} position${n !== 1 ? 's' : ''}`;
  }
}

async function loadJobs() {
  try {
    const resp = await fetch('jobs.json?_=' + Date.now());
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    allJobs = data.jobs || [];

    if (data.updated && data.updated !== 'never') {
      const d = new Date(data.updated);
      document.getElementById('last-updated').textContent =
        'Updated ' + d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }

    render();
  } catch (err) {
    document.getElementById('job-count').textContent = 'Could not load jobs — check back soon.';
    console.error('Failed to load jobs.json:', err);
  }
}

document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeTag = btn.dataset.tag;
    render();
  });
});

let searchTimer;
document.getElementById('search').addEventListener('input', e => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    searchQuery = e.target.value.trim().toLowerCase();
    render();
  }, 200);
});

loadJobs();
