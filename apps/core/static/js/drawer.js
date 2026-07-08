/**
 * drawer.js - Logica del drawer de revision de candidatos.
 *
 * IMPORTANTE: Este script se carga UNA SOLA VEZ al cargar la pagina.
 * El contenido del drawer se inyecta via AJAX (innerHTML), por lo que
 * los <script> dentro del HTML inyectado NO se ejecutan. Toda la
 * logica del drawer debe vivir aca y referenciar elementos por id
 * (que existen solo cuando el drawer esta abierto).
 *
 * Usamos event delegation en document para que los clicks en botones
 * que aparecen despues (inyectados via AJAX) sigan funcionando.
 */

(function() {
    'use strict';

    if (window.__winnieDrawerLoaded) return;
    window.__winnieDrawerLoaded = true;

    // ------------------------------------------------------------------
    // Helpers
    // ------------------------------------------------------------------

    function getCsrfToken() {
        // Primero intenta leerlo del input hidden (caso AJAX con drawer inyectado)
        const input = document.getElementById('csrfToken');
        if (input && input.value) return input.value;
        const meta = document.querySelector('meta[name=csrf-token]');
        if (meta && meta.content) return meta.content;
        const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        if (match) return match[1];
        return '';
    }

    function getDecidirUrl() {
        // Leemos el atributo data-url del boton aprobar
        const btn = document.getElementById('approveBtn');
        if (!btn) return null;
        // El form POST apunta a /pending/<pk>/decidir/ que esta embebido
        // en la URL del form de saveChecklist o como data-* attribute.
        // Lo mas simple: derivarlo de la URL del drawer o usar una variable
        // global que el drawer template setea en un input hidden.
        const urlInput = document.getElementById('decidirUrl');
        if (urlInput && urlInput.value) return urlInput.value;
        return null;
    }

    function getChecklistUrl() {
        const urlInput = document.getElementById('checklistUrl');
        return urlInput ? urlInput.value : null;
    }

    // ------------------------------------------------------------------
    // Score del checklist
    // ------------------------------------------------------------------

    function updateScore() {
        const checks = document.querySelectorAll('.cl-item input[type=checkbox]');
        if (checks.length === 0) return 0;
        let score = 0;
        checks.forEach(c => { if (c.checked) score++; });
        const pill = document.getElementById('scorePill');
        if (pill) {
            const total = checks.length;
            pill.textContent = `${score}/${total}`;
            pill.classList.remove('ready', 'warn');
            if (score >= 3) pill.classList.add('ready');
            else if (score >= 2) pill.classList.add('warn');
        }
        return score;
    }

    // ------------------------------------------------------------------
    // Save checklist (AJAX)
    // ------------------------------------------------------------------

    async function saveChecklist(silent) {
        const form = document.getElementById('checklistForm');
        if (!form) return;
        const url = getChecklistUrl();
        if (!url) return;

        const noteEl = document.getElementById('reviewNote');
        const note = noteEl ? noteEl.value : '';
        const checks = {};
        form.querySelectorAll('input[type=checkbox]').forEach(c => { checks[c.name] = c.checked; });

        const csrf = getCsrfToken();

        const msg = document.getElementById('checklistMsg');
        const btn = document.getElementById('saveChecklistBtn');
        if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>'; }
        try {
            // Django acepta el token como form data; mas confiable que el header
            const formData = new FormData();
            formData.append('csrfmiddlewaretoken', csrf);
            formData.append('note', note);
            Object.keys(checks).forEach(k => formData.append(k, checks[k] ? 'true' : 'false'));

            const res = await fetch(url, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrf },
                body: formData,
            });
            const json = await res.json();
            if (json.ok) {
                if (msg) msg.innerHTML = `<span class="text-success"><i class="fas fa-check-circle"></i> Guardado · ${json.completed_at}</span>`;
            } else {
                if (msg) msg.innerHTML = `<span class="text-danger">${json.error || 'Error'}</span>`;
            }
        } catch (e) {
            if (msg) msg.innerHTML = `<span class="text-danger">No se pudo guardar</span>`;
        } finally {
            if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-save me-1"></i> Guardar checklist'; }
        }
    }

    // ------------------------------------------------------------------
    // Aprobar / Rechazar (AJAX)
    // ------------------------------------------------------------------

    async function decidir(decision) {
        const url = getDecidirUrl();
        if (!url) {
            console.error('drawer: decidir URL not found');
            return;
        }
        const score = updateScore();
        if (decision === 'approve' && score < 3) {
            const msg = document.getElementById('decisionMsg');
            if (msg) msg.innerHTML =
                `<span class="text-danger"><i class="fas fa-exclamation-triangle"></i> Score ${score}/${document.querySelectorAll('.cl-item input[type=checkbox]').length} insuficiente (min 3)</span>`;
            return;
        }

        const formData = new FormData();
        formData.append('decision', decision);
        const roleEl = document.getElementById('finalRole');
        const areaEl = document.getElementById('finalArea');
        const noteEl = document.getElementById('reviewNote');
        if (roleEl) formData.append('role', roleEl.value);
        if (areaEl) formData.append('area', areaEl.value);
        if (decision === 'reject' && noteEl) formData.append('notes', noteEl.value);
        // CSRF como form data (Django lo lee antes que el header)
        formData.append('csrfmiddlewaretoken', getCsrfToken());

        const msg = document.getElementById('decisionMsg');
        const btnA = document.getElementById('approveBtn');
        const btnR = document.getElementById('rejectBtn');
        if (btnA) btnA.disabled = true;
        if (btnR) btnR.disabled = true;
        if (msg) msg.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrfToken() },
                body: formData,
            });
            const ct = res.headers.get('content-type') || '';
            if (!ct.includes('application/json')) {
                console.error('drawer: non-JSON response, status', res.status);
                if (msg) msg.innerHTML = `<span class="text-danger">No se pudo procesar. Recargá la página.</span>`;
                if (btnA) btnA.disabled = false;
                if (btnR) btnR.disabled = false;
                return;
            }
            const payload = await res.json();
            if (payload.ok) {
                if (msg) msg.innerHTML = '<span class="text-success">Listo, redirigiendo...</span>';
                window.location.href = payload.redirect || '/ver_pendientes/';
            } else {
                if (msg) msg.innerHTML = `<span class="text-danger">${payload.error || 'Error'}</span>`;
                if (btnA) btnA.disabled = false;
                if (btnR) btnR.disabled = false;
            }
        } catch (e) {
            if (msg) msg.innerHTML = `<span class="text-danger">No se pudo conectar. Reintentá.</span>`;
            if (btnA) btnA.disabled = false;
            if (btnR) btnR.disabled = false;
        }
    }

    // ------------------------------------------------------------------
    // PDF zoom
    // ------------------------------------------------------------------

    function setupPdfZoom() {
        const frame = document.getElementById('pdfFrame');
        const label = document.getElementById('pdfZoomLabel');
        const viewport = document.getElementById('pdfViewport');
        if (!frame || !label || !viewport) return;
        let zoom = 100;
        const apply = () => {
            frame.style.transform = `scale(${zoom/100})`;
            frame.style.transformOrigin = 'top left';
            frame.style.width = `${10000/zoom}%`;
            frame.style.height = `${10000/zoom}%`;
            label.textContent = zoom + '%';
        };
        const zoomIn = document.getElementById('pdfZoomIn');
        const zoomOut = document.getElementById('pdfZoomOut');
        const full = document.getElementById('pdfFullscreen');
        if (zoomIn) zoomIn.onclick = () => { zoom = Math.min(200, zoom + 25); apply(); };
        if (zoomOut) zoomOut.onclick = () => { zoom = Math.max(50, zoom - 25); apply(); };
        if (full) full.onclick = () => viewport.classList.toggle('fullscreen');
    }

    // Hook publico: el pending_registrations.html llama a esto despues
    // de inyectar el HTML del drawer.
    window.initDrawerContent = function() {
        setupPdfZoom();
        updateScore();
        // Limpiar cualquier mensaje de error residual de una sesion anterior
        const cm = document.getElementById('checklistMsg');
        const dm = document.getElementById('decisionMsg');
        if (cm) cm.innerHTML = '';
        if (dm) dm.innerHTML = '';
    };

    // ------------------------------------------------------------------
    // Event delegation
    // ------------------------------------------------------------------

    document.addEventListener('click', function(e) {
        const approve = e.target.closest('#approveBtn');
        if (approve) {
            e.preventDefault();
            decidir('approve');
            return;
        }
        const reject = e.target.closest('#rejectBtn');
        if (reject) {
            e.preventDefault();
            decidir('reject');
            return;
        }
        const save = e.target.closest('#saveChecklistBtn');
        if (save) {
            e.preventDefault();
            saveChecklist(false);
            return;
        }
        const zoomIn = e.target.closest('#pdfZoomIn');
        if (zoomIn && zoomIn.onclick) { e.preventDefault(); zoomIn.onclick(); return; }
        const zoomOut = e.target.closest('#pdfZoomOut');
        if (zoomOut && zoomOut.onclick) { e.preventDefault(); zoomOut.onclick(); return; }
        const full = e.target.closest('#pdfFullscreen');
        if (full && full.onclick) { e.preventDefault(); full.onclick(); return; }
    });

    document.addEventListener('change', function(e) {
        if (e.target.matches && e.target.matches('.cl-item input[type=checkbox]')) {
            updateScore();
            clearTimeout(window._clTimer);
            window._clTimer = setTimeout(() => saveChecklist(true), 600);
        }
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && typeof window.closeDrawer === 'function') {
            window.closeDrawer();
        }
    });

})();
