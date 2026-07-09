(function() {
    var quickModalEl = document.getElementById('quickTaskModal');
    if (!quickModalEl) return;
    var quickForm = document.getElementById('quickTaskForm');

    function getCsrf() {
        var m = document.querySelector('meta[name="csrf-token"]');
        if (m) return m.getAttribute('content');
        var i = quickForm && quickForm.querySelector('[name="csrfmiddlewaretoken"]');
        return i ? i.value : '';
    }

    window.openQuickTaskModal = function(prefillTitle) {
        var modal = bootstrap.Modal.getOrCreateInstance(quickModalEl);
        var titleInput = quickModalEl.querySelector('input[name="title"]');
        if (titleInput && typeof prefillTitle === 'string') titleInput.value = prefillTitle;
        modal.show();
        setTimeout(function() { if (titleInput) titleInput.focus(); }, 300);
    };

    var createBtn = document.getElementById('topbarCreateBtn');
    if (createBtn) {
        createBtn.addEventListener('click', function() { window.openQuickTaskModal(''); });
    }

    if (quickForm) {
        quickForm.addEventListener('submit', function(e) {
            e.preventDefault();
            var btn = quickModalEl.querySelector('[type="submit"]');
            btn.disabled = true;
            var originalText = btn.innerHTML;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

            var formData = new URLSearchParams(new FormData(this));
            formData.set('status', 'TODO');

            fetch('/task/quick-create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCsrf(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.success) {
                    var modal = bootstrap.Modal.getInstance(quickModalEl);
                    if (modal) modal.hide();
                    quickForm.reset();
                    if (typeof showToast === 'function') showToast('Tarea creada: ' + data.task.title, 'success');
                    setTimeout(function() { location.reload(); }, 500);
                } else {
                    if (typeof showToast === 'function') showToast(data.error || 'Error al crear tarea', 'error');
                }
            })
            .catch(function() {
                if (typeof showToast === 'function') showToast('Error de conexion', 'error');
            })
            .finally(function() {
                btn.disabled = false;
                btn.innerHTML = originalText;
            });
        });
    }
})();
