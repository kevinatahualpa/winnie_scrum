document.addEventListener('DOMContentLoaded', function() {
    const events = window.calendarEvents || [];
    const year = window.calendarYear;
    const month = window.calendarMonth - 1;

    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const today = new Date();

    let html = '';

    for (let i = 0; i < firstDay; i++) {
        html += '<div class="cal-day empty"></div>';
    }

    for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const isToday = today.getDate() === day && today.getMonth() === month && today.getFullYear() === year;
        const dayEvents = events.filter(e => e.date === dateStr);

        html += `<div class="cal-day${isToday ? ' today' : ''}">`;
        html += `<div class="cal-day-num">${day}</div>`;

        dayEvents.slice(0, 3).forEach(event => {
            html += `<span class="cal-event" style="background:${event.color}18;color:${event.color}" title="${event.title}">${event.title}</span>`;
        });

        if (dayEvents.length > 3) {
            html += `<div class="cal-event-more">+${dayEvents.length - 3} más</div>`;
        }

        html += '</div>';
    }

    document.getElementById('calendarGrid').innerHTML = html;
});
