function initCommonUI() {
    const userBtn = document.getElementById('userDropdownBtn');
    const userMenu = document.getElementById('userMenu');

    if (userBtn && userMenu && !userBtn.dataset.initialized) {
        userBtn.dataset.initialized = 'true';

        // Intercept clicks on userBtn during the CAPTURE phase
        // This stops the event from propagating to conflicting inline scripts.
        userBtn.addEventListener('click', (e) => {
            // DO NOT intercept clicks originating from inside the menu itself (e.g. links)
            if (userMenu.contains(e.target)) {
                return;
            }
            e.stopPropagation();
            e.stopImmediatePropagation();
            userMenu.classList.toggle('show');
        }, true);

        // Hide menu when clicking anywhere else
        document.addEventListener('click', () => {
            userMenu.classList.remove('show');
        });
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCommonUI);
} else {
    initCommonUI();
}
