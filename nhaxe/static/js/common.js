function fixStatusColors() {
    // Find all elements that might be status badges
    const badges = document.querySelectorAll('.status-badge, .detail-badge, [class*="badge"]');
    badges.forEach(badge => {
        const text = badge.textContent.trim().toLowerCase();
        // Check for 'hoan thanh' variations and 'completed'
        if (text.includes('hoàn thành') || 
            (text.includes('hoan') && text.includes('thanh')) || 
            text === 'completed' || 
            text === 'finish') {
            
            badge.style.backgroundColor = '#E8F5E9';
            badge.style.color = '#1B5E20';
            badge.style.padding = '6px 15px';
            badge.style.borderRadius = '20px';
            badge.style.border = 'none';
        }
    });
}

function initCommonUI() {
    const userBtn = document.getElementById('userDropdownBtn');
    const userMenu = document.getElementById('userMenu');

    if (userBtn && userMenu && !userBtn.dataset.initialized) {
        userBtn.dataset.initialized = 'true';
        userBtn.addEventListener('click', (e) => {
            if (userMenu.contains(e.target)) return;
            e.stopPropagation();
            userMenu.classList.toggle('show');
        }, true);
        document.addEventListener('click', () => userMenu.classList.remove('show'));
    }
    
    // Run status color fix
    fixStatusColors();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCommonUI);
} else {
    initCommonUI();
}

// Also run it after a short delay to catch any dynamic content
setTimeout(fixStatusColors, 500);
