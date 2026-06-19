// analyze.js - Analyze page logic

let currentExtractType = 'methodology';

document.addEventListener('DOMContentLoaded', async () => {
    await loadPapersIntoSelect('paper-select', 'Choose a paper...');
});

function switchTab(tab) {
    document.getElementById('tab-summary').classList.toggle('active', tab === 'summary');
    document.getElementById('tab-extract').classList.toggle('active', tab === 'extract');
    document.getElementById('panel-summary').style.display = tab === 'summary' ? 'block' : 'none';
    document.getElementById('panel-extract').style.display = tab === 'extract' ? 'block' : 'none';
}

function selectExtractType(el) {
    document.querySelectorAll('.extract-type-card').forEach(card => card.classList.remove('active'));
    el.classList.add('active');
    currentExtractType = el.dataset.type;

    const labels = {
        methodology: 'Extract methodology',
        findings: 'Extract key findings',
        future_work: 'Extract future work'
    };
    document.getElementById('extract-btn').textContent = labels[currentExtractType];
}

function getSelectedPaper() {
    return document.getElementById('paper-select').value;
}

function showLoadingResult(containerId, message) {
    document.getElementById(containerId).innerHTML = `
        <div class="answer-box fade-in">
            <div style="display:flex; align-items:center; gap:10px;">
                <div class="spinner"></div>
                <span style="color:var(--text-dim); font-size:13.5px;">${message}</span>
            </div>
        </div>
    `;
}

function showErrorResult(containerId, message) {
    document.getElementById(containerId).innerHTML = `
        <div class="answer-box fade-in" style="border-left-color:#C77B6B">
            <h4 style="color:#C77B6B">Couldn't complete this</h4>
            <div class="answer-text">${message}</div>
        </div>
    `;
}

async function handleSummarize() {
    const paper = getSelectedPaper();

    if (!paper) {
        showToast('Choose a paper first', 'warning');
        return;
    }

    setLoading('summarize-btn', true, 'Working...');
    showLoadingResult('summary-results', 'Reading the paper and writing a summary...');

    try {
        const result = await summarizePaper(paper);

        document.getElementById('summary-results').innerHTML = `
            <div class="answer-box fade-in">
                <h4>Summary — ${paper}</h4>
                <div class="answer-text">${formatMarkdown(result.summary)}</div>
            </div>
        `;

    } catch (error) {
        showErrorResult('summary-results', error.message || 'Failed to generate a summary');
        showToast('Summarization failed', 'error');
    }

    setLoading('summarize-btn', false, 'Generate summary');
}

async function handleExtract() {
    const paper = getSelectedPaper();

    if (!paper) {
        showToast('Choose a paper first', 'warning');
        return;
    }

    const typeLabels = {
        methodology: 'methodology',
        findings: 'key findings',
        future_work: 'future work'
    };

    setLoading('extract-btn', true, 'Working...');
    showLoadingResult('extract-results', `Pulling out the ${typeLabels[currentExtractType]}...`);

    try {
        const result = await extractFromPaper(paper, currentExtractType);
        const content = result.methodology || result.findings || result.future_work;
        const titles = { methodology: 'Methodology', findings: 'Key findings', future_work: 'Future work' };

        document.getElementById('extract-results').innerHTML = `
            <div class="answer-box fade-in">
                <h4>${titles[currentExtractType]} — ${paper}</h4>
                <div class="answer-text">${formatMarkdown(content)}</div>
            </div>
        `;

    } catch (error) {
        showErrorResult('extract-results', error.message || 'Failed to extract content');
        showToast('Extraction failed', 'error');
    }

    const labels = {
        methodology: 'Extract methodology',
        findings: 'Extract key findings',
        future_work: 'Extract future work'
    };
    setLoading('extract-btn', false, labels[currentExtractType]);
}