// ============================================
// 🎬 AI FILM ANALYZER - MAIN JAVASCRIPT
// Netflix + Letterboxd + Glassmorphism
// ============================================

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Initialize App
function initializeApp() {
    setupChatModal();
    setupAiStudio();
    setupAdminTools();
    setupAdminDrawer();
    setupAnalysisButtons();
    setupCarousel();
    setupFormValidation();
}

// ============================================
// AI CHAT MODAL
// ============================================

let chatVisible = false;

function setupChatModal() {
    const chatBtn = document.getElementById('ai-chat-btn');
    const chatModal = document.getElementById('chat-modal');
    const chatClose = document.getElementById('chat-close');
    const chatSend = document.getElementById('chat-send');
    const chatInput = document.getElementById('chat-input');

    if (!chatBtn) return;

    // Toggle chat modal
    chatBtn.addEventListener('click', function() {
        chatVisible = !chatVisible;
        if (chatModal) {
            chatModal.style.display = chatVisible ? 'flex' : 'none';
            if (chatVisible) {
                chatInput.focus();
            }
        }
    });

    // Close button
    if (chatClose) {
        chatClose.addEventListener('click', function() {
            chatVisible = false;
            chatModal.style.display = 'none';
        });
    }

    // Send message
    if (chatSend && chatInput) {
        chatSend.addEventListener('click', sendChatMessage);
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }
}

function setupAiStudio() {
    const form = document.getElementById('ai-studio-form');
    const input = document.getElementById('ai-studio-input');
    const conversation = document.getElementById('ai-conversation');
    const clearBtn = document.getElementById('ai-clear-btn');
    const chips = document.querySelectorAll('.prompt-chip');

    if (!form || !input || !conversation) return;

    chips.forEach(chip => {
        chip.addEventListener('click', function() {
            input.value = this.dataset.prompt || '';
            input.focus();
        });
    });

    if (clearBtn) {
        clearBtn.addEventListener('click', function() {
            conversation.innerHTML = '';
            const welcome = document.createElement('div');
            welcome.className = 'message ai';
            welcome.textContent = 'Yeni bir sohbet baslatildi. Detayli bir film istegi yazabilirsin.';
            conversation.appendChild(welcome);
        });
    }

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const message = input.value.trim();
        if (!message) return;

        const userMsg = document.createElement('div');
        userMsg.className = 'message user';
        userMsg.textContent = message;
        conversation.appendChild(userMsg);
        conversation.scrollTop = conversation.scrollHeight;

        input.value = '';

        const loadingMsg = document.createElement('div');
        loadingMsg.className = 'message ai';
        loadingMsg.textContent = 'AI dusunuyor...';
        conversation.appendChild(loadingMsg);
        conversation.scrollTop = conversation.scrollHeight;

        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: 'question=' + encodeURIComponent(message)
        })
        .then(response => response.json())
        .then(data => {
            loadingMsg.textContent = data.response || 'Uygun bir cevap olusturulamadi. Lutfen yeniden dene.';
            if (Array.isArray(data.movies) && data.movies.length > 0) {
                const moviesWrap = document.createElement('div');
                moviesWrap.className = 'ai-movie-results';
                moviesWrap.innerHTML = data.movies.map(movie => {
                    const poster = movie.poster_path
                        ? `https://image.tmdb.org/t/p/w300${movie.poster_path}`
                        : '';
                    const year = movie.release_date ? String(movie.release_date).slice(0, 4) : '';
                    const rating = movie.vote_average ? Number(movie.vote_average).toFixed(1) : '0.0';
                    return `
                        <a class="ai-movie-card" href="/movie/${movie.id}">
                            <div class="ai-movie-poster">
                                ${poster
                                    ? `<img src="${poster}" alt="${movie.title}">`
                                    : `<div class="ai-movie-fallback">🎬</div>`}
                            </div>
                            <div class="ai-movie-info">
                                <div class="ai-movie-title">${movie.title}</div>
                                <div class="ai-movie-meta">⭐ ${rating}${year ? ` • ${year}` : ''}</div>
                            </div>
                        </a>
                    `;
                }).join('');
                conversation.appendChild(moviesWrap);
            }
            conversation.scrollTop = conversation.scrollHeight;
        })
        .catch(() => {
            loadingMsg.textContent = 'Baglanti hatasi olustu. Birazdan tekrar deneyebiliriz.';
            conversation.scrollTop = conversation.scrollHeight;
        });
    });
}

function setupAdminTools() {
    const userSearch = document.getElementById('admin-user-search');
    const userRows = document.querySelectorAll('.admin-user-row');
    const reviewFilter = document.getElementById('admin-review-rating-filter');
    const reviewRows = document.querySelectorAll('.admin-review-row');

    if (userSearch && userRows.length) {
        userSearch.addEventListener('input', function() {
            const query = this.value.trim().toLowerCase();
            userRows.forEach(row => {
                const haystack = row.dataset.search || '';
                row.style.display = haystack.includes(query) ? '' : 'none';
            });
        });
    }

    if (reviewFilter && reviewRows.length) {
        reviewFilter.addEventListener('change', function() {
            const minRating = Number(this.value || 0);
            reviewRows.forEach(row => {
                const rating = Number(row.dataset.rating || 0);
                row.style.display = !minRating || rating >= minRating ? '' : 'none';
            });
        });
    }
}

function setupAdminDrawer() {
    const drawer = document.getElementById('admin-quick-drawer');
    const toggleBtn = document.getElementById('admin-drawer-toggle');
    const closeBtn = document.getElementById('admin-drawer-close');
    if (!drawer || !toggleBtn) return;

    toggleBtn.addEventListener('click', () => {
        drawer.classList.add('open');
    });

    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            drawer.classList.remove('open');
        });
    }

    document.addEventListener('click', (event) => {
        if (!drawer.classList.contains('open')) return;
        if (drawer.contains(event.target) || toggleBtn.contains(event.target)) return;
        drawer.classList.remove('open');
    });
}

function sendChatMessage() {
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const message = chatInput.value.trim();

    if (!message) return;

    // Add user message to UI
    const userMsg = document.createElement('div');
    userMsg.className = 'message user';
    userMsg.textContent = message;
    chatMessages.appendChild(userMsg);

    // Send to server
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: 'question=' + encodeURIComponent(message)
    })
    .then(response => response.json())
    .then(data => {
        const aiMsg = document.createElement('div');
        aiMsg.className = 'message ai';
        aiMsg.textContent = data.response || 'Üzgünüm, bir hata oluştu.';
        chatMessages.appendChild(aiMsg);

        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    })
    .catch(error => {
        console.error('Chat Error:', error);
        const errorMsg = document.createElement('div');
        errorMsg.className = 'message ai';
        errorMsg.textContent = 'Üzgünüm, bir hata oluştu. Lütfen tekrar deneyin.';
        chatMessages.appendChild(errorMsg);
    });

    chatInput.value = '';
}

// ============================================
// FILM ANALYSIS (AI/Gemini Integration)
// ============================================

function setupAnalysisButtons() {
    const analysisButtons = document.querySelectorAll('.btn-analysis');
    analysisButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const movieId = this.dataset.movieId;
            const movieTitle = this.dataset.movieTitle;
            showAnalysisModal(movieId, movieTitle);
        });
    });
}

function showAnalysisModal(movieId, movieTitle) {
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <button class="modal-close" onclick="this.parentElement.parentElement.remove()">✕</button>
            <div class="modal-header">🤖 Gemini Analizi: ${movieTitle}</div>
            <div class="modal-body" style="margin-top: 20px;">
                <div class="loading" style="margin: 20px auto; display: block;"></div>
                <p style="text-align: center; color: var(--text-muted);">Analiz yapılıyor...</p>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    fetch(`/api/analyze/${movieId}`)
        .then(async (response) => {
            const data = await response.json().catch(() => ({}));
            const body = modal.querySelector('.modal-body');

            if (!response.ok || data.error) {
                body.innerHTML = '';
                const box = document.createElement('div');
                box.className = 'alert alert-danger';
                box.textContent =
                    data.error ||
                    `Analiz alınamadı (HTTP ${response.status}).`;
                body.appendChild(box);
                return;
            }

            body.innerHTML = '';
            const wrap = document.createElement('div');
            wrap.style.background = 'rgba(56, 189, 248, 0.1)';
            wrap.style.borderLeft = '4px solid var(--color-primary)';
            wrap.style.padding = '16px';
            wrap.style.borderRadius = '8px';

            const tagEl = document.createElement('div');
            tagEl.style.fontWeight = '700';
            tagEl.style.color = 'var(--color-primary)';
            tagEl.style.marginBottom = '8px';
            tagEl.textContent = `ETİKET: ${data.tag || 'Genel'}`;

            const analysisEl = document.createElement('div');
            analysisEl.style.color = 'var(--text-secondary)';
            analysisEl.style.lineHeight = '1.6';
            analysisEl.textContent = data.analysis || '';

            wrap.appendChild(tagEl);
            wrap.appendChild(analysisEl);
            body.appendChild(wrap);
        })
        .catch(() => {
            const body = modal.querySelector('.modal-body');
            body.innerHTML = `
                <div class="alert alert-danger">
                    Analiz alınamadı. Lütfen daha sonra tekrar deneyin.
                </div>
            `;
        });

    // Close on overlay click
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// ============================================
// CAROUSEL/HORIZONTAL SCROLL
// ============================================

function setupCarousel() {
    const carousels = document.querySelectorAll('.carousel-container');
    
    carousels.forEach(carousel => {
        let isDown = false;
        let startX;
        let scrollLeft;

        carousel.addEventListener('mousedown', (e) => {
            isDown = true;
            startX = e.pageX - carousel.offsetLeft;
            scrollLeft = carousel.scrollLeft;
        });

        carousel.addEventListener('mouseleave', () => {
            isDown = false;
        });

        carousel.addEventListener('mouseup', () => {
            isDown = false;
        });

        carousel.addEventListener('mousemove', (e) => {
            if (!isDown) return;
            e.preventDefault();
            const x = e.pageX - carousel.offsetLeft;
            const walk = (x - startX) * 1;
            carousel.scrollLeft = scrollLeft - walk;
        });
    });
}

// ============================================
// FORM VALIDATION
// ============================================

function setupFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const inputs = form.querySelectorAll('input[required], textarea[required]');
            let isValid = true;

            inputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.style.borderColor = 'var(--color-danger)';
                } else {
                    input.style.borderColor = '';
                }
            });

            if (!isValid) {
                e.preventDefault();
            }
        });
    });
}

// ============================================
// ADD TO WATCHLIST (AJAX)
// ============================================

function addToWatchlist(movieId, button) {
    fetch(`/add-to-watchlist/${movieId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            button.textContent = '✓ Eklendi';
            button.disabled = true;
            button.style.opacity = '0.6';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('İzleme listesine eklenemedi.');
    });
}

// ============================================
// UTILITIES
// ============================================

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('tr-TR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// ============================================
// SCROLL ANIMATION
// ============================================

const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
};

const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
            observer.unobserve(entry.target);
        }
    });
}, observerOptions);

document.addEventListener('DOMContentLoaded', function() {
    const elements = document.querySelectorAll('.film-card, .carousel-section');
    elements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
        observer.observe(el);
    });
});

console.log('🎬 AI Film Analyzer - JavaScript Loaded');
