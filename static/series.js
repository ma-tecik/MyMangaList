// JS fore List page and Series related pages like add, edirt etc.

document.addEventListener('DOMContentLoaded', function () {
    const currentPath = window.location.pathname;
    let section = '';

    if (currentPath.startsWith('/series/plan-to')) {
        section = 'planTo';
    } else if (currentPath.startsWith('/series/reading')) {
        section = 'reading';
    } else if (currentPath.startsWith('/series/completed')) {
        section = 'completed';
    } else if (currentPath.startsWith('/series/one-shots')) {
        section = 'oneShots';
    } else if (currentPath.startsWith('/series/on-hold')) {
        section = 'onHold';
    } else if (currentPath.startsWith('/series/dropped')) {
        section = 'dropped';
    } else if (currentPath.startsWith('/series/ongoing')) {
        section = 'ongoing';
    }

    if (section) {
        const el = document.getElementById(`${section}`);
        if (el) {
            el.classList.add('active');
        }
    }
});