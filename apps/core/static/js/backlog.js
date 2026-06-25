document.addEventListener('DOMContentLoaded', function() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

    /* ─── Drag-and-drop reorder ─── */
    var tbody = document.getElementById('backlogBody');
    if (tbody) {
        var draggedRow = null;

        tbody.addEventListener('dragstart', function(e) {
            var row = e.target.closest('tr');
            if (!row) return;
            draggedRow = row;
            row.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', row.dataset.taskId);
        });

        tbody.addEventListener('dragend', function() {
            if (draggedRow) draggedRow.classList.remove('dragging');
            draggedRow = null;
            tbody.querySelectorAll('.drag-over').forEach(function(el) { el.classList.remove('drag-over'); });
        });

        tbody.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            var target = e.target.closest('tr');
            if (!target || target === draggedRow) return;
            target.classList.add('drag-over');

            var rect = target.getBoundingClientRect();
            var mid = rect.top + rect.height / 2;
            if (e.clientY < mid) {
                target.parentNode.insertBefore(draggedRow, target);
            } else {
                target.parentNode.insertBefore(draggedRow, target.nextSibling);
            }
        });

        tbody.addEventListener('dragleave', function(e) {
            var target = e.target.closest('tr');
            if (target) target.classList.remove('drag-over');
        });

        tbody.addEventListener('drop', function(e) {
            e.preventDefault();
            tbody.querySelectorAll('.drag-over').forEach(function(el) { el.classList.remove('drag-over'); });
            reorderBacklog();
        });
    }

    function reorderBacklog() {
        if (!tbody) return;
        var rows = tbody.querySelectorAll('tr');
        var order = Array.from(rows).map(function(r, i) { return r.dataset.taskId; }).filter(Boolean);
        if (order.length < 2) return;
        fetch('/backlog/reorder/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({order: order})
        })
        .then(function(r) { return r.json(); })
        .then(function(d) {
            if (d.success) showToast('Orden actualizado');
            else showToast(d.error || 'Error al reordenar', 'error');
        })
        .catch(function() { showToast('Error de conexion', 'error'); });
    }

    /* ─── Quick Create Modal ─── */
    var quickForm = document.getElementById('quickTaskForm');
    var quickBtn = document.getElementById('quickTaskBtn');
    var quickModalEl = document.getElementById('quickTaskModal');

    function openQuickModal() {
        if (!quickModalEl) return;
        var modal = new bootstrap.Modal(quickModalEl);
        modal.show();
        setTimeout(function() {
            var input = quickModalEl.querySelector('input[name="title"]');
            if (input) input.focus();
        }, 300);
    }

    if (quickBtn) quickBtn.addEventListener('click', openQuickModal);

    if (quickForm) {
        quickForm.addEventListener('submit', function(e) {
            e.preventDefault();
            var btn = this.querySelector('[type="submit"]');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

            var formData = new URLSearchParams(new FormData(this));
            formData.set('status', 'backlog');

            fetch('/task/quick-create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body: formData
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.success) {
                    var modal = bootstrap.Modal.getInstance(quickModalEl);
                    if (modal) modal.hide();
                    showToast('Tarea creada: ' + data.task.title);
                    setTimeout(function() { location.reload(); }, 300);
                } else {
                    showToast(data.error || 'Error al crear tarea', 'error');
                }
            })
            .catch(function() { showToast('Error de conexion', 'error'); })
            .finally(function() {
                btn.disabled = false;
                btn.innerHTML = 'Crear Tarea';
            });
        });
    }

    /* ─── Keyboard Shortcuts ─── */
    document.addEventListener('keydown', function(e) {
        var tag = e.target.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

        if (e.key === 'c' || e.key === 'C') {
            e.preventDefault();
            openQuickModal();
        }
    });


});
