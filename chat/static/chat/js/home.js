// Modal & buttons
const modalOverlay = document.getElementById('modalOverlay');
const modalClose = document.getElementById('modalClose');
const loginBtn = document.getElementById('loginBtn');        // Navbar Login button
const startChatBtn = document.getElementById('startChatBtn'); 
const modalPrimaryBtn = document.getElementById('modalPrimaryBtn'); // Modal Sign Up button
const tryDemoBtn = document.getElementById('tryDemoBtn');

// Navbar Login button: redirect to login page
if (loginBtn) {
    loginBtn.addEventListener('click', () => {
        const url = loginBtn.dataset.url;
        if (url) window.location.href = url;
    });
}

// Start Chat button: open modal
if (startChatBtn) {
    startChatBtn.addEventListener('click', (e) => {
        e.preventDefault();
        modalOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';

        // Update modal primary button text (Sign Up)
        if (modalPrimaryBtn) {
            modalPrimaryBtn.querySelector('span:last-child').textContent = "Sign Up for Free";
        }
    });
}

// Modal primary button: redirect to register page
if (modalPrimaryBtn) {
    modalPrimaryBtn.addEventListener('click', () => {
        const url = modalPrimaryBtn.dataset.url;
        if (url) window.location.href = url;
    });
}

// Try demo button: redirect to chat page
if (tryDemoBtn) {
    tryDemoBtn.addEventListener('click', () => {
        const url = tryDemoBtn.dataset.url;
        if (url) window.location.href = url;
    });
}

// CTA Get Started button: redirect based on authentication
if (ctaBtn) {
    ctaBtn.addEventListener('click', () => {
        const isAuthenticated = ctaBtn.dataset.authenticated === 'true';
        const chatUrl = ctaBtn.dataset.chatUrl;
        const loginUrl = ctaBtn.dataset.loginUrl;

        if (isAuthenticated && chatUrl) {
            window.location.href = chatUrl;
        } else if (!isAuthenticated && loginUrl) {
            window.location.href = loginUrl;
        }
    });
}

// Modal close
function closeModal() {
    modalOverlay.classList.remove('active');
    document.body.style.overflow = '';
}
if (modalClose) modalClose.addEventListener('click', closeModal);

if (modalOverlay) {
    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) closeModal();
    });
}

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modalOverlay.classList.contains('active')) {
        closeModal();
    }
});

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#' && document.querySelector(href)) {
            e.preventDefault();
            const target = document.querySelector(href);
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// ----------------------
// Chat Preview Animation
// ----------------------
document.addEventListener("DOMContentLoaded", () => {
    const bubbles = document.querySelectorAll(".chat-preview .chat-bubble");

    bubbles.forEach((bubble, index) => {
        setTimeout(() => {
            bubble.classList.add("show");
        }, 600 * index); // हर bubble delay से आएगी
    });
});

