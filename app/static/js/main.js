// Basis JavaScript für TerminFinder
document.addEventListener('DOMContentLoaded', function() {
    console.log('TerminFinder geladen');

    // Smooth scrolling für Navigation
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
});