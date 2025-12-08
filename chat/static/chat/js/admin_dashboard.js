// c:\Users\patel\sheryansh\chatbot\chatbot\chat\static\chat\js\admin_dashboard.js
function initializeAdminSidebar() {
    const sidebarToggle = document.getElementById('admin-sidebar-toggle');
    const adminLayout = document.querySelector('.admin-layout');
    const adminSidebar = document.getElementById('admin-sidebar');

    if (sidebarToggle && adminLayout && adminSidebar) {
        // Ensure previous listeners are removed to prevent duplicates if called multiple times
        if (sidebarToggle._hasClickListener) {
            sidebarToggle.removeEventListener('click', sidebarToggle._clickListener);
        }
        if (document._hasClickListener) {
            document.removeEventListener('click', document._clickListener);
        }

        const clickListener = function() {
            adminLayout.classList.toggle('sidebar-collapsed');
        };
        sidebarToggle.addEventListener('click', clickListener);
        sidebarToggle._clickListener = clickListener;
        sidebarToggle._hasClickListener = true;

        const documentClickListener = function(event) {
            // Check if the sidebar is currently open (not collapsed)
            const isSidebarOpen = !adminLayout.classList.contains('sidebar-collapsed');

            // Only close sidebar on outside click if on small screen AND sidebar is open
            if (window.innerWidth <= 900 && isSidebarOpen) {
                // Check if the click is outside the sidebar and outside the toggle button
                if (!adminSidebar.contains(event.target) && !sidebarToggle.contains(event.target)) {
                    adminLayout.classList.add('sidebar-collapsed'); // Collapse the sidebar
                }
            }
        };
        document.addEventListener('click', documentClickListener);
        document._clickListener = documentClickListener;
        document._hasClickListener = true;

        // Initial check for large screens to ensure sidebar is visible and toggle is hidden
        function handleResize() {
            if (window.innerWidth > 900) {
                adminLayout.classList.remove('sidebar-collapsed'); // Ensure sidebar is open on large screens
            }
        }

        window.addEventListener('resize', handleResize);
        handleResize(); // Call on load
    } else {
        console.warn("Admin sidebar elements not found. Sidebar toggle functionality may not work.");
    }
}

// Run on DOMContentLoaded (initial load)
document.addEventListener('DOMContentLoaded', initializeAdminSidebar);

// Run on window.onload (after all resources are loaded)
// This helps if other scripts dynamically add/modify elements after DOMContentLoaded
window.addEventListener('load', initializeAdminSidebar);
