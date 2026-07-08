document.addEventListener('DOMContentLoaded', function() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '{{ csrf_token }}';
    let draggedCard = null;
    let dropIndicator = null;
    let touchStartX = 0, touchStartY = 0;
    let isDragging = false;

    function getCardCenter(card) {
        const rect = card.getBoundingClientRect();
        return rect.top + rect.height / 2;
    }

    function findInsertPosition(column, mouseY) {
        const cards = Array.from(column.querySelectorAll('.task-card:not(.dragging)'));
        for (let i = 0; i < cards.length; i++) {
            const cardCenter = getCardCenter(cards[i]);
            if (mouseY < cardCenter) {
                return cards[i];
            }
        }
        return null;
    }

    function createDropIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'drop-indicator';
        return indicator;
    }

    function setupDragEvents(card) {
        card.addEventListener('dragstart', function(e) {
            draggedCard = this;
            this.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/plain', this.dataset.taskId);
            setTimeout(() => this.style.opacity = '0.4', 0);
        });

        card.addEventListener('dragend', function() {
            this.classList.remove('dragging');
            this.style.opacity = '1';
            draggedCard = null;
            document.querySelectorAll('.task-column').forEach(col => {
                col.classList.remove('drag-over');
                const indicator = col.querySelector('.drop-indicator');
                if (indicator) indicator.remove();
            });
            document.querySelectorAll('.column-card').forEach(cc => cc.classList.remove('drag-over'));
        });
    }

    document.querySelectorAll('.task-card').forEach(setupDragEvents);

    document.querySelectorAll('.task-column').forEach(column => {
        column.addEventListener('dragover', function(e) {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            this.classList.add('drag-over');
            this.closest('.column-card')?.classList.add('drag-over');

            if (!dropIndicator) {
                dropIndicator = createDropIndicator();
            }

            const insertBefore = findInsertPosition(this, e.clientY);
            if (insertBefore) {
                this.insertBefore(dropIndicator, insertBefore);
            } else {
                this.appendChild(dropIndicator);
            }
        });

        column.addEventListener('dragleave', function(e) {
            if (!this.contains(e.relatedTarget)) {
                this.classList.remove('drag-over');
                this.closest('.column-card')?.classList.remove('drag-over');
                if (dropIndicator && dropIndicator.parentNode === this) {
                    dropIndicator.remove();
                }
            }
        });

        column.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('drag-over');
            this.closest('.column-card')?.classList.remove('drag-over');

            if (!draggedCard) return;

            const taskId = draggedCard.dataset.taskId;
            const newStatus = this.dataset.status;
            const oldStatus = draggedCard.dataset.status;

            if (dropIndicator && dropIndicator.parentNode === this) {
                dropIndicator.remove();
                dropIndicator = null;
            }

            const insertBefore = findInsertPosition(this, e.clientY);
            if (insertBefore) {
                this.insertBefore(draggedCard, insertBefore);
            } else {
                this.appendChild(draggedCard);
            }

            const emptyMsg = this.querySelector('.empty-msg');
            if (emptyMsg) emptyMsg.remove();

            draggedCard.classList.remove('dragging');
            draggedCard.dataset.status = newStatus;
            draggedCard.style.opacity = '1';

            updateCounts();

            if (newStatus === oldStatus) return;

            fetch(`/task/${taskId}/status/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body: `status=${newStatus}`
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showToast(`Tarea movida a "${getStatusName(newStatus)}"`);
                } else {
                    showToast('Error al actualizar la tarea', 'error');
                    setTimeout(() => { htmx.trigger('#board', 'boardRefresh'); }, 300);
                }
            })
            .catch(() => {
                showToast('Error de conexion', 'error');
                    setTimeout(() => { htmx.trigger('#board', 'boardRefresh'); }, 300);
            });

            draggedCard = null;
        });
    });

    function setupTouchEvents(card) {
        let touchClone = null;
        let currentColumn = null;

        card.addEventListener('touchstart', function(e) {
            if (this.querySelector('a, button, form')) {
                const target = e.target;
                if (target.closest('a, button, form')) return;
            }
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
            draggedCard = this;
        }, { passive: true });

        card.addEventListener('touchmove', function(e) {
            if (!draggedCard) return;
            const dx = Math.abs(e.touches[0].clientX - touchStartX);
            const dy = Math.abs(e.touches[0].clientY - touchStartY);
            if (!isDragging && (dx > 10 || dy > 10)) {
                isDragging = true;
                draggedCard.classList.add('dragging');
                document.body.style.userSelect = 'none';
            }
            if (!isDragging) return;
            e.preventDefault();

            const touch = e.touches[0];
            const elementBelow = document.elementFromPoint(touch.clientX, touch.clientY);
            const column = elementBelow?.closest('.task-column');

            if (column !== currentColumn) {
                if (currentColumn) {
                    currentColumn.classList.remove('drag-over');
                    currentColumn.closest('.column-card')?.classList.remove('drag-over');
                    const indicator = currentColumn.querySelector('.drop-indicator');
                    if (indicator) indicator.remove();
                }
                currentColumn = column;
                if (column) {
                    column.classList.add('drag-over');
                    column.closest('.column-card')?.classList.add('drag-over');
                    if (!dropIndicator) {
                        dropIndicator = createDropIndicator();
                    }
                    const insertBefore = findInsertPosition(column, touch.clientY);
                    if (insertBefore) {
                        column.insertBefore(dropIndicator, insertBefore);
                    } else {
                        column.appendChild(dropIndicator);
                    }
                }
            }
        }, { passive: false });

        card.addEventListener('touchend', function(e) {
            if (!isDragging) {
                draggedCard = null;
                return;
            }
            isDragging = false;
            document.body.style.userSelect = '';

            if (currentColumn && draggedCard) {
                const taskId = draggedCard.dataset.taskId;
                const newStatus = currentColumn.dataset.status;
                const oldStatus = draggedCard.dataset.status;

                if (dropIndicator && dropIndicator.parentNode === currentColumn) {
                    dropIndicator.remove();
                    dropIndicator = null;
                }

                const insertBefore = findInsertPosition(currentColumn, e.changedTouches[0].clientY);
                if (insertBefore) {
                    currentColumn.insertBefore(draggedCard, insertBefore);
                } else {
                    currentColumn.appendChild(draggedCard);
                }

                currentColumn.classList.remove('drag-over');
                currentColumn.closest('.column-card')?.classList.remove('drag-over');

                const emptyMsg = currentColumn.querySelector('.empty-msg');
                if (emptyMsg) emptyMsg.remove();

                draggedCard.classList.remove('dragging');
                draggedCard.dataset.status = newStatus;

                updateCounts();

                if (newStatus !== oldStatus) {
                    var boardEl = document.getElementById('board');
                    if (boardEl) boardEl.classList.add('board-loading');

                    fetch('/task/' + taskId + '/status/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'X-CSRFToken': csrfToken
                        },
                        body: 'status=' + newStatus
                    })
                    .then(function(r) { return r.json(); })
                    .then(function(data) {
                        if (boardEl) boardEl.classList.remove('board-loading');
                        if (data.success) {
                            showToast('Tarea movida a "' + getStatusName(newStatus) + '"');
                        } else {
                            showToast('Error al actualizar', 'error');
                            setTimeout(function() { htmx.trigger('#board', 'boardRefresh'); }, 300);
                        }
                    })
                    .catch(function() {
                        if (boardEl) boardEl.classList.remove('board-loading');
                        showToast('Error de conexion', 'error');
                        setTimeout(function() { location.reload(); }, 1000);
                    });
                }
            }

            draggedCard = null;
            currentColumn = null;
        });
    }

    document.querySelectorAll('.task-card').forEach(setupTouchEvents);

    function getStatusName(status) {
        const names = {
            'backlog': 'Backlog',
            'todo': 'Por Hacer',
            'in-progress': 'En Progreso',
            'done': 'Completado'
        };
        return names[status] || status;
    }

    function updateCounts() {
        document.querySelectorAll('.task-column').forEach(col => {
            const status = col.dataset.status;
            const count = col.querySelectorAll('.task-card').length;
            const badge = document.querySelector(`.task-count[data-status="${status}"]`);
            if (badge) badge.textContent = count;
            if (count === 0 && !col.querySelector('.empty-msg')) {
                col.innerHTML += '<div class="text-center text-muted py-3 small empty-msg">Sin tareas</div>';
            }
        });
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
                    setTimeout(function() { htmx.trigger('#board', 'boardRefresh'); }, 300);
                } else {
                    showToast(data.error || 'Error al crear tarea', 'error');
                }
            })
            .catch(function() {
                showToast('Error de conexion', 'error');
            })
            .finally(function() {
                btn.disabled = false;
                btn.innerHTML = 'Crear Tarea';
            });
        });
    }

    /* ─── Inline Editing ─── */
    document.querySelectorAll('.task-card').forEach(function(card) {
        /* Title inline edit */
        var titleEl = card.querySelector('.task-title');
        if (titleEl) {
            titleEl.addEventListener('dblclick', function() {
                var taskId = card.dataset.taskId;
                var current = this.textContent.trim();
                var input = document.createElement('input');
                input.type = 'text';
                input.className = 'form-control form-control-sm';
                input.value = current;
                this.replaceWith(input);
                input.focus();
                input.select();

                function save() {
                    var val = input.value.trim();
                    if (val && val !== current) {
                        fetch('/task/' + taskId + '/field/', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': csrfToken
                            },
                            body: JSON.stringify({field: 'title', value: val})
                        })
                        .then(function(r) { return r.json(); })
                        .then(function(d) {
                            if (!d.success) showToast(d.error, 'error');
                        });
                    }
                    var p = document.createElement('p');
                    p.className = 'fw-medium small mb-1 task-title';
                    p.textContent = val || current;
                    input.replaceWith(p);
                }

                input.addEventListener('blur', save);
                input.addEventListener('keydown', function(ev) {
                    if (ev.key === 'Enter') { ev.preventDefault(); save(); }
                    if (ev.key === 'Escape') { ev.preventDefault(); input.value = current; save(); }
                });
            });
        }

        /* Priority inline edit */
        var prioBadge = card.querySelector('.priority-badge');
        if (prioBadge) {
            prioBadge.addEventListener('dblclick', function(e) {
                e.stopPropagation();
                var taskId = card.dataset.taskId;
                var select = document.createElement('select');
                select.className = 'form-select form-select-sm';
                select.innerHTML = '<option value="high">Alta</option><option value="medium">Media</option><option value="low">Baja</option>';
                select.value = card.dataset.priority || 'medium';
                this.replaceWith(select);
                select.focus();

                function save() {
                    var val = select.value;
                    fetch('/task/' + taskId + '/field/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken
                        },
                        body: JSON.stringify({field: 'priority', value: val})
                    })
                    .then(function(r) { return r.json(); })
                    .then(function(d) {
                        if (d.success) { htmx.trigger('#board', 'boardRefresh'); }
                        else showToast(d.error, 'error');
                    });
                }

                select.addEventListener('change', save);
                select.addEventListener('blur', save);
                select.addEventListener('keydown', function(ev) {
                    if (ev.key === 'Escape') { ev.preventDefault(); htmx.trigger('#board', 'boardRefresh'); }
                });
            });
        }

        /* Assignee inline edit */
        var assigneeEl = card.querySelector('.assignee-badge');
        if (assigneeEl) {
            assigneeEl.addEventListener('dblclick', function(e) {
                e.stopPropagation();
                var taskId = card.dataset.taskId;
                var select = document.createElement('select');
                select.className = 'form-select form-select-sm';
                select.innerHTML = '<option value="">Sin asignar</option>';
                var users = card.querySelectorAll('[data-user-option]');
                if (window.assigneeOptions) {
                    window.assigneeOptions.forEach(function(u) {
                        var opt = document.createElement('option');
                        opt.value = u.id;
                        opt.textContent = u.name;
                        select.appendChild(opt);
                    });
                }
                select.style.width = '120px';
                this.replaceWith(select);
                select.focus();

                function save() {
                    var val = select.value;
                    fetch('/task/' + taskId + '/field/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken
                        },
                        body: JSON.stringify({field: 'assignee', value: val})
                    })
                    .then(function(r) { return r.json(); })
                    .then(function(d) {
                        if (d.success) { htmx.trigger('#board', 'boardRefresh'); }
                        else showToast(d.error, 'error');
                    });
                }

                select.addEventListener('change', save);
                select.addEventListener('blur', save);
            });
        }
    });

    /* ─── Keyboard Shortcuts ─── */
    document.addEventListener('keydown', function(e) {
        var tag = e.target.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

        if (e.key === 'c' || e.key === 'C') {
            e.preventDefault();
            openQuickModal();
        }
    });

    function applyFilters() {
        const params = new URLSearchParams();
        const area = document.getElementById('areaFilter')?.value;
        const project = document.getElementById('projectFilter')?.value;
        const assignee = document.getElementById('assigneeFilter')?.value;

        if (area) params.set('area', area);
        if (project) params.set('project', project);
        if (assignee) params.set('assignee', assignee);

        const qs = params.toString();
        const board = document.getElementById('board');
        const url = '/ver_tablero/fragment/' + (qs ? '?' + qs : '');
        htmx.ajax('GET', url, {target: '#board', swap: 'innerHTML'});
    }

    var _projectOptions = null;
    var _assigneeOptions = null;

    function initCascadeState() {
        var areaSelect = document.getElementById('areaFilter');
        var projectSelect = document.getElementById('projectFilter');
        var assigneeSelect = document.getElementById('assigneeFilter');
        if (!areaSelect || !projectSelect || !assigneeSelect) return;

        _projectOptions = Array.from(projectSelect.querySelectorAll('option'));
        _assigneeOptions = Array.from(assigneeSelect.querySelectorAll('option'));

        // Initial disabled state: enable downstream selects if they have a value from filters
        projectSelect.disabled = !areaSelect.value;
        assigneeSelect.disabled = !projectSelect.value;
    }

    function updateProjectOptions() {
        var areaSelect = document.getElementById('areaFilter');
        var projectSelect = document.getElementById('projectFilter');
        if (!areaSelect || !projectSelect) return;

        var selectedArea = areaSelect.value;
        var currentProject = projectSelect.value;

        projectSelect.innerHTML = '';

        var options = _projectOptions || Array.from(projectSelect.querySelectorAll('option'));
        var filtered = options.filter(function(opt) {
            if (opt.value === '') return true;
            if (!selectedArea) return true;
            return opt.dataset.area === selectedArea;
        });

        filtered.forEach(function(opt) { projectSelect.appendChild(opt); });

        if (currentProject && projectSelect.querySelector('option[value="' + currentProject + '"]')) {
            projectSelect.value = currentProject;
        }

        projectSelect.disabled = !selectedArea && !projectSelect.querySelector('option[value]:not([value=""])');
    }

    function updateAssigneeOptions() {
        var projectSelect = document.getElementById('projectFilter');
        var assigneeSelect = document.getElementById('assigneeFilter');
        if (!projectSelect || !assigneeSelect) return;

        var selectedProject = projectSelect.value;
        var currentAssignee = assigneeSelect.value;

        assigneeSelect.innerHTML = '';

        var options = _assigneeOptions || Array.from(assigneeSelect.querySelectorAll('option'));
        var filtered = options.filter(function(opt) {
            if (opt.value === '') return true;
            if (!selectedProject) return true;
            var projects = (opt.dataset.projects || '').split(',').filter(Boolean);
            return projects.indexOf(selectedProject) !== -1;
        });

        filtered.forEach(function(opt) { assigneeSelect.appendChild(opt); });

        if (currentAssignee && assigneeSelect.querySelector('option[value="' + currentAssignee + '"]')) {
            assigneeSelect.value = currentAssignee;
        }

        assigneeSelect.disabled = !selectedProject;
    }

    document.addEventListener('DOMContentLoaded', initCascadeState);

    document.getElementById('areaFilter')?.addEventListener('change', function() {
        updateProjectOptions();
        var assigneeSelect = document.getElementById('assigneeFilter');
        if (assigneeSelect) assigneeSelect.disabled = true;
        applyFilters();
    });
    document.getElementById('projectFilter')?.addEventListener('change', function() {
        updateAssigneeOptions();
        applyFilters();
    });
    document.getElementById('assigneeFilter')?.addEventListener('change', applyFilters);

    document.querySelectorAll('.task-card').forEach(function(card) {
        card.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const editLink = this.querySelector('a[aria-label^="Editar"]');
                if (editLink) editLink.click();
            }
        });
    });
});
