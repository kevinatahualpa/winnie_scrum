document.addEventListener('DOMContentLoaded', function() {
    const areaFilter = document.getElementById('areaFilter');
    const projectFilter = document.getElementById('projectFilter');
    const sortSelect = document.getElementById('sortSelect');

    areaFilter?.addEventListener('change', function() {
        const url = new URL(window.location.href);
        if (this.value) {
            url.searchParams.set('area', this.value);
        } else {
            url.searchParams.delete('area');
        }
        url.searchParams.delete('project');
        window.location.href = url.toString();
    });

    projectFilter?.addEventListener('change', function() {
        const url = new URL(window.location.href);
        if (this.value) {
            url.searchParams.set('project', this.value);
        } else {
            url.searchParams.delete('project');
        }
        window.location.href = url.toString();
    });

    sortSelect?.addEventListener('change', function() {
        const url = new URL(window.location.href);
        url.searchParams.set('sort', this.value);
        window.location.href = url.toString();
    });
});
