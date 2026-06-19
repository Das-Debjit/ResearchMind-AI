// chat.js - Chat page logic

document.addEventListener('DOMContentLoaded', async () => {
    await loadPapersIntoSidebar();
});

async function loadPapersIntoSidebar() {
    const container = document.getElementById('papers-checkboxes');

    try {
        const data = await getPapers();

        if (!data.papers || data.papers.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="padding:16px 0;">
                    <p>No papers yet</p>
                </div>`;
            return;
        }

        container.innerHTML = data.papers.map((paper) => `
            <label class="paper-checkbox">
                <input type="checkbox" value="${paper}" checked>
                <span>${paper}</span>
            </label>
        `).join('');

    } catch (error) {
        showToast('Failed to load papers', 'error');
    }
}

function handleEnter(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleAsk();
    }
}

function askSuggested(el) {
    document.getElementById('question-input').value = el.textContent;
    handleAsk();
}

async function handleAsk() {
    const input = document.getElementById('question-input');
    const question = input.value.trim();

    if (!question) {
        showToast('Type a question first', 'warning');
        return;
    }

    const checkedBoxes = document.querySelectorAll('#papers-checkboxes input[type="checkbox"]:checked');
    const selectedPapers = Array.from(checkedBoxes).map(cb => cb.value);

    if (selectedPapers.length === 0) {
        showToast('Select at least one paper to search', 'warning');
        return;
    }

    const messagesContainer = document.getElementById('chat-messages');

    if (messagesContainer.querySelector('.empty-state')) {
        messagesContainer.innerHTML = '';
    }

    const questionEl = document.createElement('div');
    questionEl.className = 'message-question fade-in';
    questionEl.textContent = question;
    messagesContainer.appendChild(questionEl);

    const answerEl = document.createElement('div');
    answerEl.className = 'fade-in';
    answerEl.innerHTML = `
        <div class="answer-box">
            <div style="display:flex; align-items:center; gap:10px;">
                <div class="spinner"></div>
                <span style="color:var(--text-dim); font-size:13.5px;">Reading through your papers...</span>
            </div>
        </div>
    `;
    messagesContainer.appendChild(answerEl);

    input.value = '';
    setLoading('ask-btn', true, '...');

    window.scrollTo(0, document.body.scrollHeight);

    try {
        const result = await askQuestion(question, 5, selectedPapers);

        answerEl.innerHTML = `
            <div class="answer-box">
                <h4>Answer</h4>
                <div class="answer-text">${formatMarkdown(result.answer)}</div>
            </div>
            ${result.sources && result.sources.length > 0 ? `
                <div style="margin-top:16px;">
                    <h4 style="font-family:'JetBrains Mono',monospace; font-size:11px; color:var(--text-dim); text-transform:uppercase; letter-spacing:0.06em; margin-bottom:12px;">
                        Sources (${result.sources.length})
                    </h4>
                    ${renderCitations(result.sources)}
                </div>
            ` : ''}
        `;

    } catch (error) {
        answerEl.innerHTML = `
            <div class="answer-box" style="border-left-color:#C77B6B">
                <h4 style="color:#C77B6B">Couldn't get an answer</h4>
                <div class="answer-text">${error.message || 'Something went wrong. Try again.'}</div>
            </div>
        `;
        showToast('Failed to get answer', 'error');
    }

    setLoading('ask-btn', false, 'Ask');
    window.scrollTo(0, document.body.scrollHeight);
}