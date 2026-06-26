document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function(el) { new bootstrap.Tooltip(el); });

    function applyFilters() {
        const params = new URLSearchParams();
        const area = document.getElementById('areaFilter')?.value;
        const project = document.getElementById('projectFilter')?.value;
        const role = document.getElementById('roleFilter')?.value;
        const client = document.getElementById('clientFilter')?.value;
        // Preserve current tab
        const currentUrl = new URL(window.location.href);
        const tab = currentUrl.searchParams.get('tab');
        if (tab) params.set('tab', tab);
        if (area) params.set('area', area);
        if (project) params.set('project', project);
        if (role) params.set('role', role);
        if (client) params.set('client', client);
        const qs = params.toString();
        window.location.href = qs ? `/ver_usuarios/?${qs}` : '/ver_usuarios/';
    }

    function updateProjectOptions() {
        const areaSelect = document.getElementById('areaFilter');
        const projectSelect = document.getElementById('projectFilter');
        if (!areaSelect || !projectSelect) return;
        const selectedArea = areaSelect.value;
        const allOptions = Array.from(projectSelect.querySelectorAll('option'));
        const currentProject = projectSelect.value;
        projectSelect.innerHTML = '';
        const filtered = allOptions.filter(opt => {
            if (opt.value === '') return true;
            if (!selectedArea) return true;
            return opt.dataset.area === selectedArea;
        });
        filtered.forEach(opt => projectSelect.appendChild(opt));
        if (currentProject && projectSelect.querySelector(`option[value="${currentProject}"]`)) {
            projectSelect.value = currentProject;
        }
    }

    document.getElementById('areaFilter')?.addEventListener('change', function() { updateProjectOptions(); applyFilters(); });
    document.getElementById('projectFilter')?.addEventListener('change', applyFilters);
    document.getElementById('roleFilter')?.addEventListener('change', applyFilters);
});
