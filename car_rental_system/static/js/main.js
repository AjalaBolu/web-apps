// ============================================
// main.js - DriveEase Car Rental System
// ============================================
// General JavaScript for the frontend.
// Handles UI interactions and enhancements.

document.addEventListener('DOMContentLoaded', function () {

    // ----------------------------------------
    // Auto-dismiss flash alerts after 4 seconds
    // ----------------------------------------
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 4000);
    });

    // ----------------------------------------
    // Add active class to current nav link
    // based on the current URL path
    // ----------------------------------------
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(function (link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // ----------------------------------------
    // Confirm before any delete action
    // (Extra safety check for delete buttons)
    // ----------------------------------------
    const deleteForms = document.querySelectorAll('form[onsubmit]');
    // Already handled inline with onsubmit="return confirm(...)"

    // ----------------------------------------
    // Animate cards on page load
    // ----------------------------------------
    const cards = document.querySelectorAll('.car-card');
    cards.forEach(function (card, index) {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';

        setTimeout(function () {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 80); // Stagger each card by 80ms
    });

});
