/**
 * crud_drawer.js — Drawer CRUD unificado
 * Usa clases de crud_forms.css. Selects custom. Validación en español.
 */
var __crudInstances = {};

function initCrudDrawer(config) {
    __crudInstances[config.entity] = config;
    ensureHost();
    document.addEventListener('keydown', function(e) { if (e.key === 'Escape') closeCrudDrawer(); });
}

function ensureHost() {
    if (document.getElementById('crudDrawerHost')) return;
    var host = document.createElement('div');
    host.id = 'crudDrawerHost';
    host.className = 'crud-drawer-overlay';
    host.style.cssText = 'position:fixed;inset:0;z-index:99999;display:none;justify-content:flex-end;background:rgba(0,0,0,0.4);';
    host.innerHTML = '<div class="crud-drawer-panel" style="width:480px;max-width:92vw;height:100vh;background:var(--surface-1);display:flex;flex-direction:column;overflow:hidden;"></div>';
    document.body.appendChild(host);
    host.addEventListener('click', function(e) { if (e.target === host) closeCrudDrawer(); });
}

function openCrudDrawer(entity, data) {
    var config = __crudInstances[entity];
    if (!config) return;
    var host = document.getElementById('crudDrawerHost');
    var inner = host.querySelector('.crud-drawer-panel');
    var isEdit = data && data.id;

    var fem = config.label.endsWith('a') || config.label.endsWith('d');
    var h = '';
    h += '<div class="crud-drawer-header">';
    h += '  <h6 class="crud-drawer-title">' + (isEdit ? 'Editar ' : (fem ? 'Nueva ' : 'Nuevo ')) + config.label + '</h6>';
    h += '  <button type="button" class="crud-btn-close" onclick="closeCrudDrawer()"><i class="fas fa-times"></i></button>';
    h += '</div>';
    h += '<div class="crud-drawer-body">';
    h += '  <form id="crudDrawerForm" novalidate>';
    h += '    <input type="hidden" name="csrfmiddlewaretoken" value="' + getCsrfToken() + '">';
    h += '    <input type="hidden" name="id" id="crudField_id" value="' + (data ? (data.id || '') : '') + '">';

    config.fields.forEach(function(f) {
        var val = data ? (data[f.name] != null ? data[f.name] : (f.default || '')) : (f.default || '');
        h += '    <div class="crud-field">';
        h += '      <label class="crud-label" for="crudField_' + f.name + '">' + f.label + (f.required ? ' <span class="crud-label-required">*</span>' : '') + '</label>';

        if (f.type === 'textarea') {
            h += '      <textarea name="' + f.name + '" id="crudField_' + f.name + '" class="crud-input crud-textarea" rows="' + (f.rows || 3) + '"' + attr('placeholder', f.placeholder) + (f.required ? ' data-required="true"' : '') + '>' + escapeHtml(val) + '</textarea>';
        } else if (f.type === 'select') {
            var opts = resolveOptions(f, data);
            var placeholder = f.emptyLabel || 'Seleccionar ' + f.label.toLowerCase();
            h += buildSelect(f.name, opts, val, placeholder, f.required);
        } else if (f.type === 'color') {
            h += '      <div class="crud-color-row">';
            h += '        <input type="color" name="' + f.name + '" id="crudField_' + f.name + '" class="crud-input" value="' + escapeHtml(val) + '">';
            h += '        <span class="crud-color-value">' + escapeHtml(val || '#000000') + '</span>';
            h += '      </div>';
        } else if (f.type === 'checkbox_group') {
            var copts = resolveOptions(f, data);
            var vArr = typeof val === 'string' ? val.split(',').filter(Boolean) : (val || []);
            h += '      <div class="crud-checkbox-group">';
            copts.forEach(function(o) {
                var ov = (o.value != null ? o.value : o);
                var ol = (o.label != null ? o.label : o);
                var chk = vArr.indexOf(String(ov)) !== -1 ? ' checked' : '';
                h += '        <label class="crud-checkbox"><input type="checkbox" name="' + f.name + '[]" value="' + escapeHtml(ov) + '"' + chk + '>' + escapeHtml(ol) + '</label>';
            });
            h += '      </div>';
        } else {
            var type = f.type || 'text';
            if (type === 'phone') type = 'tel';
            h += '      <input type="' + type + '" name="' + f.name + '" id="crudField_' + f.name + '" class="crud-input" value="' + escapeHtml(val) + '"' + (f.step ? ' step="' + f.step + '"' : '') + attr('placeholder', f.placeholder) + (f.required ? ' data-required="true"' : '') + '>';
        }
        h += '      <div class="crud-error"></div>';
        h += '    </div>';
    });

    h += '  </form>';
    h += '</div>';
    h += '<div class="crud-drawer-footer">';
    h += '  <button type="button" class="crud-btn-cancel" onclick="closeCrudDrawer()">Cancelar</button>';
    h += '  <button type="button" class="crud-btn-submit" id="crudDrawerSubmit"><i class="fas fa-check"></i>' + (isEdit ? 'Guardar' : 'Crear ' + config.label) + '</button>';
    h += '</div>';

    inner.innerHTML = h;
    host.style.display = 'flex';
    animateIn(inner);

    setTimeout(function() {
        var first = inner.querySelector('.crud-input:not([type=hidden]):not([type=color]), .crud-textarea, .custom-select-trigger');
        if (first) first.focus();
    }, 250);

    // Init custom selects
    inner.querySelectorAll('.custom-select-wrapper').forEach(function(w) { initSelect(w); });

    // Hook for dynamic fields (sprint → project dependency, etc.)
    if (config.onAfterRender) {
        config.onAfterRender(form, data, isEdit);
    }

    // Submit handler
    document.getElementById('crudDrawerSubmit').addEventListener('click', function() { submitForm(config, isEdit); });
}

/* ── Custom Select ──────────────────────────────────────── */

function buildSelect(name, options, selectedValue, placeholder, required) {
    var found = options.find(function(o) {
        var ov = o.value != null ? o.value : o;
        return String(ov) === String(selectedValue);
    });
    var display = found ? (found.label || '') : placeholder;
    var hasSelection = !!found;

    var h = '<div class="custom-select-wrapper">';
    h += '  <input type="hidden" name="' + name + '" id="crudField_' + name + '" class="custom-select-value" value="' + escapeHtml(selectedValue || '') + '"' + (required ? ' data-required="true"' : '') + '>';
    h += '  <button type="button" class="custom-select-trigger" tabindex="0">';
    h += '    <span class="custom-select-display' + (hasSelection ? ' selected' : '') + '">' + escapeHtml(display) + '</span>';
    h += '    <i class="fas fa-chevron-down custom-select-chevron"></i>';
    h += '  </button>';
    h += '  <div class="custom-select-dropdown">';
    if (options.length === 0) {
        h += '    <div class="custom-select-option option-empty">Sin opciones</div>';
    }
    options.forEach(function(o) {
        var ov = o.value != null ? o.value : o;
        var ol = o.label != null ? o.label : o;
        var sel = String(ov) === String(selectedValue);
        h += '    <div class="custom-select-option' + (sel ? ' selected' : '') + '" data-value="' + escapeHtml(ov) + '">';
        h += '      <span>' + escapeHtml(ol) + '</span>';
        if (sel) h += '      <i class="fas fa-check option-check"></i>';
        h += '    </div>';
    });
    h += '  </div>';
    h += '</div>';
    return h;
}

function initSelect(wrapper) {
    var trigger = wrapper.querySelector('.custom-select-trigger');
    var display = wrapper.querySelector('.custom-select-display');
    var input = wrapper.querySelector('.custom-select-value');
    var dropdown = wrapper.querySelector('.custom-select-dropdown');
    var options = dropdown.querySelectorAll('.custom-select-option');
    var fieldErr = wrapper.closest('.crud-field').querySelector('.crud-error');
    wrapper._placeholder = display.textContent;

    function open() {
        closeAll();
        dropdown.style.display = 'block';
        wrapper.classList.add('open');
        var sel = dropdown.querySelector('.custom-select-option.selected');
        if (sel) sel.scrollIntoView({ block: 'nearest' });
    }
    function close() { dropdown.style.display = 'none'; wrapper.classList.remove('open'); }

    trigger.addEventListener('click', function(e) {
        e.stopPropagation();
        dropdown.style.display === 'block' ? close() : open();
    });
    trigger.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); }
        if (e.key === 'Escape') close();
        if (e.key === 'ArrowDown') { e.preventDefault(); open(); var first = dropdown.querySelector('.custom-select-option'); if (first) first.focus(); }
    });

    options.forEach(function(opt) {
        opt.addEventListener('click', function() {
            var val = this.dataset.value;
            input.value = val;
            display.textContent = this.querySelector('span').textContent;
            display.classList.add('selected');
            wrapper.querySelectorAll('.custom-select-option').forEach(function(o) { o.classList.remove('selected'); });
            this.classList.add('selected');
            trigger.classList.remove('has-error');
            if (fieldErr) fieldErr.style.display = 'none';
            close();
        });
        opt.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') { e.preventDefault(); this.click(); }
            if (e.key === 'ArrowDown') { e.preventDefault(); var n = this.nextElementSibling; if (n && n.classList.contains('custom-select-option')) n.focus(); }
            if (e.key === 'ArrowUp') { e.preventDefault(); var p = this.previousElementSibling; if (p && p.classList.contains('custom-select-option')) p.focus(); }
            if (e.key === 'Escape') close();
        });
    });

    wrapper._close = close;
    wrapper._open = open;
}

function closeAll() {
    document.querySelectorAll('.custom-select-wrapper').forEach(function(w) {
        w.querySelector('.custom-select-dropdown').style.display = 'none';
        w.classList.remove('open');
    });
}

document.addEventListener('click', closeAll);

/* ── Dynamic select rebuild (for dependent dropdowns) ────── */
function rebuildCustomSelectOptions(inputEl, options, selectedValue) {
    var wrapper = inputEl.closest('.custom-select-wrapper');
    if (!wrapper) return;

    var display = wrapper.querySelector('.custom-select-display');
    var dropdown = wrapper.querySelector('.custom-select-dropdown');

    dropdown.innerHTML = '';
    if (!options || options.length === 0) {
        dropdown.innerHTML = '<div class="custom-select-option option-empty">Sin opciones</div>';
    }
    var found = false;
    (options || []).forEach(function(o) {
        var ov = o.value != null ? o.value : o;
        var ol = o.label != null ? o.label : o;
        var sel = String(ov) === String(selectedValue);
        if (sel) found = true;
        dropdown.innerHTML += '<div class="custom-select-option' + (sel ? ' selected' : '') + '" data-value="' + escapeHtml(ov) + '">'
            + '<span>' + escapeHtml(ol) + '</span>'
            + (sel ? '<i class="fas fa-check option-check"></i>' : '')
            + '</div>';
    });

    // Re-init event listeners on new options
    dropdown.querySelectorAll('.custom-select-option').forEach(function(opt) {
        opt.addEventListener('click', function() {
            dropdown.querySelectorAll('.custom-select-option').forEach(function(o) { o.classList.remove('selected'); var chk = o.querySelector('.option-check'); if (chk) chk.remove(); });
            this.classList.add('selected');
            var v = this.dataset.value;
            inputEl.value = v;
            display.textContent = v ? this.querySelector('span').textContent : (wrapper._placeholder || 'Seleccionar');
            display.classList.toggle('selected', !!v);
            var errEl = wrapper.closest('.crud-field').querySelector('.crud-error');
            if (errEl) errEl.style.display = 'none';
            wrapper.querySelector('.custom-select-trigger').classList.remove('has-error');
            dropdown.style.display = 'none';
            wrapper.classList.remove('open');
            inputEl.dispatchEvent(new Event('change', { bubbles: true }));
        });
    });

    // Update display
    var match = found ? options.find(function(o) { return String(o.value != null ? o.value : o) === String(selectedValue); }) : null;
    display.textContent = match ? match.label : (wrapper._placeholder || 'Seleccionar');
    display.classList.toggle('selected', !!match);
    inputEl.value = selectedValue || '';
    dropdown.style.display = 'none';
}

/* ── Form Submit + Validation ───────────────────────────── */

function submitForm(config, isEdit) {
    var form = document.getElementById('crudDrawerForm');
    var host = document.getElementById('crudDrawerHost');
    var inner = host.querySelector('.crud-drawer-panel');

    clearErrors(inner);
    var errors = validateFields(config, inner);
    if (errors.length > 0) {
        var first = inner.querySelector('.has-error, .custom-select-trigger.has-error');
        if (first) first.focus();
        return;
    }

    var btn = document.getElementById('crudDrawerSubmit');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" style="width:14px;height:14px;"></span> Procesando...';

    var idEl = document.getElementById('crudField_id');
    var id = idEl ? idEl.value : '';
    var url = (id && config.editUrl) ? (config.editUrl + id + '/edit/') : config.createUrl;
    var fd = new URLSearchParams(new FormData(form));

    config.fields.forEach(function(f) {
        if (f.type === 'checkbox_group') {
            fd.delete(f.name + '[]'); fd.delete(f.name);
            form.querySelectorAll('[name="' + f.name + '[]"]:checked').forEach(function(cb) { fd.append(f.name, cb.value); });
        }
    });

    fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest' },
        body: fd
    })
    .then(function(r) { return r.ok ? r.json() : r.text().then(function(t) { throw new Error(t ? t.substring(0, 200) : 'HTTP ' + r.status); }); })
    .then(function(data) {
        if (data.success) {
            closeCrudDrawer();
            var fem = config.label.endsWith('a') || config.label.endsWith('d');
            var msg = config.label + (isEdit ? ' actualizad' : ' cread') + (fem ? 'a' : 'o');
            if (typeof showToast === 'function') showToast(msg, 'success');
            setTimeout(function() { if (data.redirect) window.location.href = data.redirect; else location.reload(); }, 500);
        } else {
            var errMsg = data.errors ? flattenErrors(data.errors) : (data.error || 'Error desconocido');
            if (typeof showToast === 'function') showToast(errMsg, 'error');
        }
    })
    .catch(function(err) {
        if (typeof showToast === 'function') showToast(err.message || 'Error de conexión', 'error');
    })
    .finally(function() {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-check"></i>' + (isEdit ? 'Guardar' : 'Crear ' + config.label);
    });
}

function validateFields(config, container) {
    var errors = [];
    config.fields.forEach(function(f) {
        if (!f.required) return;
        var fieldEl = document.getElementById('crudField_' + f.name);
        var errEl = container.querySelector('#crudField_' + f.name) ? container.querySelector('#crudField_' + f.name).closest('.crud-field').querySelector('.crud-error') : null;

        var isEmpty = false;
        var target = null;

        if (f.type === 'select') {
            var wrapper = container.querySelector('.custom-select-wrapper input[name="' + f.name + '"]')?.closest('.custom-select-wrapper');
            var hidden = wrapper?.querySelector('.custom-select-value');
            isEmpty = !hidden || !hidden.value;
            target = wrapper?.querySelector('.custom-select-trigger');
            if (isEmpty && errEl) {
                errEl.textContent = 'Seleccioná ' + f.label.toLowerCase();
                errEl.style.display = 'block';
                if (target) target.classList.add('has-error');
            }
        } else {
            var val = fieldEl ? fieldEl.value : '';
            isEmpty = !val || (typeof val === 'string' && !val.trim());
            if (isEmpty && errEl) {
                errEl.textContent = f.label + ' es obligatorio';
                errEl.style.display = 'block';
                if (fieldEl) fieldEl.classList.add('has-error');
                target = fieldEl;
            }
        }

        if (isEmpty) errors.push({ field: f, target: target });
    });
    return errors;
}

function clearErrors(container) {
    container.querySelectorAll('.crud-error').forEach(function(e) { e.style.display = 'none'; e.textContent = ''; });
    container.querySelectorAll('.has-error').forEach(function(e) { e.classList.remove('has-error'); });
}

/* ── Drawer Lifecycle ────────────────────────────────────── */

function animateIn(panel) {
    panel.style.transform = 'translateX(100%)';
    panel.style.transition = 'transform 0.2s ease';
    requestAnimationFrame(function() { requestAnimationFrame(function() { panel.style.transform = 'translateX(0)'; }); });
}

function closeCrudDrawer() {
    var host = document.getElementById('crudDrawerHost');
    if (!host) return;
    var inner = host.querySelector('.crud-drawer-panel');
    if (inner) {
        inner.style.transform = 'translateX(100%)';
        setTimeout(function() { host.style.display = 'none'; inner.innerHTML = ''; }, 200);
    }
}

/* ── Helpers ─────────────────────────────────────────────── */

function resolveOptions(f, data) {
    if (f.options) return f.options;
    if (f.optionsData) {
        var raw = window[f.optionsData] || [];
        return typeof raw[0] === 'object' ? raw : raw.map(function(v) { return {value: v, label: v}; });
    }
    if (f.optionsFrom) {
        var raw2 = (data && data[f.optionsFrom]) ? data[f.optionsFrom] : (window[f.optionsFrom] || []);
        return typeof raw2[0] === 'object' ? raw2 : raw2.map(function(v) { return {value: v, label: v}; });
    }
    return [];
}

function attr(name, value) { return value ? ' ' + name + '="' + escapeHtml(value) + '"' : ''; }

function flattenErrors(errors) {
    if (typeof errors === 'string') return errors;
    var msgs = [];
    for (var key in errors) {
        if (Array.isArray(errors[key])) msgs = msgs.concat(errors[key]);
        else msgs.push(errors[key]);
    }
    return msgs.join(', ') || 'Error';
}

function getCsrfToken() {
    var input = document.querySelector('[name=csrfmiddlewaretoken]');
    if (input && input.value) return input.value;
    var meta = document.querySelector('meta[name=csrf-token]');
    if (meta && meta.content) return meta.content;
    var match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

function escapeHtml(str) {
    if (str == null) return '';
    return String(str).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
