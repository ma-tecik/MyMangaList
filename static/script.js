document.addEventListener('DOMContentLoaded', function () {
    const currentPath = window.location.pathname;
    let section = '';

    if (currentPath.startsWith('/plan-to')) {
        section = 'planTo';
    } else if (currentPath.startsWith('/reading')) {
        section = 'reading';
    } else if (currentPath.startsWith('/completed')) {
        section = 'completed';
    } else if (currentPath.startsWith('/one-shots')) {
        section = 'oneShots';
    } else if (currentPath.startsWith('/dropped')) {
        section = 'dropped';
    } else if (currentPath.startsWith('/ongoing')) {
        section = 'ongoing';
    }

    if (section) {
        const el = document.getElementById(`${section}`);
        if (el) {
            el.classList.add('active');
        }
    }
});