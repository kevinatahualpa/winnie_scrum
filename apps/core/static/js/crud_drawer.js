/**
 * crud_drawer.js - Generic slide-in drawer for CRUD operations.
 *
 * Usage:
 *   initCrudDrawer({
 *       entity: 'project',
 *       label: 'Proyecto',
 *       fields: [
 *           {name:'name', label:'Nombre', type:'text', required:true},
 *           {name:'email', label:'Email', type:'email'},
 *           {name:'budget', label:'Presupuesto', type:'number', default:0},
 *           {name:'start', label:'Inicio', type:'date'},
 *           {name:'area', label:'Area', type:'select', options: [...]},
 *           {name:'client', label:'Cliente', type:'select', optionsData:'clientOptions'},
 *       ],
 *       createUrl: '/.../create/',
 *       editUrl: '/.../',
 *   });
 *
 * Supported field types: text, email, tel, number, date, color, textarea, select, checkbox_group
 * For select: use `options` (inline array) or `optionsData` (global variable name).
 * For checkbox_group: uses {name}[] as form field name.
 */

var __crudInstances = {};

function initCrudDrawer(config) {
    __crudInstances[config.entity] = config;

    if (!document.getElementById('crudDrawerHost')) {
        var host = document.createElement('div');
        host.id = 'crudDrawerHost';
        host.style.cssText = 'position:fixed;inset:0;z-index:99999;display:none;justify-content:flex-end;background:rgba(15,23,42,0.55);';
        host.innerHTML = '<div class="crud-drawer-inner" style="width:480px;max-width:92vw;height:100vh;background:var(--surface);box-shadow:-8px 0 24px rgba(0,0,0,0.2);display:flex;flex-direction:column;overflow:hidden;"></div>';
        document.body.appendChild(host);

        host.addEventListener('click', function(e) {
            if (e.target === host) closeCrudDrawer();
        });
    }

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') closeCrudDrawer();
    });
}

function openCrudDrawer(entity, data) {
    var config = __crudInstances[entity];
    if (!config) return;

    var host = document.getElementById('crudDrawerHost');
    var inner = host.querySelector('.crud-drawer-inner');
    var isEdit = data && data.id;

    var html = '';
    html += '<div class="drawer-header">';
    html += '  <h6 class="mb-0">' + (isEdit ? 'Editar ' : 'Nuevo ') + config.label + '</h6>';
    html += '  <button type="button" class="btn-close-drawer ms-auto" onclick="closeCrudDrawer()"><i class="fas fa-times"></i></button>';
    html += '</div>';
    html += '<div style="flex:1;overflow-y:auto;padding:1.25rem;">';
    html += '  <form id="crudDrawerForm">';
    html += '    <input type="hidden" name="csrfmiddlewaretoken" value="' + getCsrfToken() + '">';
    html += '    <input type="hidden" name="id" id="crudField_id" value="' + (data ? (data.id || '') : '') + '">';

    config.fields.forEach(function(f) {
        var val = data ? (data[f.name] != null ? data[f.name] : (f.default || '')) : (f.default || '');
        html += '    <div class="mb-2">';
        html += '      <label class="form-label small">' + f.label + (f.required ? ' *' : '') + '</label>';

        if (f.type === 'textarea') {
            html += '      <textarea name="' + f.name + '" id="crudField_' + f.name + '" class="form-control form-control-sm" rows="' + (f.rows || 2) + '"' + attr('placeholder', f.placeholder) + (f.required ? ' required' : '') + '>' + escapeHtml(val) + '</textarea>';
        } else if (f.type === 'color') {
            html += '      <input type="color" name="' + f.name + '" id="crudField_' + f.name + '" class="form-control form-control-color" value="' + escapeHtml(val) + '"' + (f.required ? ' required' : '') + '>';
        } else if (f.type === 'select') {
            var opts = resolveOptions(f, data);
            html += '      <select name="' + f.name + '" id="crudField_' + f.name + '" class="form-select form-select-sm"' + (f.required ? ' required' : '') + '>';
            if (f.emptyLabel !== false) {
                html += '        <option value="">' + (f.emptyLabel || '-- ' + f.label + ' --') + '</option>';
            }
            opts.forEach(function(o) {
                var ov = (o.value != null ? o.value : o);
                var ol = (o.label != null ? o.label : o);
                var selected = (String(ov) === String(val)) ? ' selected' : '';
                html += '        <option value="' + escapeHtml(ov) + '"' + selected + '>' + escapeHtml(ol) + '</option>';
            });
            html += '      </select>';
        } else if (f.type === 'checkbox_group') {
            var copts = resolveOptions(f, data);
            html += '      <div class="row g-1">';
            var valArr = val;
            if (typeof val === 'string' && val) valArr = val.split(',');
            if (!valArr) valArr = [];
            copts.forEach(function(o) {
                var ov = (o.value != null ? o.value : o);
                var ol = (o.label != null ? o.label : o);
                var checked = valArr.indexOf(String(ov)) !== -1 ? ' checked' : '';
                html += '        <div class="col-6">';
                html += '          <label class="form-check form-check-sm">';
                html += '            <input class="form-check-input" type="checkbox" name="' + f.name + '[]" value="' + escapeHtml(ov) + '"' + checked + '>';
                html += '            <span class="form-check-label small">' + escapeHtml(ol) + '</span>';
                html += '          </label>';
                html += '        </div>';
            });
            html += '      </div>';
        } else {
            var inputType = f.type || 'text';
            if (inputType === 'phone') inputType = 'tel';
            html += '      <input type="' + inputType + '" name="' + f.name + '" id="crudField_' + f.name + '" class="form-control form-control-sm" value="' + escapeHtml(val) + '"' + (f.step ? ' step="' + f.step + '"' : '') + attr('placeholder', f.placeholder) + (f.required ? ' required' : '') + '>';
        }
        html += '    </div>';
    });

    html += '  </form>';
    html += '</div>';
    html += '<div class="d-flex justify-content-end gap-2 p-3 border-top">';
    html += '  <button type="button" class="btn btn-sm btn-ghost" onclick="closeCrudDrawer()">Cancelar</button>';
    html += '  <button type="submit" form="crudDrawerForm" class="btn btn-sm btn-success" id="crudDrawerSubmit"><i class="fas fa-save me-1"></i> Guardar</button>';
    html += '</div>';

    // Fix gender for 'Nuevo/Nueva'
    var fem = ['Area', 'Especialidad', 'Tecnologia', 'Solicitud'];
    if (!isEdit && fem.indexOf(config.label) !== -1) {
        html = html.replace('Nuevo ', 'Nueva ');
    }

    inner.innerHTML = html;
    host.style.display = 'flex';

    inner.style.transform = 'translateX(100%)';
    inner.style.transition = 'transform 0.18s ease';
    requestAnimationFrame(function() {
        requestAnimationFrame(function() {
            inner.style.transform = 'translateX(0)';
        });
    });

    setTimeout(function() {
        var firstInput = inner.querySelector('input:not([type=hidden]):not([type=color]), textarea, select');
        if (firstInput) firstInput.focus();
    }, 200);

    var form = document.getElementById('crudDrawerForm');
    if (form) {
        form.onsubmit = function(e) {
            e.preventDefault();
            var btn = document.getElementById('crudDrawerSubmit');
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

            var idEl = document.getElementById('crudField_id');
            var id = idEl ? idEl.value : '';
            var url;
            if (id && config.editUrl) {
                url = config.editUrl + id + '/edit/';
            } else {
                url = config.createUrl;
            }
            var formData = new URLSearchParams(new FormData(this));

            // Normalize checkbox_group values for Django (send each as separate param)
            config.fields.forEach(function(f) {
                if (f.type === 'checkbox_group') {
                    formData.delete(f.name + '[]');
                    formData.delete(f.name);
                    var checked = form.querySelectorAll('[name="' + f.name + '[]"]:checked');
                    checked.forEach(function(cb) { formData.append(f.name, cb.value); });
                }
            });

            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.success) {
                    closeCrudDrawer();
                    showToast(config.label + (isEdit ? ' actualizad' : ' cread') + (fem.indexOf(config.label) !== -1 ? 'a' : 'o'), 'success');
                    setTimeout(function() {
                        if (data.redirect) { window.location.href = data.redirect; }
                        else { location.reload(); }
                    }, 500);
                } else {
                    showToast(data.errors ? flattenErrors(data.errors) : (data.error || 'Error'), 'error');
                }
            })
            .catch(function() { showToast('Error de conexion', 'error'); })
            .finally(function() {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-save me-1"></i> Guardar';
            });
        };
    }
}

function closeCrudDrawer() {
    var host = document.getElementById('crudDrawerHost');
    if (!host) return;
    var inner = host.querySelector('.crud-drawer-inner');
    if (inner) {
        inner.style.transform = 'translateX(100%)';
        setTimeout(function() {
            host.style.display = 'none';
            inner.innerHTML = '';
        }, 180);
    } else {
        host.style.display = 'none';
    }
}

// --- helpers ---

function resolveOptions(f, data) {
    if (f.options) return f.options;
    if (f.optionsData) {
        var raw = window[f.optionsData] || [];
        if (typeof raw[0] === 'object') return raw;
        return raw.map(function(v) { return {value: v, label: v}; });
    }
    if (f.optionsFrom) {
        // optionsFrom: 'otherFieldName' -> use the value from the data object
        var key = f.optionsFrom;
        var raw2 = (data && data[key]) ? data[key] : (window[key] || []);
        if (typeof raw2[0] === 'object') return raw2;
        return raw2.map(function(v) { return {value: v, label: v}; });
    }
    return [];
}

function attr(name, value) {
    return value ? ' ' + name + '="' + escapeHtml(value) + '"' : '';
}

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
    var match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

function escapeHtml(str) {
    if (str == null) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}
