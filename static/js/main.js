// main.js - Main application entry point
document.addEventListener('DOMContentLoaded', () => {
    // Initialize global config
    window.config = {
        SHOP_URL: document.querySelector('meta[name="shop-url"]')?.content,
        active_theme_id: document.querySelector('meta[name="active-theme-id"]')?.content
    };

    // Handle loading animation
    const loader = document.querySelector('.loading');
    if (loader) {
        window.addEventListener('load', () => {
            AnimationService.fadeOut(loader);
        });
    }

    // Load AI Insights
    loadAIInsights();

    // Initialize menu toggle
    const menuToggle = document.querySelector('.menu-toggle');
    menuToggle?.addEventListener('click', () => {
        const sidebar = document.querySelector('.sidebar');
        sidebar?.classList.toggle('active');
    });

    // Mobile menu functionality
    const mobileMenuButton = document.querySelector('.mobile-menu-button');
    const mobileMenu = document.querySelector('.mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                // Close mobile menu if open
                if (mobileMenu) {
                    mobileMenu.classList.add('hidden');
                }
            }
        });
    });
});

// Load AI Insights
async function loadAIInsights() {
    const insightsContainer = document.querySelector('#ai-insights-container');
    if (!insightsContainer) return;
    
    try {
        const data = await APIService.loadAIInsights();
        
        if (data.insights && data.insights.length > 0) {
            // Split insights into initial and remaining
            const initialInsights = data.insights.slice(0, 3);
            const remainingInsights = data.insights.slice(3);
            
            // Create container for insights
            let html = '<div class="insights-wrapper space-y-3">';
            
            // Add initial insights (visible)
            html += initialInsights.map(insight => `
                <div class="flex items-start space-x-2 insight-item p-4 bg-gray-800/50 rounded-lg" style="animation: fadeIn 0.5s ease-out">
                    <i class="fas fa-lightbulb text-primary mt-1"></i>
                    <p class="flex-1">${insight}</p>
                </div>
            `).join('');
            
            // Add remaining insights (hidden)
            if (remainingInsights.length > 0) {
                html += `<div class="hidden" id="remaining-insights">`;
                html += remainingInsights.map(insight => `
                    <div class="flex items-start space-x-2 insight-item p-4 bg-gray-800/50 rounded-lg" style="animation: fadeIn 0.5s ease-out">
                        <i class="fas fa-lightbulb text-primary mt-1"></i>
                        <p class="flex-1">${insight}</p>
                    </div>
                `).join('');
                html += '</div>';
                
                // Add show more button
                html += `
                    <button id="toggle-insights" class="w-full mt-2 py-2 px-4 bg-gray-800/50 text-primary hover:bg-gray-800 rounded-lg transition-all duration-300 flex items-center justify-center space-x-2">
                        <span>Show More</span>
                        <i class="fas fa-chevron-down transition-transform duration-300"></i>
                    </button>
                `;
            }
            
            html += '</div>';
            insightsContainer.innerHTML = html;
            
            // Add event listener for show more button
            const toggleBtn = document.getElementById('toggle-insights');
            const remainingDiv = document.getElementById('remaining-insights');
            
            if (toggleBtn && remainingDiv) {
                toggleBtn.addEventListener('click', () => {
                    const isHidden = remainingDiv.classList.contains('hidden');
                    const btnText = toggleBtn.querySelector('span');
                    const btnIcon = toggleBtn.querySelector('i');
                    
                    if (isHidden) {
                        remainingDiv.classList.remove('hidden');
                        btnText.textContent = 'Show Less';
                        btnIcon.style.transform = 'rotate(180deg)';
                        remainingDiv.style.animation = 'fadeIn 0.5s ease-out';
                    } else {
                        remainingDiv.classList.add('hidden');
                        btnText.textContent = 'Show More';
                        btnIcon.style.transform = '';
                        // Scroll back to top of insights
                        insightsContainer.scrollIntoView({ behavior: 'smooth' });
                    }
                });
            }
        } else {
            throw new Error('No insights available');
        }
    } catch (error) {
        console.error('Error loading insights:', error);
        insightsContainer.innerHTML = `
            <div class="flex items-start space-x-2 insight-item text-red-400 p-4 bg-gray-800/50 rounded-lg">
                <i class="fas fa-exclamation-circle mt-1"></i>
                <p class="flex-1">Failed to load insights. Please try again later.</p>
            </div>
        `;
    }
}

// Image extraction function
async function extractImages(url) {
    try {
        const response = await fetch('/api/ai/generate-content2', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-KEY': getApiKey()  // Get API key from storage/session
            },
            body: JSON.stringify({ 
                url,
                language: 'en'  // Default to English
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data.scraping.images || [];
    } catch (error) {
        console.error('Error extracting images:', error);
        showToast('Error extracting images. Please try again.', 'error');
        return [];
    }
}

// Helper function to get API key
function getApiKey() {
    return localStorage.getItem('api_key') || sessionStorage.getItem('api_key');
}

// Show toast message
function showToast(message, type = 'info') {
    // Implementation depends on your toast library
    if (window.ToastService) {
        window.ToastService.show(message, type);
    } else {
        console.log(message);
    }
} 