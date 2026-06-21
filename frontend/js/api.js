// Generate or retrieve a persistent anonymous user ID for this browser.
// This is NOT authentication — it's a private-by-default identifier so each
// visitor's uploaded papers stay separate from everyone else's.
function getUserId() {
    let userId = localStorage.getItem('researchmind_user_id');
    if (!userId) {
        userId = 'u_' + crypto.randomUUID();
        localStorage.setItem('researchmind_user_id', userId);
    }
    return userId;
}

const USER_ID = getUserId();

// api.js - All backend API calls

const API_BASE = 'https://debjit-007-researchmind-ai-backend.hf.space';

// ── Toast Notifications ──────────────────────────────────

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container') 
        || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    const icons = { success: '✅', error: '❌', warning: '⚠️' };
    
    toast.innerHTML = `
        <span>${icons[type] || '📢'}</span>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

// ── API Functions ────────────────────────────────────────

async function apiRequest(endpoint, method = 'GET', body = null, isFile = false) {
    try {
        const options = {
            method,
            headers: isFile ? { 'X-User-Id': USER_ID } : {
                'Content-Type': 'application/json',
                'X-User-Id': USER_ID
            }
        };

        if (body) {
            options.body = isFile ? body : JSON.stringify(body);
        }

        const response = await fetch(`${API_BASE}${endpoint}`, options);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Request failed');
        }

        return data;
    } catch (error) {
        console.error(`API Error [${endpoint}]:`, error);
        throw error;
    }
}

// Get all uploaded papers
async function getPapers() {
    return await apiRequest('/api/papers');
}

// Upload a PDF paper
async function uploadPaper(file) {
    const formData = new FormData();
    formData.append('file', file);
    return await apiRequest('/api/upload', 'POST', formData, true);
}

// Ask a question
async function askQuestion(question, topK = 5, paperFilter = null) {
    return await apiRequest('/api/ask', 'POST', {
        question,
        top_k: topK,
        paper_filter: paperFilter
    });
}


// Summarize a paper
async function summarizePaper(paperName) {
    return await apiRequest('/api/summarize', 'POST', { paper_name: paperName });
}

// Extract from paper
async function extractFromPaper(paperName, extractType) {
    return await apiRequest('/api/extract', 'POST', {
        paper_name: paperName,
        extract_type: extractType
    });
}

// Compare papers
async function comparePapers(paperNames) {
    return await apiRequest('/api/compare', 'POST', { paper_names: paperNames });
}

// Analyze gaps
async function analyzeGaps(paperNames) {
    return await apiRequest('/api/gaps', 'POST', { paper_names: paperNames });
}

// Clear all papers
async function clearPapers() {
    return await apiRequest('/api/papers', 'DELETE');
}

// ── Shared UI Helpers ────────────────────────────────────

function setLoading(btnId, loading, text = '') {
    const btn = document.getElementById(btnId);
    if (!btn) return;
    
    if (loading) {
        btn.disabled = true;
        btn.dataset.originalText = btn.innerHTML;
        btn.innerHTML = `<div class="spinner"></div> ${text || 'Processing...'}`;
    } else {
        btn.disabled = false;
        btn.innerHTML = btn.dataset.originalText || text;
    }
}

function formatMarkdown(text) {
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/^### (.*)/gm, '<h3>$1</h3>')
        .replace(/^## (.*)/gm, '<h2>$1</h2>')
        .replace(/^# (.*)/gm, '<h1>$1</h1>')
        .replace(/^- (.*)/gm, '<li>$1</li>')
        .replace(/\n/g, '<br>');
}

function renderCitations(sources) {
    if (!sources || sources.length === 0) return '';
    
    return sources.map((source, i) => `
        <div class="citation-card fade-in">
            <div class="citation-header">
                <span class="citation-source">📄 ${source.document}</span>
                <span class="citation-page">Page ${source.page}</span>
            </div>
            <div class="citation-snippet">"${source.snippet}"</div>
        </div>
    `).join('');
}

// Load papers into a select dropdown
async function loadPapersIntoSelect(selectId, placeholder = 'Select a paper...') {
    const select = document.getElementById(selectId);
    if (!select) return;
    
    try {
        const data = await getPapers();
        select.innerHTML = `<option value="">${placeholder}</option>`;
        
        data.papers.forEach(paper => {
            const option = document.createElement('option');
            option.value = paper;
            option.textContent = paper;
            select.appendChild(option);
        });
        
        return data.papers;
    } catch (error) {
        showToast('Failed to load papers', 'error');
        return [];
    }
}