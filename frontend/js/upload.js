// upload.js - Upload page logic

let uploadedPapers = [];

document.addEventListener('DOMContentLoaded', async () => {
    await loadExistingPapers();
    setupDragAndDrop();
    setupFileInput();
});

async function loadExistingPapers() {
    try {
        const data = await getPapers();
        uploadedPapers = data.papers || [];
        renderPapers();
        updateStats();
    } catch (error) {
        console.error('Failed to load papers:', error);
    }
}

function setupDragAndDrop() {
    const uploadArea = document.getElementById('upload-area');

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', async (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.pdf'));
        if (files.length > 0) await uploadFiles(files);
    });
}

function setupFileInput() {
    const fileInput = document.getElementById('file-input');
    fileInput.addEventListener('change', async (e) => {
        const files = Array.from(e.target.files);
        if (files.length > 0) await uploadFiles(files);
        fileInput.value = '';
    });
}

async function uploadFiles(files) {
    const progress = document.getElementById('upload-progress');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');

    progress.style.display = 'block';

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const percent = Math.round((i / files.length) * 100);

        progressFill.style.width = `${percent}%`;
        progressText.textContent = `Uploading ${file.name}  (${i + 1}/${files.length})`;

        try {
            const result = await uploadPaper(file);
            uploadedPapers = result.total_papers > 0
                ? [...new Set([...uploadedPapers, file.name])]
                : uploadedPapers;

            showToast(`${file.name} added to library`, 'success');
        } catch (error) {
            showToast(`Couldn't upload ${file.name}: ${error.message}`, 'error');
        }
    }

    progressFill.style.width = '100%';
    progressText.textContent = 'Done';

    setTimeout(() => {
        progress.style.display = 'none';
        progressFill.style.width = '0%';
    }, 1500);

    await loadExistingPapers();
}

function renderPapers() {
    const container = document.getElementById('papers-container');
    const clearBtn = document.getElementById('clear-btn');
    const actionButtons = document.getElementById('action-buttons');

    if (uploadedPapers.length === 0) {
        container.innerHTML = `
            <div class="empty-state" style="padding:24px 0;">
                <p>Nothing uploaded yet</p>
            </div>`;
        clearBtn.style.display = 'none';
        actionButtons.style.display = 'none';
        return;
    }

    clearBtn.style.display = 'block';
    actionButtons.style.display = 'flex';

    container.innerHTML = uploadedPapers.map((paper, i) => `
        <div class="paper-item fade-in">
            <div class="paper-info">
                <span class="paper-index">${String(i + 1).padStart(2, '0')}</span>
                <span class="paper-name" title="${paper}">${paper}</span>
            </div>
            <span class="badge badge-success">indexed</span>
        </div>
    `).join('');
}

function updateStats() {
    const statEl = document.getElementById('stat-papers');
    if (statEl) statEl.textContent = uploadedPapers.length;
}

async function clearAllPapers() {
    if (!confirm('Clear the entire library? This cannot be undone.')) return;

    try {
        await clearPapers();
        uploadedPapers = [];
        renderPapers();
        updateStats();
        showToast('Library cleared', 'success');
    } catch (error) {
        showToast('Failed to clear library', 'error');
    }
}