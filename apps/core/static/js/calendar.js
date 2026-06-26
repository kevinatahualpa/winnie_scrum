document.addEventListener('DOMContentLoaded', function() {
    const events = window.calendarEvents || [];
    const year = window.calendarYear;
    const month = window.calendarMonth - 1;

    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const today = new Date();
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

    const eventsByDate = {};
    events.forEach(e => {
        if (!eventsByDate[e.date]) eventsByDate[e.date] = [];
        eventsByDate[e.date].push(e);
    });

    let html = '';

    for (let i = 0; i < firstDay; i++) {
        html += '<div class="cal-day empty"></div>';
    }

    for (let day = 1; day <= daysInMonth; day++) {
        const m = String(month + 1).padStart(2, '0');
        const d = String(day).padStart(2, '0');
        const dateStr = `${year}-${m}-${d}`;
        const isToday = dateStr === todayStr;
        const dayEvents = eventsByDate[dateStr] || [];
        const hasEvents = dayEvents.length > 0;

        html += `<div class="cal-day${isToday ? ' today' : ''}${hasEvents ? ' has-events' : ''}" data-date="${dateStr}" onclick="openCalDrawer('${dateStr}')" role="button" tabindex="0" aria-label="${day} de ${m} — ${dayEvents.length} evento(s)">`;
        html += `<div class="cal-day-num">${day}</div>`;

        dayEvents.slice(0, 3).forEach(event => {
            const iconClass = event.icon || 'fa-circle';
            html += `<span class="cal-event" style="background:${event.color}18;color:${event.color}" title="${escapeAttr(event.title)}"><i class="fas ${iconClass} cal-event-icon"></i>${escapeHtml(event.title)}</span>`;
        });

        if (dayEvents.length > 3) {
            html += `<div class="cal-event-more">+${dayEvents.length - 3} más</div>`;
        }

        html += '</div>';
    }

    document.getElementById('calendarGrid').innerHTML = html;
});

function openCalDrawer(dateStr) {
    const events = window.calendarEvents || [];
    const dayEvents = events.filter(e => e.date === dateStr);
    const [y, m, d] = dateStr.split('-');
    const monthNames = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
    const title = `${parseInt(d)} de ${monthNames[parseInt(m)]} de ${y}`;
    const weekDay = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'][new Date(y, parseInt(m) - 1, parseInt(d)).getDay()];
    const fullTitle = `${weekDay} ${title}`;

    document.getElementById('calDrawerTitle').textContent = fullTitle;

    let body = '';
    if (dayEvents.length === 0) {
        body = '<div class="text-center text-secondary py-4"><i class="far fa-calendar fa-2x mb-2 d-block" style="opacity:0.3"></i>Sin eventos este día</div>';
    } else {
        dayEvents.forEach(event => {
            body += `<div class="cal-drawer-event">
                <div class="cal-drawer-event-bar" style="background:${event.color}"></div>
                <div class="cal-drawer-event-body">
                    <div class="cal-drawer-event-title"><i class="fas ${event.icon} cal-drawer-event-icon"></i>${escapeHtml(event.title)}</div>
                    <div class="cal-drawer-event-meta">
                        <span class="cal-drawer-event-tag" style="background:${event.color}18;color:${event.color}">${event.label}</span>
                        ${event.project ? `<span class="cal-drawer-event-project"><i class="fas fa-briefcase"></i> ${escapeHtml(event.project)}</span>` : ''}
                    </div>
                    ${event.detail ? `<div class="cal-drawer-event-detail">${escapeHtml(event.detail)}</div>` : ''}
                </div>
            </div>`;
        });
    }
    document.getElementById('calDrawerBody').innerHTML = body;
    document.getElementById('calDrawer').classList.add('open');
    document.getElementById('calDrawerOverlay').classList.add('open');
    document.body.style.overflow = 'hidden';
}

function closeCalDrawer() {
    document.getElementById('calDrawer').classList.remove('open');
    document.getElementById('calDrawerOverlay').classList.remove('open');
    document.body.style.overflow = '';
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function escapeAttr(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
