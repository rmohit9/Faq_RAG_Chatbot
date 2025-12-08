// Mobile menu toggle and navigation functionality
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenu = document.getElementById('mobileMenu');
    const navLinks = document.getElementById('navLinks');
    const body = document.body;

    // Handle Home button click
    const homeButton = document.querySelector('.nav-link[href="#"]');
    if (homeButton) {
        homeButton.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = '/';
            // Close mobile menu if open
            if (mobileMenu && navLinks) {
                mobileMenu.classList.remove('active');
                navLinks.classList.remove('active');
                body.classList.remove('nav-open');
            }
        });
    }

    // Mobile menu toggle
    if (mobileMenu && navLinks) {
        mobileMenu.addEventListener('click', function() {
            mobileMenu.classList.toggle('active');
            navLinks.classList.toggle('active');
            body.classList.toggle('nav-open');
        });

        // Close mobile menu when clicking on a nav link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', function(e) {
                // Don't prevent default for regular links
                if (link.getAttribute('href') === '#') {
                    e.preventDefault();
                    return;
                }
                
                mobileMenu.classList.remove('active');
                navLinks.classList.remove('active');
                body.classList.remove('nav-open');
                
                // Update active state
                document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }

    // Add active class to current page link
    const currentPage = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        // For home page, check if we're at the root
        if ((currentPage === '/' && link.getAttribute('href') === '#') || 
            link.getAttribute('href') === currentPage) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    // Handle browser back/forward navigation
    window.addEventListener('popstate', function() {
        const currentPath = window.location.pathname;
        document.querySelectorAll('.nav-link').forEach(link => {
            if ((currentPath === '/' && link.getAttribute('href') === '#') || 
                link.getAttribute('href') === currentPath) {
                document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
                link.classList.add('active');
            }
        });
    });
});
