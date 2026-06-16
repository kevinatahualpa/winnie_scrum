document.addEventListener('DOMContentLoaded', function() {
    const specialtySelect = document.querySelector('[name="required_specialty"]');
    const assigneeSelect = document.getElementById('assigneeSelect');
    const assigneeHint = document.getElementById('assigneeHint');
    const allOptions = Array.from(assigneeSelect.querySelectorAll('option'));

    function filterBySpecialty() {
        const specialtyId = specialtySelect.value;
        const currentAssignee = assigneeSelect.value;

        if (!specialtyId) {
            assigneeSelect.innerHTML = '';
            allOptions.forEach(opt => assigneeSelect.appendChild(opt));
            assigneeHint.style.display = 'none';
            return;
        }

        assigneeHint.style.display = 'block';
        assigneeHint.innerHTML = '<i class="fas fa-filter me-1"></i>Mostrando solo usuarios con esta especialidad';

        const filtered = allOptions.filter(opt => {
            if (opt.value === '') return true;
            return opt.dataset.specialty === specialtyId;
        });

        assigneeSelect.innerHTML = '';
        filtered.forEach(opt => assigneeSelect.appendChild(opt));

        if (filtered.length === 1) {
            assigneeHint.innerHTML = '<i class="fas fa-exclamation-triangle me-1" style="color:#f59e0b"></i>No hay usuarios con esta especialidad';
        } else {
            const count = filtered.length - 1;
            assigneeHint.innerHTML = `<i class="fas fa-users me-1" style="color:var(--success)"></i>${count} usuario(s) con esta especialidad`;
        }

        if (currentAssignee && assigneeSelect.querySelector(`option[value="${currentAssignee}"]`)) {
            assigneeSelect.value = currentAssignee;
        }
    }

    specialtySelect?.addEventListener('change', filterBySpecialty);
    filterBySpecialty();
});
