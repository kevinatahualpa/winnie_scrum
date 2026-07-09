/* chat_poll.js — Delta polling eficiente para el chat.
 * - Solo pide mensajes nuevos con ?after=<last_id> (respuesta JSON ligera).
 * - Pausa cuando la pestana no esta visible (ahorra recursos del servidor).
 * - Backoff: si no hay actividad, aumenta el intervalo; al llegar mensajes, lo baja.
 */
(function () {
    var timer = null;
    var container = null;
    var lastId = 0;
    var currentUserId = null;
    var baseUrl = '';
    var interval = 4000;          // arranca en 4s
    var MIN_INTERVAL = 4000;
    var MAX_INTERVAL = 20000;     // hasta 20s si no hay actividad
    var idleCount = 0;

    function esc(s) {
        var d = document.createElement('div');
        d.textContent = s == null ? '' : s;
        return d.innerHTML;
    }

    function computeLastId() {
        var rows = container.querySelectorAll('[data-msg-id]');
        var max = 0;
        rows.forEach(function (r) {
            var id = parseInt(r.getAttribute('data-msg-id'), 10);
            if (id > max) max = id;
        });
        return max;
    }

    function atBottom() {
        return container.scrollHeight - container.scrollTop - container.clientHeight < 80;
    }

    function appendMessages(list) {
        var stick = atBottom();
        list.forEach(function (m) {
            if (container.querySelector('[data-msg-id="' + m.id + '"]')) return;
            var wrap = document.createElement('div');
            wrap.className = 'd-flex mb-2 ' + (m.is_mine ? 'justify-content-end' : '');
            wrap.setAttribute('data-msg-id', m.id);
            wrap.innerHTML =
                '<div class="message-bubble ' + (m.is_mine ? 'sent' : 'received') + '" style="max-width:70%;">' +
                    '<div class="d-flex justify-content-between align-items-center gap-2 mb-1">' +
                        '<small class="fw-bold msg-sender-' + (m.is_mine ? 'self' : 'other') + '">' + esc(m.sender_name) + '</small>' +
                        '<small style="font-size:0.55rem;opacity:0.6;">' + esc(m.time) + '</small>' +
                    '</div>' +
                    (m.subject ? '<small class="d-block mb-1" style="font-size:0.6rem;opacity:0.5;">' + esc(m.subject) + '</small>' : '') +
                    '<p class="mb-0 small">' + esc(m.body) + '</p>' +
                '</div>';
            // remove "no messages" placeholder if present
            var empty = container.querySelector('.text-center.py-5');
            if (empty) empty.remove();
            container.appendChild(wrap);
        });
        if (stick) container.scrollTop = container.scrollHeight;
    }

    function schedule() {
        clearTimeout(timer);
        timer = setTimeout(poll, interval);
    }

    function poll() {
        if (!container || document.hidden) { schedule(); return; }
        var url = baseUrl + (baseUrl.indexOf('?') > -1 ? '&' : '?') + 'after=' + lastId;
        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(function (r) { return r.json(); })
            .then(function (d) {
                if (d.messages && d.messages.length) {
                    appendMessages(d.messages);
                    lastId = d.last_id || computeLastId();
                    interval = MIN_INTERVAL;   // hubo actividad -> responde rapido
                    idleCount = 0;
                } else {
                    idleCount++;
                    if (idleCount > 3 && interval < MAX_INTERVAL) {
                        interval = Math.min(interval + 3000, MAX_INTERVAL);
                    }
                }
                schedule();
            })
            .catch(function () { schedule(); });
    }

    window.initChatPoll = function () {
        clearTimeout(timer);
        container = document.getElementById('chatMessages');
        if (!container || !container.dataset.chatPollUrl) return;
        baseUrl = container.dataset.chatPollUrl;
        currentUserId = container.dataset.chatCurrentUser;
        lastId = computeLastId();
        interval = MIN_INTERVAL;
        idleCount = 0;
        container.scrollTop = container.scrollHeight;
        schedule();
    };

    // Reanuda inmediatamente al volver a la pestana
    document.addEventListener('visibilitychange', function () {
        if (!document.hidden && container) {
            interval = MIN_INTERVAL;
            idleCount = 0;
            clearTimeout(timer);
            poll();
        }
    });
})();
