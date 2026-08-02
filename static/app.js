const API_BASE = '/api';
let currentPage = 0;
const PAGE_SIZE = 10;

const form = document.getElementById('ticketForm');
const submitBtn = document.getElementById('submitBtn');
const submitText = document.getElementById('submitText');
const result = document.getElementById('result');
const ticketsList = document.getElementById('ticketsList');
const errorBanner = document.getElementById('errorBanner');

// Form submission
form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const subject = document.getElementById('subject').value;
    const body = document.getElementById('body').value;

    submitBtn.disabled = true;
    submitText.innerHTML = '<span class="loading"></span>Submitting...';
    result.classList.remove('show');

    try {
        const response = await fetch(`${API_BASE}/tickets`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ subject, body }),
        });

        if (!response.ok) {
            const error = await response.json();
            if (response.status === 503) {
                showApiKeyError(error.detail);
            } else {
                showError(`Error: ${error.detail || 'Failed to submit ticket'}`);
            }
            return;
        }

        const ticket = await response.json();

        // Display result
        displayResult(ticket);

        // Clear form
        form.reset();

        // Reload tickets list
        currentPage = 0;
        await loadTickets();

    } catch (error) {
        console.error('Error:', error);
        showError('Failed to submit ticket. Please try again.');
    } finally {
        submitBtn.disabled = false;
        submitText.textContent = 'Submit Ticket';
    }
});

function displayResult(ticket) {
    const categoryBadge = document.getElementById('categoryBadge');
    const priorityBadge = document.getElementById('priorityBadge');
    const summary = document.getElementById('summary');
    const suggestedResponse = document.getElementById('suggestedResponse');

    categoryBadge.innerHTML = `<span class="badge badge-category">${escapeHtml(ticket.category)}</span>`;

    const priorityClass = `badge-priority-${ticket.priority}`;
    priorityBadge.innerHTML = `<span class="badge ${priorityClass}">${escapeHtml(ticket.priority.toUpperCase())}</span>`;

    summary.textContent = ticket.summary;
    suggestedResponse.textContent = ticket.suggested_response;

    result.classList.add('show');
}

function showApiKeyError(message) {
    errorBanner.classList.add('show');
    console.error('API Key Error:', message);
}

function showError(message) {
    alert(message);
}

async function loadTickets() {
    try {
        const offset = currentPage * PAGE_SIZE;
        const response = await fetch(`${API_BASE}/tickets?limit=${PAGE_SIZE}&offset=${offset}`);

        if (!response.ok) {
            console.error('Failed to load tickets');
            return;
        }

        const data = await response.json();
        displayTickets(data.tickets, data.total);

    } catch (error) {
        console.error('Error loading tickets:', error);
    }
}

function displayTickets(tickets, total) {
    if (tickets.length === 0) {
        ticketsList.innerHTML = `
            <div class="empty-state">
                <p>No tickets yet. Submit one above to get started.</p>
            </div>
        `;
        return;
    }

    let html = '<div class="tickets-list">';

    for (const ticket of tickets) {
        const date = new Date(ticket.created_at);
        const dateStr = date.toLocaleString();

        html += `
            <div class="ticket-item">
                <div class="ticket-subject">${escapeHtml(ticket.subject)}</div>
                <div class="ticket-meta">
                    <span class="badge badge-category">${escapeHtml(ticket.category)}</span>
                    <span class="badge badge-priority-${ticket.priority}">${escapeHtml(ticket.priority)}</span>
                    <span class="ticket-time">${escapeHtml(dateStr)}</span>
                </div>
            </div>
        `;
    }

    html += '</div>';

    // Add pagination if needed
    const totalPages = Math.ceil(total / PAGE_SIZE);
    if (totalPages > 1) {
        html += '<div class="pagination">';

        if (currentPage > 0) {
            html += `<button onclick="previousPage()">← Previous</button>`;
        }

        for (let i = 0; i < totalPages; i++) {
            const activeClass = i === currentPage ? 'active' : '';
            html += `<button class="${activeClass}" onclick="goToPage(${i})">${i + 1}</button>`;
        }

        if (currentPage < totalPages - 1) {
            html += `<button onclick="nextPage()">Next →</button>`;
        }

        html += '</div>';
    }

    ticketsList.innerHTML = html;
}

function previousPage() {
    if (currentPage > 0) {
        currentPage--;
        loadTickets();
    }
}

function nextPage() {
    currentPage++;
    loadTickets();
}

function goToPage(page) {
    currentPage = page;
    loadTickets();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Load initial tickets
window.addEventListener('load', () => {
    loadTickets();
});
