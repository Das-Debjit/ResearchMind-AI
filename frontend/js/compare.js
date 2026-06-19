// compare.js - Compare & Gap Analysis page logic

let currentMode = 'compare';

document.addEventListener('DOMContentLoaded', async () => {
    await loadPapersIntoMultiselect();
});

async function loadPapersIntoMultiselect() {
    const container = document.getElementById('papers-multiselect-container');

    try {
        const data = await getPapers();

        if (!data.papers || data.papers.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="padding:24px 0;">
                    <p>No papers yet</p>
                </div>`;
            return;
        }

        container.innerHTML = data.papers.map((paper) => `
            <label class="multiselect-item">
                <input type="checkbox" value="${paper}" onchange="updateSelectedCount()">
                <span>${paper}</span>
            </label>
        `).join('');

    } catch (error) {
        showToast('Failed to load papers', 'error');
    }
}

function getSelectedPapers() {
    const checkboxes = document.querySelectorAll('#papers-multiselect-container input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

function updateSelectedCount() {
    const count = getSelectedPapers().length;
    document.getElementById('selected-count').textContent = `${count} selected`;
}

function switchMode(mode) {
    currentMode = mode;
    document.getElementById('tab-compare').classList.toggle('active', mode === 'compare');
    document.getElementById('tab-gaps').classList.toggle('active', mode === 'gaps');

    const btn = document.getElementById('action-btn');
    btn.textContent = mode === 'compare' ? 'Compare selected papers' : 'Analyze research gaps';

    document.getElementById('results-area').innerHTML = '';
}

async function handleAction() {
    const selectedPapers = getSelectedPapers();

    if (currentMode === 'compare' && selectedPapers.length < 2) {
        showToast('Select at least 2 papers to compare', 'warning');
        return;
    }

    if (currentMode === 'gaps' && selectedPapers.length < 1) {
        showToast('Select at least 1 paper', 'warning');
        return;
    }

    const resultsArea = document.getElementById('results-area');
    const loadingMsg = currentMode === 'compare'
        ? 'Comparing approach, data, and results...'
        : 'Looking for gaps and open questions...';

    resultsArea.innerHTML = `
        <div class="answer-box fade-in">
            <div style="display:flex; align-items:center; gap:10px;">
                <div class="spinner"></div>
                <span style="color:var(--text-dim); font-size:13.5px;">${loadingMsg}</span>
            </div>
        </div>
    `;

    setLoading('action-btn', true, 'Working...');

    try {
        let result;

        if (currentMode === 'compare') {
            result = await comparePapers(selectedPapers);
            resultsArea.innerHTML = `
                <div class="answer-box fade-in">
                    <h4>Comparison — ${selectedPapers.length} papers</h4>
                    <div class="answer-text">${formatMarkdown(result.comparison)}</div>
                </div>
            `;
        } else {
            result = await analyzeGaps(selectedPapers);
            resultsArea.innerHTML = `
                <div class="answer-box fade-in">
                    <h4>Research gap analysis</h4>
                    <div class="answer-text">${formatMarkdown(result.gaps)}</div>
                </div>
            `;
        }

    } catch (error) {
        resultsArea.innerHTML = `
            <div class="answer-box fade-in" style="border-left-color:#C77B6B">
                <h4 style="color:#C77B6B">Something went wrong</h4>
                <div class="answer-text">${error.message || 'Try again in a moment'}</div>
            </div>
        `;
        showToast('Action failed', 'error');
    }

    const btnLabel = currentMode === 'compare' ? 'Compare selected papers' : 'Analyze research gaps';
    setLoading('action-btn', false, btnLabel);
}