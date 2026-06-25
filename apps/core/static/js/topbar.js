document.getElementById('sidebarToggle')?.addEventListener('click', function() {
    document.querySelector('.sidebar').classList.toggle('show');
});

(function() {
    var searchInput = document.getElementById('globalSearch');
    if (!searchInput) return;

    var dropdown = null;
    var debounceTimer = null;

    function createDropdown() {
        dropdown = document.createElement('div');
        dropdown.className = 'search-dropdown';
        dropdown.style.cssText = '\n        position:absolute;top:100%;right:0;width:320px;max-height:400px;overflow-y:auto;\n        background:#fff;border:1px solid var(--border);border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,0.1);\n        z-index:1050;display:none;margin-top:4px;\n    ';
        searchInput.closest('.position-relative').appendChild(dropdown);
    }

    function showLoading() {
        if (!dropdown) createDropdown();
        dropdown.innerHTML = '<div class="text-center py-3"><div class="spinner-border spinner-border-sm text-secondary" role="status"></div><div class="small text-muted mt-1">Buscando...</div></div>';
        dropdown.style.display = 'block';
    }

    function renderResults(data) {
        if (!dropdown) createDropdown();
        var html = '';

        if (data.projects && data.projects.length) {
            html += '<div class="search-group"><div class="search-group-title"><i class="fas fa-folder"></i> Proyectos</div>';
            data.projects.forEach(function(p) {
                html += '<a href="/ver_proyectos/' + p.id + '/" class="search-item">' + escapeHtml(p.name) + '</a>';
            });
            html += '</div>';
        }

        if (data.tasks && data.tasks.length) {
            html += '<div class="search-group"><div class="search-group-title"><i class="fas fa-tasks"></i> Tareas</div>';
            data.tasks.forEach(function(t) {
                var projectLabel = t.project__name ? ' <span class="text-muted">\xb7 ' + escapeHtml(t.project__name) + '</span>' : '';
                html += '<a href="/task/' + t.id + '/edit/" class="search-item">' + escapeHtml(t.title) + projectLabel + '</a>';
            });
            html += '</div>';
        }

        if (data.users && data.users.length) {
            html += '<div class="search-group"><div class="search-group-title"><i class="fas fa-users"></i> Usuarios</div>';
            data.users.forEach(function(u) {
                html += '<a href="/ver_equipo/' + u.id + '/edit/" class="search-item">' + escapeHtml(u.first_name + ' ' + u.last_name) + ' <span class="text-muted">\xb7 ' + escapeHtml(u.email) + '</span></a>';
            });
            html += '</div>';
        }

        if (!html) {
            html = '<div class="text-center py-4 text-muted small"><i class="fas fa-search d-block mb-1" style="font-size:1.2rem;opacity:0.3;"></i>Sin resultados</div>';
        }

        dropdown.innerHTML = html;
        dropdown.style.display = 'block';
    }

    function doSearch(query) {
        if (!query) {
            if (dropdown) dropdown.style.display = 'none';
            return;
        }
        showLoading();
        fetch('/buscar/?q=' + encodeURIComponent(query))
            .then(function(r) { return r.json(); })
            .then(renderResults)
            .catch(function() {
                if (dropdown) {
                    dropdown.innerHTML = '<div class="text-center py-3 text-danger small">Error al buscar</div>';
                }
            });
    }

    searchInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        var val = this.value.trim();
        if (val.length < 2) {
            if (dropdown) dropdown.style.display = 'none';
            return;
        }
        debounceTimer = setTimeout(function() { doSearch(val); }, 300);
    });

    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            if (dropdown) dropdown.style.display = 'none';
            this.blur();
        }
    });

    document.addEventListener('click', function(e) {
        if (dropdown && !e.target.closest('.position-relative') && dropdown.style.display !== 'none') {
            dropdown.style.display = 'none';
        }
    });

    function escapeHtml(text) {
        var div = document.createElement('div');
        div.appendChild(document.createTextNode(text));
        return div.innerHTML;
    }
})();
