// animations.js - Utility functions for animations
function animateValue(element, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const value = Math.floor(progress * (end - start) + start);
        element.textContent = value.toLocaleString();
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

function initializeAnimations() {
    // Animate stats cards on scroll
    const statsCards = document.querySelectorAll('.stat-card');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'slideIn 0.5s ease-out forwards';
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    statsCards.forEach(card => observer.observe(card));

    // Initialize Stats Animation
    document.querySelectorAll('.stat-value').forEach(stat => {
        const value = parseInt(stat.dataset.value || stat.textContent);
        stat.textContent = '0';
        animateValue(stat, 0, value, 1000);
    });
}

// Export for use in other files
window.animations = {
    animateValue,
    initializeAnimations
}; 