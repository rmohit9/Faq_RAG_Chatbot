document.addEventListener('DOMContentLoaded', function () {
    const navbarToggle = document.getElementById('navbar-toggle');
    const navbarDropdown = document.getElementById('navbar-dropdown');
    if (navbarToggle && navbarDropdown) {
        navbarToggle.addEventListener('click', () => { navbarDropdown.classList.toggle('active'); navbarToggle.classList.toggle('open'); });
        document.addEventListener('click', (e) => { if (!navbarToggle.contains(e.target) && !navbarDropdown.contains(e.target)) { navbarDropdown.classList.remove('active'); navbarToggle.classList.remove('open'); } });
        navbarDropdown.addEventListener('click', (e) => { if (e.target.tagName === 'A') { navbarDropdown.classList.remove('active'); navbarToggle.classList.remove('open'); } });
    }
});