/* backlog.js — Jira-style Backlog: accordion blocks, drag&drop between
   sprints/backlog, inline status, assignee picker, quick create. */
(function () {
    var root = document.getElementById('jiraBacklog');
    if (!root) return;

    var canManage = root.dataset.canManage === '1';
    var projectId = root.dataset.project || '';
    var isGeneral = root.dataset.general === '1';
    var U = window.blUrls || {};

    function csrf() {
        var m = document.querySelector('meta[name="csrf-token"]');
        return m ? m.getAttribute('content') : '';
    }
    function toast(msg, type) { if (typeof showToast === 'function') showToast(msg, type || 'success'); }

    /* ── Collapse / expand blocks ── */
    root.querySelectorAll('.bl-collapse').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var block = btn.closest('.bl-block');
            var open = block.classList.toggle('collapsed');
            btn.setAttribute('aria-expanded', open ? 'false' : 'true');
        });
    });

    /* ── Status counters recompute ── */
    function recount(block) {
        if (!block) return;
        var rows = block.querySelectorAll('.bl-row');
        var c = { TODO: 0, PROG: 0, DONE: 0 };
        rows.forEach(function (r) {
            var s = r.dataset.status;
            if (s === 'DONE') c.DONE++;
            else if (s === 'PROG' || s === 'TEST') c.PROG++;
            else c.TODO++;
        });
        var head = block.querySelector('.bl-counts');
        if (head) {
            head.querySelector('.bl-c-todo').textContent = c.TODO;
            head.querySelector('.bl-c-prog').textContent = c.PROG;
            head.querySelector('.bl-c-done').textContent = c.DONE;
        }
        // enable/disable start button by total
        var total = rows.length;
        var startBtn = block.querySelector('.bl-start-sprint');
        if (startBtn) startBtn.disabled = total === 0;
        // remove empty placeholders if rows exist
        var list = block.querySelector('.bl-tasklist');
        var empty = list && list.querySelector('.bl-empty');
        if (empty && rows.length) empty.remove();
    }

    /* ── Drag & drop between blocks ── */
    var dragged = null;

    function bindRow(row) {
        row.addEventListener('dragstart', function (e) {
            dragged = row;
            row.classList.add('dragging');
            e.dataTransfer.effectAllowed = 'move';
            try { e.dataTransfer.setData('text/plain', row.dataset.taskId); } catch (_) {}
        });
        row.addEventListener('dragend', function () {
            row.classList.remove('dragging');
            root.querySelectorAll('.bl-tasklist.drop-hover').forEach(function (l) { l.classList.remove('drop-hover'); });
            dragged = null;
        });
    }

    if (canManage && !isGeneral) {
        root.querySelectorAll('.bl-row').forEach(bindRow);

        root.querySelectorAll('.bl-tasklist').forEach(function (list) {
            list.addEventListener('dragover', function (e) {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
                list.classList.add('drop-hover');
                var after = getAfterElement(list, e.clientY);
                if (dragged) {
                    if (after == null) list.appendChild(dragged);
                    else list.insertBefore(dragged, after);
                }
            });
            list.addEventListener('dragleave', function (e) {
                if (!list.contains(e.relatedTarget)) list.classList.remove('drop-hover');
            });
            list.addEventListener('drop', function (e) {
                e.preventDefault();
                list.classList.remove('drop-hover');
                if (!dragged) return;
                var taskId = dragged.dataset.taskId;
                var targetSprint = list.dataset.sprintId || null;
                var srcBlock = dragged.closest('.bl-block');
                var dstBlock = list.closest('.bl-block');

                fetch(U.assignSprint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
                    body: JSON.stringify({ task_id: taskId, sprint_id: targetSprint })
                })
                .then(function (r) { return r.json(); })
                .then(function (d) {
                    if (d.success) {
                        recount(srcBlock);
                        recount(dstBlock);
                        toast(d.message || 'Tarea movida');
                    } else {
                        toast(d.error || 'Error', 'error');
                        setTimeout(function () { location.reload(); }, 600);
                    }
                })
                .catch(function () { toast('Error de conexion', 'error'); });
            });
        });
    }

    function getAfterElement(list, y) {
        var els = Array.prototype.slice.call(list.querySelectorAll('.bl-row:not(.dragging)'));
        return els.reduce(function (closest, child) {
            var box = child.getBoundingClientRect();
            var offset = y - box.top - box.height / 2;
            if (offset < 0 && offset > closest.offset) return { offset: offset, element: child };
            return closest;
        }, { offset: -Infinity, element: null }).element;
    }

    /* ── Inline status change ── */
    root.querySelectorAll('.bl-status').forEach(function (sel) {
        sel.addEventListener('change', function () {
            var id = sel.dataset.taskId;
            var val = sel.value;
            fetch(U.statusBase + id + '/status/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
                body: JSON.stringify({ status: val })
            })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (d.success) {
                    sel.className = 'bl-status bl-status-' + val;
                    var row = sel.closest('.bl-row');
                    row.dataset.status = val;
                    recount(row.closest('.bl-block'));
                    toast('Estado actualizado');
                } else { toast(d.error || 'Error', 'error'); }
            })
            .catch(function () { toast('Error de conexion', 'error'); });
        });
    });

    /* ── Assignee quick picker ── */
    var openPicker = null;
    function closePicker() { if (openPicker) { openPicker.remove(); openPicker = null; } }
    document.addEventListener('click', function (e) {
        if (openPicker && !e.target.closest('.bl-assignee-picker') && !e.target.closest('.bl-assignee')) closePicker();
    });

    if (canManage) {
        root.querySelectorAll('.bl-assignee').forEach(function (holder) {
            holder.addEventListener('click', function (e) {
                e.stopPropagation();
                if (openPicker) { closePicker(); return; }
                var taskId = holder.dataset.taskId;
                var pick = document.createElement('div');
                pick.className = 'bl-assignee-picker';
                var html = '<input type="text" class="bl-picker-search" placeholder="Buscar...">';
                html += '<div class="bl-picker-list">';
                (window.blAssignees || []).forEach(function (a) {
                    html += '<div class="bl-picker-item" data-value="' + a.value + '">' +
                        '<span class="bl-avatar" style="background:' + a.color + '">' + (a.initials || '?') + '</span>' +
                        '<span>' + a.label + '</span></div>';
                });
                html += '</div>';
                pick.innerHTML = html;
                document.body.appendChild(pick);
                var r = holder.getBoundingClientRect();
                pick.style.position = 'fixed';
                pick.style.top = (r.bottom + 4) + 'px';
                pick.style.left = Math.max(8, r.right - 220) + 'px';
                openPicker = pick;

                var search = pick.querySelector('.bl-picker-search');
                search.focus();
                search.addEventListener('input', function () {
                    var q = this.value.toLowerCase();
                    pick.querySelectorAll('.bl-picker-item').forEach(function (it) {
                        it.style.display = it.textContent.toLowerCase().indexOf(q) > -1 ? '' : 'none';
                    });
                });

                pick.querySelectorAll('.bl-picker-item').forEach(function (it) {
                    it.addEventListener('click', function () {
                        var val = it.dataset.value;
                        fetch(U.fieldBase + taskId + '/field/', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf() },
                            body: JSON.stringify({ field: 'assignee', value: val })
                        })
                        .then(function (r) { return r.json(); })
                        .then(function (d) {
                            if (d.success) {
                                var a = (window.blAssignees || []).find(function (x) { return String(x.value) === String(val); });
                                if (a && a.value) {
                                    holder.innerHTML = '<span class="bl-avatar" style="background:' + a.color + '" title="' + a.label + '">' + a.initials + '</span>';
                                } else {
                                    holder.innerHTML = '<span class="bl-avatar bl-avatar-empty" title="Sin asignar"><i class="fas fa-user"></i></span>';
                                }
                                toast('Responsable actualizado');
                            } else { toast(d.error || 'Error', 'error'); }
                            closePicker();
                        })
                        .catch(function () { toast('Error de conexion', 'error'); closePicker(); });
                    });
                });
            });
        });
    }

    /* ── Quick create inline per block (Jira-style rich form) ── */
    var ISSUE_TYPES = [
        { value: 'task', label: 'Task', icon: 'fa-square-check', color: '#3b82f6' },
        { value: 'story', label: 'Story', icon: 'fa-bookmark', color: '#22c55e' },
        { value: 'bug', label: 'Bug', icon: 'fa-bug', color: '#ef4444' }
    ];

    function buildInlineForm(sprintId) {
        var form = document.createElement('div');
        form.className = 'bl-create-form';
        form.dataset.type = 'task';
        form.dataset.assignee = '';
        form.dataset.due = '';

        var typeOpts = ISSUE_TYPES.map(function (t) {
            return '<div class="bl-cf-type-opt" data-value="' + t.value + '"><i class="fas ' + t.icon + '" style="color:' + t.color + '"></i> ' + t.label + '</div>';
        }).join('');

        form.innerHTML =
            '<div class="bl-cf-type" tabindex="0" title="Tipo de incidencia">' +
                '<i class="fas fa-square-check bl-cf-type-icon" style="color:#3b82f6"></i>' +
                '<i class="fas fa-caret-down bl-cf-caret"></i>' +
                '<div class="bl-cf-type-menu">' + typeOpts + '</div>' +
            '</div>' +
            '<input type="text" class="bl-cf-input" placeholder="Describe what needs to be done, or generate work items from Confluence, Loom, or an image.">' +
            '<div class="bl-cf-due" title="Fecha de vencimiento (obligatoria)">' +
                '<i class="far fa-calendar"></i>' +
                '<input type="date" class="bl-cf-date">' +
            '</div>' +
            '<div class="bl-cf-assignee" tabindex="0" title="Asignar responsable (obligatorio)">' +
                '<span class="bl-avatar bl-avatar-empty bl-cf-avatar"><i class="fas fa-user"></i></span>' +
                '<div class="bl-cf-assignee-menu">' +
                    '<input type="text" class="bl-cf-assignee-search" placeholder="Buscar...">' +
                    '<div class="bl-cf-assignee-list"></div>' +
                '</div>' +
            '</div>' +
            '<button type="button" class="bl-cf-submit">Create <span class="bl-cf-enter">↵</span></button>' +
            '<button type="button" class="bl-cf-cancel" title="Cancelar"><i class="fas fa-times"></i></button>';
        return form;
    }

    function wireInlineForm(form, sprintId, block, addBtn) {
        var input = form.querySelector('.bl-cf-input');
        var submit = form.querySelector('.bl-cf-submit');
        var dateInput = form.querySelector('.bl-cf-date');
        var dueWrap = form.querySelector('.bl-cf-due');
        var assigneeWrap = form.querySelector('.bl-cf-assignee');
        var avatar = form.querySelector('.bl-cf-avatar');

        function closeForm() {
            form.remove();
            if (addBtn) addBtn.style.display = '';
        }

        function floatMenu(menu, anchor, alignRight) {
            var r = anchor.getBoundingClientRect();
            menu.style.position = 'fixed';
            menu.style.top = (r.bottom + 4) + 'px';
            if (alignRight) {
                menu.style.left = 'auto';
                menu.style.right = (window.innerWidth - r.right) + 'px';
            } else {
                menu.style.left = r.left + 'px';
                menu.style.right = 'auto';
            }
        }

        // Type dropdown
        var typeWrap = form.querySelector('.bl-cf-type');
        var typeIcon = form.querySelector('.bl-cf-type-icon');
        var typeMenu = form.querySelector('.bl-cf-type-menu');
        typeWrap.addEventListener('click', function (e) {
            e.stopPropagation();
            var opening = !typeWrap.classList.contains('open');
            assigneeWrap.classList.remove('open');
            typeWrap.classList.toggle('open');
            if (opening) floatMenu(typeMenu, typeWrap, false);
        });
        form.querySelectorAll('.bl-cf-type-opt').forEach(function (opt) {
            opt.addEventListener('click', function (e) {
                e.stopPropagation();
                var t = ISSUE_TYPES.find(function (x) { return x.value === opt.dataset.value; });
                form.dataset.type = t.value;
                typeIcon.className = 'fas ' + t.icon + ' bl-cf-type-icon';
                typeIcon.style.color = t.color;
                typeWrap.classList.remove('open');
            });
        });

        // Assignee dropdown
        var assigneeMenu = form.querySelector('.bl-cf-assignee-menu');
        var list = form.querySelector('.bl-cf-assignee-list');
        (window.blAssignees || []).forEach(function (a) {
            var it = document.createElement('div');
            it.className = 'bl-cf-assignee-opt';
            it.dataset.value = a.value;
            it.innerHTML = '<span class="bl-avatar" style="background:' + a.color + '">' + (a.initials || '?') + '</span><span>' + a.label + '</span>';
            list.appendChild(it);
        });
        assigneeWrap.addEventListener('click', function (e) {
            e.stopPropagation();
            var opening = !assigneeWrap.classList.contains('open');
            typeWrap.classList.remove('open');
            assigneeWrap.classList.toggle('open');
            if (opening) {
                floatMenu(assigneeMenu, assigneeWrap, true);
                var s = form.querySelector('.bl-cf-assignee-search');
                if (s) s.focus();
            }
        });
        var aSearch = form.querySelector('.bl-cf-assignee-search');
        aSearch.addEventListener('click', function (e) { e.stopPropagation(); });
        aSearch.addEventListener('input', function () {
            var q = this.value.toLowerCase();
            list.querySelectorAll('.bl-cf-assignee-opt').forEach(function (it) {
                it.style.display = it.textContent.toLowerCase().indexOf(q) > -1 ? '' : 'none';
            });
        });
        list.querySelectorAll('.bl-cf-assignee-opt').forEach(function (it) {
            it.addEventListener('click', function (e) {
                e.stopPropagation();
                var val = it.dataset.value;
                form.dataset.assignee = val;
                var a = (window.blAssignees || []).find(function (x) { return String(x.value) === String(val); });
                if (a && a.value) {
                    avatar.className = 'bl-avatar bl-cf-avatar';
                    avatar.style.background = a.color;
                    avatar.textContent = a.initials;
                } else {
                    avatar.className = 'bl-avatar bl-avatar-empty bl-cf-avatar';
                    avatar.style.background = '';
                    avatar.innerHTML = '<i class="fas fa-user"></i>';
                }
                assigneeWrap.classList.remove('open');
                validate();
            });
        });

        // Due date
        dateInput.addEventListener('change', function () {
            form.dataset.due = dateInput.value;
            dueWrap.classList.toggle('has-value', !!dateInput.value);
            validate();
        });
        dueWrap.addEventListener('click', function () {
            if (dateInput.showPicker) { try { dateInput.showPicker(); } catch (_) {} }
            else dateInput.focus();
        });

        function validate() {
            var ok = input.value.trim() && form.dataset.assignee && form.dataset.due;
            submit.classList.toggle('bl-cf-ready', !!ok);
            assigneeWrap.classList.toggle('bl-required', !form.dataset.assignee);
            dueWrap.classList.toggle('bl-required', !form.dataset.due);
            return ok;
        }
        input.addEventListener('input', validate);

        function doCreate() {
            if (!input.value.trim()) { input.classList.add('bl-cf-input-err'); input.focus(); return; }
            input.classList.remove('bl-cf-input-err');
            if (!form.dataset.assignee || !form.dataset.due) {
                validate();
                if (typeof showToast === 'function') showToast('Responsable y fecha son obligatorios', 'error');
                return;
            }
            submit.disabled = true;
            var body = new URLSearchParams();
            body.set('title', input.value.trim());
            body.set('project', form.dataset.project || projectId);
            body.set('type', form.dataset.type);
            body.set('priority', 'medium');
            body.set('points', '1');
            body.set('status', 'TODO');
            body.set('assignee', form.dataset.assignee);
            body.set('due_date', form.dataset.due);
            body.set('require_meta', '1');
            if (sprintId) body.set('sprint', sprintId);
            fetch(U.quickCreate, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' },
                body: body.toString()
            })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (d.success) { toast('Tarea creada'); location.reload(); }
                else { toast(d.error || 'Error al crear', 'error'); submit.disabled = false; }
            })
            .catch(function () { toast('Error de conexion', 'error'); submit.disabled = false; });
        }
        submit.addEventListener('click', doCreate);
        input.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') { e.preventDefault(); doCreate(); }
            else if (e.key === 'Escape') closeForm();
        });
        form.querySelector('.bl-cf-cancel').addEventListener('click', closeForm);

        // Close dropdowns on outside click
        document.addEventListener('click', function onDoc(e) {
            if (!document.body.contains(form)) { document.removeEventListener('click', onDoc); return; }
            if (!form.contains(e.target)) {
                typeWrap.classList.remove('open');
                assigneeWrap.classList.remove('open');
            }
        });

        validate();
        setTimeout(function () { input.focus(); }, 20);
    }

    root.querySelectorAll('.bl-quick-add').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var sprintId = btn.dataset.sprintId || '';
            var block = btn.closest('.bl-block');
            if (block.querySelector('.bl-create-form')) {
                block.querySelector('.bl-cf-input').focus();
                return;
            }
            var form = buildInlineForm(sprintId);
            form.dataset.project = btn.dataset.projectId || projectId;
            btn.parentNode.insertBefore(form, btn);
            btn.style.display = 'none';
            wireInlineForm(form, sprintId, block, btn);
        });
    });

    /* ── Block 3-dot menus (edit/delete sprint, create sprint) ── */
    var openBlMenu = null;
    function closeBlMenu() {
        if (openBlMenu) { openBlMenu.classList.remove('open'); openBlMenu = null; }
    }
    document.addEventListener('click', function (e) {
        if (openBlMenu && !e.target.closest('.bl-menu') && !e.target.closest('.bl-menu-btn')) closeBlMenu();
    });
    root.querySelectorAll('.bl-menu-btn').forEach(function (btn) {
        var menu = btn.parentNode.querySelector('.bl-menu');
        if (!menu) return;
        btn.addEventListener('click', function (e) {
            e.stopPropagation();
            var isOpen = menu.classList.contains('open');
            closeBlMenu();
            if (isOpen) return;
            var r = btn.getBoundingClientRect();
            menu.style.top = (r.bottom + 4) + 'px';
            menu.style.left = 'auto';
            menu.style.right = (window.innerWidth - r.right) + 'px';
            menu.classList.add('open');
            openBlMenu = menu;
        });
    });
    root.querySelectorAll('.bl-menu-item').forEach(function (item) {
        item.addEventListener('click', function (e) {
            e.stopPropagation();
            var action = item.dataset.action;
            closeBlMenu();
            if (action === 'edit-sprint') {
                window.editarSprintInline(item.dataset.sprintId);
            } else if (action === 'delete-sprint') {
                var name = item.dataset.sprintName || 'este sprint';
                var doDelete = function () {
                    fetch('/sprint/' + item.dataset.sprintId + '/delete/', {
                        method: 'POST',
                        headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' }
                    })
                    .then(function (r) { return r.json(); })
                    .then(function (d) {
                        if (d.success) { toast(d.message || 'Sprint eliminado'); location.reload(); }
                        else { toast(d.error || 'Error', 'error'); }
                    })
                    .catch(function () { toast('Error de conexion', 'error'); });
                };
                if (typeof showConfirm === 'function') {
                    showConfirm('Eliminar sprint', 'Eliminar "' + name + '"? Sus tareas volveran al backlog.', doDelete);
                } else if (confirm('Eliminar "' + name + '"? Sus tareas volveran al backlog.')) {
                    doDelete();
                }
            } else if (action === 'create-sprint') {
                var cb = document.getElementById('blCreateSprintBtn');
                if (cb) cb.click();
            } else if (action === 'new-task-backlog') {
                var qa = root.querySelector('.bl-block[data-block="backlog"] .bl-quick-add');
                if (qa) qa.click();
            } else if (action === 'edit-task') {
                window.openTaskDrawer(item.dataset.taskId);
            } else if (action === 'delete-task') {
                var title = item.dataset.taskTitle || 'esta tarea';
                var taskId = item.dataset.taskId;
                var doDel = function () {
                    fetch('/task/' + taskId + '/delete/', {
                        method: 'POST',
                        headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' }
                    })
                    .then(function (r) { return r.json(); })
                    .then(function (d) {
                        if (d.success) {
                            var row = root.querySelector('.bl-row[data-task-id="' + taskId + '"]');
                            var blk = row ? row.closest('.bl-block') : null;
                            if (row) row.remove();
                            if (blk) recount(blk);
                            toast(d.message || 'Tarea eliminada');
                        } else { toast(d.error || 'Error', 'error'); }
                    })
                    .catch(function () { toast('Error de conexion', 'error'); });
                };
                if (typeof showConfirm === 'function') {
                    showConfirm('Eliminar tarea', 'Eliminar "' + title + '"?', doDel);
                } else if (confirm('Eliminar "' + title + '"?')) {
                    doDel();
                }
            }
        });
    });

    /* ── Row 3-dot menus (edit/delete task) ── */
    function bindRowMenu(scope) {
        (scope || root).querySelectorAll('.bl-row-menu-btn').forEach(function (btn) {
            if (btn.dataset.bound) return;
            btn.dataset.bound = '1';
            var menu = btn.parentNode.querySelector('.bl-row-menu');
            if (!menu) return;
            btn.addEventListener('click', function (e) {
                e.stopPropagation();
                var isOpen = menu.classList.contains('open');
                closeBlMenu();
                if (isOpen) return;
                var r = btn.getBoundingClientRect();
                menu.style.top = (r.bottom + 4) + 'px';
                menu.style.left = 'auto';
                menu.style.right = (window.innerWidth - r.right) + 'px';
                menu.classList.add('open');
                openBlMenu = menu;
            });
            menu.querySelectorAll('.bl-menu-item').forEach(function (item) {
                item.addEventListener('click', function (e) {
                    e.stopPropagation();
                    var action = item.dataset.action;
                    closeBlMenu();
                    if (action === 'edit-task') {
                        window.openTaskDrawer(item.dataset.taskId);
                    } else if (action === 'delete-task') {
                        var title = item.dataset.taskTitle || 'esta tarea';
                        var taskId = item.dataset.taskId;
                        var doDel = function () {
                            fetch('/task/' + taskId + '/delete/', {
                                method: 'POST',
                                headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' }
                            })
                            .then(function (r) { return r.json(); })
                            .then(function (d) {
                                if (d.success) {
                                    var row = root.querySelector('.bl-row[data-task-id="' + taskId + '"]');
                                    var blk = row ? row.closest('.bl-block') : null;
                                    if (row) row.remove();
                                    if (blk) recount(blk);
                                    toast(d.message || 'Tarea eliminada');
                                } else { toast(d.error || 'Error', 'error'); }
                            })
                            .catch(function () { toast('Error de conexion', 'error'); });
                        };
                        if (typeof showConfirm === 'function') {
                            showConfirm('Eliminar tarea', 'Eliminar "' + title + '"?', doDel);
                        } else if (confirm('Eliminar "' + title + '"?')) {
                            doDel();
                        }
                    }
                });
            });
        });
    }
    bindRowMenu(root);

    /* ── Start sprint ── */
    root.querySelectorAll('.bl-start-sprint').forEach(function (btn) {
        btn.addEventListener('click', function () {
            if (btn.disabled) return;
            var sprintId = btn.dataset.sprintId;
            var f = document.createElement('form');
            f.method = 'POST';
            f.action = '/sprint/' + sprintId + '/start/';
            f.innerHTML = '<input type="hidden" name="csrfmiddlewaretoken" value="' + csrf() + '">';
            document.body.appendChild(f);
            f.submit();
        });
    });

    /* ── Create sprint modal (AJAX) ── */
    var createBtn = document.getElementById('blCreateSprintBtn');
    var sprintModalEl = document.getElementById('blSprintModal');
    if (createBtn && sprintModalEl) {
        createBtn.addEventListener('click', function () {
            if (window.bootstrap) bootstrap.Modal.getOrCreateInstance(sprintModalEl).show();
        });
        var sprintForm = sprintModalEl.querySelector('form');
        if (sprintForm) {
            sprintForm.addEventListener('submit', function (e) {
                e.preventDefault();
                var btn = sprintForm.querySelector('[type="submit"]');
                btn.disabled = true;
                fetch(sprintForm.action, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' },
                    body: new FormData(sprintForm)
                })
                .then(function (r) { return r.json(); })
                .then(function (d) {
                    if (d.success) {
                        toast(d.message || 'Sprint creado');
                        location.reload();
                    } else {
                        toast(d.error || 'Error al crear sprint', 'error');
                        btn.disabled = false;
                    }
                })
                .catch(function () { toast('Error de conexion', 'error'); btn.disabled = false; });
            });
        }
    }

    /* ── Task edit drawer ── */
    window.openTaskDrawer = function (taskId) {
        if (typeof openCrudDrawer !== 'function') return;
        if (taskId) {
            fetch('/task/' + taskId + '/json/').then(function (r) { return r.json(); }).then(function (data) { openCrudDrawer('task', data); });
        } else { openCrudDrawer('task'); }
    };

    window.editarSprintInline = function (sprintId) {
        window.location.href = '/ver_sprints/?project=' + projectId;
    };

    if (typeof initCrudDrawer === 'function') {
        var drawerFields = [
            { name: 'title', label: 'Titulo', type: 'text', required: true },
            { name: 'assignee', label: 'Asignado a', type: 'select', optionsData: 'taskAssigneeOptions' },
            { name: 'type', label: 'Tipo', type: 'select', options: [
                { value: 'task', label: 'Tarea' }, { value: 'story', label: 'Historia' },
                { value: 'bug', label: 'Bug' }, { value: 'epic', label: 'Epic' } ], default: 'task' },
            { name: 'priority', label: 'Prioridad', type: 'select', options: [
                { value: 'medium', label: 'Media' }, { value: 'high', label: 'Alta' }, { value: 'low', label: 'Baja' } ], default: 'medium' },
            { name: 'points', label: 'Puntos', type: 'select', options: [
                { value: '1', label: '1' }, { value: '2', label: '2' }, { value: '3', label: '3' },
                { value: '5', label: '5' }, { value: '8', label: '8' }, { value: '13', label: '13' } ], default: '1' },
            { name: 'description', label: 'Descripcion', type: 'textarea', rows: 3 }
        ];
        if (!projectId) {
            drawerFields.splice(1, 0, { name: 'project', label: 'Proyecto', type: 'select', optionsData: 'taskProjectOptions', required: true });
        }
        initCrudDrawer({
            entity: 'task', label: 'Tarea',
            fields: drawerFields,
            createUrl: U.quickCreate, editUrl: '/task/'
        });
    }
})();
