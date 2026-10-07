// HyperFrames & Modal GPU Fleet Studio Front-end Logic

let currentAspect = "9:16";
let lastGeneratedImageB64 = null;
let uploadedSourceB64 = null;
let timerInterval = null;

// Presets mapping
const PRESETS = {
  cyber: "Cinematic cybernetic operative standing on rain-slicked neon skyscraper rooftop, volumetric fog, dynamic low angle, 8K ultra detailed, octane render, raytraced reflection",
  "sci-fi": "Deep space planetary observation outpost, titanium modular airlocks, stark lunar lighting, high contrast matte composite armor, hard sci-fi realism",
  space: "Vast glowing stellar accretion disk orbiting a rotating Kerr black hole, gravitational lensing, interstellar gas filaments, cosmic dust clouds, 8K wallpaper",
  anime: "Studio quality atmospheric illustration, dramatic stormy sunset over coastal breakwater, windblown aesthetic, intricate line art, cinematic lighting"
};

// ── Tab Switching ────────────────────────────────────────────────────────────
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

  const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(b =>
    b.getAttribute('onclick').includes(tabId)
  );
  if (activeBtn) activeBtn.classList.add('active');

  const target = document.getElementById(tabId);
  if (target) target.classList.add('active');

  if (tabId === 'tab-fleet') {
    fetchFleetStatus();
    fetchJobs();
  }
}

// ── Aspect Ratio Picker ──────────────────────────────────────────────────────
function setAspect(aspect, btn) {
  currentAspect = aspect;
  document.querySelectorAll('#dit-aspect-group .aspect-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}

function setPreset(key) {
  if (PRESETS[key]) {
    document.getElementById('dit-prompt').value = PRESETS[key];
  }
}

// ── Fleet Telemetry & Live Status ────────────────────────────────────────────
async function fetchFleetStatus() {
  const btn = document.getElementById('btn-refresh-fleet');
  btn.textContent = '↻ Probing...';

  try {
    const res = await fetch('/api/fleet/status?timeout=4');
    const data = await res.json();

    if (data.success) {
      const healthyDit = data.dit_workers.filter(w => w.status === 'healthy');
      const healthyEdit = data.edit_workers.filter(w => w.status === 'healthy');

      // Update pills
      document.getElementById('text-dit').textContent = `DiT: ${healthyDit.length}/${data.dit_workers.length} A100 Nodes`;
      document.getElementById('dot-dit').className = healthyDit.length > 0 ? 'dot' : 'dot offline';

      document.getElementById('text-edit').textContent = `Edit: ${healthyEdit.length > 0 ? 'Ready' : 'Offline'}`;
      document.getElementById('dot-edit').className = healthyEdit.length > 0 ? 'dot' : 'dot offline';

      // Update Telemetry Table
      const tbody = document.getElementById('telemetry-table-body');
      tbody.innerHTML = '';

      data.dit_workers.forEach(w => {
        const isH = w.status === 'healthy';
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${isH ? '🟢' : '🔴'} ${w.status}</td>
          <td><strong>${w.workspace}</strong></td>
          <td>Qwen DiT 2.1</td>
          <td>${w.gpu || 'A100-80GB'}</td>
          <td>${isH ? `VRAM: ${w.vram_used_gb}/${w.vram_total_gb} GB` : (w.error || 'N/A')}</td>
          <td>${w.elapsed_s ? w.elapsed_s + 's' : '-'}</td>
        `;
        tbody.appendChild(tr);
      });

      data.edit_workers.forEach(w => {
        const isH = w.status === 'healthy';
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${isH ? '🟢' : '🔴'} ${w.status}</td>
          <td><strong>${w.workspace}</strong></td>
          <td>Qwen Image 2.1 Edit</td>
          <td>${w.gpu || 'A100-80GB'}</td>
          <td>${w.pipeline || 'Dedicated Edit'}</td>
          <td>${w.elapsed_s ? w.elapsed_s + 's' : '-'}</td>
        `;
        tbody.appendChild(tr);
      });
    }
  } catch (err) {
    console.error('Failed to probe fleet:', err);
  } finally {
    btn.textContent = '↻ Refresh Nodes';
  }
}

// ── Text-to-Image Generation (Qwen DiT 2.1) ──────────────────────────────────
async function runDitGeneration() {
  const prompt = document.getElementById('dit-prompt').value.trim();
  if (!prompt) {
    alert('Please enter a prompt.');
    return;
  }

  const btn = document.getElementById('btn-dit-generate');
  btn.disabled = true;
  btn.innerHTML = '<span>⚡ Dispatching to Modal Fleet...</span>';

  // Toggle stage
  document.getElementById('dit-empty-state').style.display = 'none';
  document.getElementById('dit-result-img').style.display = 'none';
  document.getElementById('dit-info-bar').style.display = 'none';
  document.getElementById('dit-loading-state').style.display = 'block';

  let startTime = Date.now();
  timerInterval = setInterval(() => {
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    document.getElementById('dit-timer').textContent = `${elapsed}s elapsed`;
  }, 100);

  const payload = {
    prompt: prompt,
    negative_prompt: document.getElementById('dit-neg').value,
    aspect_ratio: currentAspect,
    steps: parseInt(document.getElementById('dit-steps').value),
    guidance_scale: parseFloat(document.getElementById('dit-guidance').value),
    seed: parseInt(document.getElementById('dit-seed').value),
  };

  try {
    const res = await fetch('/api/generate/draw', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    clearInterval(timerInterval);

    if (res.ok && data.success) {
      document.getElementById('dit-loading-state').style.display = 'none';
      const img = document.getElementById('dit-result-img');
      img.src = data.file_url;
      img.style.display = 'block';

      lastGeneratedImageB64 = data.b64_json;

      document.getElementById('dit-info-node').textContent = data.workspace;
      document.getElementById('dit-info-time').textContent = `${data.elapsed_s}s`;
      document.getElementById('dit-download-btn').href = data.file_url;
      document.getElementById('dit-info-bar').style.display = 'flex';
      document.getElementById('dit-preview-stage').classList.add('has-image');
    } else {
      alert(`Generation failed: ${data.detail || data.error || 'Server error'}`);
      document.getElementById('dit-empty-state').style.display = 'block';
      document.getElementById('dit-loading-state').style.display = 'none';
    }
  } catch (err) {
    clearInterval(timerInterval);
    alert(`Network error: ${err.message}`);
    document.getElementById('dit-empty-state').style.display = 'block';
    document.getElementById('dit-loading-state').style.display = 'none';
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span>⚡ Generate on Modal A100 GPU</span>';
  }
}

function sendToEdit() {
  const img = document.getElementById('dit-result-img');
  if (!img.src) return;

  // Convert image to base64
  fetch(img.src)
    .then(r => r.blob())
    .then(blob => {
      const reader = new FileReader();
      reader.onloadend = () => {
        uploadedSourceB64 = reader.result.split(',')[1];
        document.getElementById('edit-source-preview').src = reader.result;
        document.getElementById('edit-source-preview').style.display = 'block';
        document.getElementById('edit-source-empty').style.display = 'none';
        switchTab('tab-edit');
      };
      reader.readAsDataURL(blob);
    });
}

// ── Image-to-Image Edit (Qwen Image 2.1) ──────────────────────────────────────
function handleImageUpload(e) {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onloadend = () => {
    uploadedSourceB64 = reader.result.split(',')[1];
    document.getElementById('edit-source-preview').src = reader.result;
    document.getElementById('edit-source-preview').style.display = 'block';
    document.getElementById('edit-source-empty').style.display = 'none';
  };
  reader.readAsDataURL(file);
}

async function runEditGeneration() {
  const prompt = document.getElementById('edit-prompt').value.trim();
  if (!uploadedSourceB64) {
    alert('Please upload or send a source image first.');
    return;
  }
  if (!prompt) {
    alert('Please enter an edit instruction prompt.');
    return;
  }

  const btn = document.getElementById('btn-edit-run');
  btn.disabled = true;
  btn.innerHTML = '<span>🎨 Editing on GPU...</span>';

  document.getElementById('edit-result-preview').style.display = 'none';
  document.getElementById('edit-result-empty').style.display = 'none';
  document.getElementById('edit-loading').style.display = 'block';

  const payload = {
    prompt: prompt,
    image_b64: uploadedSourceB64,
    strength: parseFloat(document.getElementById('edit-strength').value),
    steps: parseInt(document.getElementById('edit-steps').value),
  };

  try {
    const res = await fetch('/api/generate/edit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    document.getElementById('edit-loading').style.display = 'none';

    if (res.ok && data.success) {
      const img = document.getElementById('edit-result-preview');
      img.src = data.file_url;
      img.style.display = 'block';
    } else {
      alert(`Edit failed: ${data.detail || data.error || 'Server error'}`);
      document.getElementById('edit-result-empty').style.display = 'block';
    }
  } catch (err) {
    document.getElementById('edit-loading').style.display = 'none';
    alert(`Network error: ${err.message}`);
    document.getElementById('edit-result-empty').style.display = 'block';
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span>🎨 Run Image Edit on Modal</span>';
  }
}

// ── Shorts Scene Pack Generator ──────────────────────────────────────────────
async function runScenePack() {
  const slug = document.getElementById('scene-slug').value.trim();
  const topic = document.getElementById('scene-topic').value.trim();

  if (!slug || !topic) {
    alert('Please provide both slug and topic.');
    return;
  }

  const btn = document.getElementById('btn-scene-pack');
  btn.disabled = true;
  btn.innerHTML = '<span>⚡ Firing 4 GPUs...</span>';

  // Set loading state on thumbs
  for (let i = 0; i < 4; i++) {
    const thumb = document.getElementById(`thumb-scene-${i}`);
    thumb.innerHTML = '<div class="spinner" style="width:28px;height:28px;"></div><span style="font-size:12px;color:var(--cyan);margin-top:8px;">Generating...</span>';
  }

  try {
    const res = await fetch('/api/generate/scene-pack', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slug, topic })
    });

    const data = await res.json();
    if (res.ok && data.success) {
      data.scenes.forEach((sc, idx) => {
        const thumb = document.getElementById(`thumb-scene-${idx}`);
        thumb.innerHTML = `<img src="${sc.file_url}" style="width:100%;height:100%;object-fit:cover;">`;
      });

      // Update project dropdown
      loadProjectOptions(data.project_dir);
      alert(`✨ 4-Scene pack generated for ${data.slug}! Switching to Video Studio.`);
      switchTab('tab-video');
    } else {
      alert(`Failed to generate scene pack: ${data.detail || 'Unknown error'}`);
    }
  } catch (err) {
    alert(`Network error: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span>⚡ Generate 4 Scenes</span>';
  }
}

// ── HyperFrames Video Studio & Render ────────────────────────────────────────
function loadProjectPreview(path) {
  const iframe = document.getElementById('video-preview-frame');
  iframe.src = `/${path}/index.html`;
}

function reloadIframe() {
  const iframe = document.getElementById('video-preview-frame');
  iframe.src = iframe.src;
}

async function loadProjectOptions(selectValue = null) {
  try {
    const res = await fetch('/api/projects');
    const data = await res.json();
    if (data.success && data.projects) {
      const select = document.getElementById('video-project-select');
      select.innerHTML = '';
      data.projects.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.path;
        opt.textContent = `${p.path} (${p.type})`;
        select.appendChild(opt);
      });
      if (selectValue) {
        select.value = selectValue;
        loadProjectPreview(selectValue);
      }
    }
  } catch (e) {
    console.error('Could not load projects:', e);
  }
}

async function triggerRender() {
  const project = document.getElementById('video-project-select').value;
  const format = document.getElementById('video-render-format').value;

  const btn = document.getElementById('btn-render-video');
  const statusBox = document.getElementById('render-status');
  const downloadArea = document.getElementById('render-download-area');

  btn.disabled = true;
  statusBox.style.display = 'block';
  downloadArea.style.display = 'none';

  try {
    const res = await fetch('/api/video/render', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_dir: project, format })
    });

    const data = await res.json();
    if (res.ok && data.success) {
      statusBox.style.display = 'none';
      downloadArea.style.display = 'block';
      const dlBtn = document.getElementById('btn-download-mp4');
      dlBtn.href = data.video_url;
      dlBtn.textContent = `⬇ Download ${data.rendered_file.split('/').pop()} (${(data.file_size_bytes/1024/1024).toFixed(1)} MB)`;
    } else {
      alert(`Render failed: ${data.detail || data.error || 'Server error'}`);
      statusBox.style.display = 'none';
    }
  } catch (err) {
    alert(`Render network error: ${err.message}`);
    statusBox.style.display = 'none';
  } finally {
    btn.disabled = false;
  }
}

// ── Durable Jobs Fetcher ─────────────────────────────────────────────────────
async function fetchJobs() {
  try {
    const res = await fetch('/api/jobs');
    const data = await res.json();
    if (data.success) {
      const tbody = document.getElementById('jobs-table-body');
      tbody.innerHTML = '';
      if (data.jobs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-dim);">No jobs recorded</td></tr>';
        return;
      }
      data.jobs.forEach(j => {
        const tr = document.createElement('tr');
        const stateColor = j.state === 'downloaded' ? 'var(--green)' : (j.state === 'failed' ? 'var(--red)' : 'var(--yellow)');
        tr.innerHTML = `
          <td><span style="color: ${stateColor}; font-weight: 700;">${j.state}</span></td>
          <td>${j.jobId}</td>
          <td>${j.jobType}</td>
          <td>${j.createdAt || '-'}</td>
          <td>${j.elapsed_s ? j.elapsed_s + 's' : '-'}</td>
          <td>${j.workspace || '-'} (${(j.sha256 || '').slice(0, 8)}...)</td>
        `;
        tbody.appendChild(tr);
      });
    }
  } catch (err) {
    console.error('Failed to load jobs:', err);
  }
}

// ── On Page Load ─────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  fetchFleetStatus();
  loadProjectOptions();
});
