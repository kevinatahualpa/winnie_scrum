function switchTab(tabId) {
    const tabsContainer = document.querySelector('.auth-tabs');
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));

    document.getElementById(tabId).classList.add('active');

    const tabs = ['login', 'register'];
    const idx = tabs.indexOf(tabId);
    if (idx >= 0) {
        document.querySelectorAll('.auth-tab')[idx].classList.add('active');
        if (tabsContainer) tabsContainer.style.display = '';
    } else if (tabId === 'forgot') {
        if (tabsContainer) tabsContainer.style.display = 'none';
    }
}

function togglePw(inputId, btn) {
    const input = document.getElementById(inputId);
    const icon = btn.querySelector('i');
    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.replace('fa-eye', 'fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.replace('fa-eye-slash', 'fa-eye');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    if (typeof SHOW_REGISTER !== 'undefined' && SHOW_REGISTER) {
        switchTab('register');
    }
});
