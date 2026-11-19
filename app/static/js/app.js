// ShopPilot - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Theme toggle
    const root = document.documentElement;
    const themeBtn = document.getElementById('theme');

    try {
        const saved = localStorage.getItem('theme');
        if (saved) root.setAttribute('data-theme', saved);
    } catch (e) {}

    function syncIcon() {
        if (!themeBtn) return;
        themeBtn.innerHTML = root.getAttribute('data-theme') === 'dark'
            ? '<i class="fa-regular fa-sun"></i>'
            : '<i class="fa-regular fa-moon"></i>';
    }
    syncIcon();

    if (themeBtn) {
        themeBtn.addEventListener('click', function() {
            const isDark = root.getAttribute('data-theme') === 'dark';
            root.setAttribute('data-theme', isDark ? 'light' : 'dark');
            try { localStorage.setItem('theme', isDark ? 'light' : 'dark'); } catch (e) {}
            syncIcon();
        });
    }

    // Mobile sidebar toggle
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const sidebar = document.querySelector('.sidebar');
    const mobileOverlay = document.getElementById('mobileOverlay');

    function toggleMobileMenu() {
        if (!sidebar || !mobileOverlay) return;
        const isOpen = sidebar.classList.contains('open');
        if (isOpen) {
            sidebar.classList.remove('open');
            mobileOverlay.style.display = 'none';
        } else {
            sidebar.classList.add('open');
            mobileOverlay.style.display = 'block';
        }
    }

    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', toggleMobileMenu);
    }
    if (mobileOverlay) {
        mobileOverlay.addEventListener('click', function() {
            if (sidebar) sidebar.classList.remove('open');
            mobileOverlay.style.display = 'none';
        });
    }

    // Auto-dismiss alerts after 8 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(function() { if (alert.parentElement) alert.remove(); }, 500);
        });
    }, 8000);

    // Confirm destructive actions
    const deleteForms = document.querySelectorAll('form[data-confirm]');
    deleteForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const msg = form.getAttribute('data-confirm') || 'آیا از انجام این عملیات اطمینان دارید؟';
            if (!confirm(msg)) {
                e.preventDefault();
                return false;
            }
        });
    });

    // Order status change via select
    const statusSelects = document.querySelectorAll('.order-status-select');
    statusSelects.forEach(function(select) {
        select.addEventListener('change', function() {
            const orderId = select.getAttribute('data-order-id');
            const newStatus = select.value;
            const form = document.getElementById('statusForm_' + orderId);
            if (form) {
                const input = form.querySelector('input[name="status"]');
                if (input) input.value = newStatus;
                form.submit();
            }
        });
    });

    // Print-friendly: hide sidebar on print
    window.addEventListener('beforeprint', function() {
        const sb = document.querySelector('.sidebar');
        if (sb) sb.style.display = 'none';
    });
    window.addEventListener('afterprint', function() {
        const sb = document.querySelector('.sidebar');
        if (sb) sb.style.display = '';
    });
});

// Helper: format number with Persian/Arabic digits
function toPersianDigits(num) {
    const persianDigits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹'];
    return num.toString().replace(/\d/g, d => persianDigits[parseInt(d)]);
}

// Helper: format currency with comma separators
function formatCurrency(amount) {
    return amount.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}