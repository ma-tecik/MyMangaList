// JS fore List page and Series info page

// Global state
let currentStatus = '';
let section = '';

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function () {
    const path = window.location.pathname;
    const statusMatch = path.match(/\/series\/(.+)/);
    if (statusMatch) {
        currentStatus = statusMatch[1];
    }

    if (currentStatus === "plan-to") {
        section = "planTo";
    } else if (currentStatus === "one-shots") {
        section = "oneShots";
    } else if (currentStatus === "on-hold") {
        section = "onHold";
    } else {
        section = currentStatus;
    }

    const el = document.getElementById(`${section}`);
    if (el) {
        el.classList.add('active');
    }
});