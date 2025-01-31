// services/index.js - Core services bundle

// AnimationService - Handles all animation-related functionality
class AnimationService {
    static fadeIn(element, duration = 500) {
        element.style.opacity = 0;
        element.style.display = 'block';
        
        let start = null;
        function animate(currentTime) {
            if (!start) start = currentTime;
            const progress = currentTime - start;
            element.style.opacity = Math.min(progress / duration, 1);
            if (progress < duration) {
                requestAnimationFrame(animate);
            }
        }
        requestAnimationFrame(animate);
    }
    
    static fadeOut(element, duration = 500) {
        let start = null;
        function animate(currentTime) {
            if (!start) start = currentTime;
            const progress = currentTime - start;
            element.style.opacity = 1 - Math.min(progress / duration, 1);
            if (progress < duration) {
                requestAnimationFrame(animate);
            } else {
                element.style.display = 'none';
            }
        }
        requestAnimationFrame(animate);
    }

    static animateValue(element, start, end, duration) {
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

    static initializeStatsAnimations() {
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

        document.querySelectorAll('.stat-value').forEach(stat => {
            const value = parseInt(stat.dataset.value || stat.textContent);
            stat.textContent = '0';
            this.animateValue(stat, 0, value, 1000);
        });
    }
}

// APIService - Handles all API-related functionality
class APIService {
    static headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    };

    static getApiKey() {
        return document.querySelector('meta[name="api-key"]')?.content || null;
    }

    static async generateContent(url, language = 'en') {
        try {
            const apiKey = this.getApiKey();
            if (apiKey) {
                this.headers['X-API-KEY'] = apiKey;
            }

            // Validate URL
            if (!url) {
                throw new Error('URL is required');
            }

            // Validate language
            const supportedLanguages = ['en', 'el', 'pl'];
            if (!supportedLanguages.includes(language)) {
                throw new Error('Unsupported language. Please use: en, el, or pl');
            }

            // Add protocol if missing
            if (!url.startsWith('http://') && !url.startsWith('https://')) {
                url = 'https://' + url;
            }

            const response = await fetch('/api/ai/generate-content2', {
                method: 'POST',
                headers: this.headers,
                body: JSON.stringify({ url, language })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error generating content:', error);
            throw error;
        }
    }

    static async detectPlatform(url) {
        try {
            const data = await this.generateContent(url);
            return data.analysis.platform_detection || { platform: 'unknown', confidence: 0 };
        } catch (error) {
            console.error('Error detecting platform:', error);
            return { platform: 'unknown', confidence: 0 };
        }
    }

    static async extractProductImages(url) {
        try {
            const data = await this.generateContent(url);
            return {
                images: data.scraping.images || [],
                productImages: data.analysis.product_images || []
            };
        } catch (error) {
            console.error('Error extracting images:', error);
            return { images: [], productImages: [] };
        }
    }

    static async loadAIInsights() {
        try {
            const response = await fetch('/ai-insights');
            if (!response.ok) {
                throw new Error('Failed to fetch AI insights');
            }
            return await response.json();
        } catch (error) {
            console.error('Error loading AI insights:', error);
            throw error;
        }
    }
}

// ToastService - Handles all notification functionality
class ToastService {
    static container;
    static toasts = new Map();
    static counter = 0;

    static init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'fixed bottom-4 right-4 z-50 space-y-4';
            document.body.appendChild(this.container);
        }
    }

    static show(message, type = 'info', options = {}) {
        this.init();
        const id = ++this.counter;
        const toast = document.createElement('div');
        
        const baseClasses = 'flex items-center p-4 rounded-lg shadow-lg transform transition-all duration-300 max-w-md';
        const typeClasses = {
            success: 'bg-green-600 text-white',
            error: 'bg-red-600 text-white',
            info: 'bg-blue-600 text-white',
            warning: 'bg-yellow-600 text-white'
        };
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            info: 'fas fa-info-circle',
            warning: 'fas fa-exclamation-triangle'
        };

        toast.className = `${baseClasses} ${typeClasses[type]}`;
        toast.innerHTML = `
            <i class="${icons[type]} mr-3"></i>
            <p class="flex-1">${message}</p>
            ${!options.autoClose ? `
                <button class="ml-4 hover:text-gray-200 focus:outline-none">
                    <i class="fas fa-times"></i>
                </button>
            ` : ''}
        `;

        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        this.container.appendChild(toast);
        
        setTimeout(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateY(0)';
        }, 10);

        this.toasts.set(id, toast);

        const closeBtn = toast.querySelector('button');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.dismiss(id));
        }

        if (options.autoClose !== false) {
            setTimeout(() => this.dismiss(id), options.duration || 3000);
        }

        return id;
    }

    static success(message, options = {}) {
        return this.show(message, 'success', options);
    }

    static error(message, options = {}) {
        return this.show(message, 'error', options);
    }

    static info(message, options = {}) {
        return this.show(message, 'info', options);
    }

    static warning(message, options = {}) {
        return this.show(message, 'warning', options);
    }

    static dismiss(id) {
        const toast = this.toasts.get(id);
        if (toast) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                toast.remove();
                this.toasts.delete(id);
            }, 300);
        }
    }
}

// LoadingMessageService - Handles loading message rotation
class LoadingMessageService {
    static messages = [
        "🔍 Analyzing product details...",
        "🤖 Implementing AI magic...",
        "✨ Crafting engaging content...",
        "📝 Generating product descriptions...",
        "🎨 Designing the perfect template...",
        "💫 Optimizing for your audience...",
        "🌟 Adding that special touch...",
        "🚀 Preparing for launch..."
    ];

    constructor(elementId) {
        this.element = document.getElementById(elementId);
        this.currentIndex = 0;
        this.interval = null;
    }

    start() {
        if (!this.element) return;
        
        // Set initial message
        this.element.textContent = LoadingMessageService.messages[0];
        
        // Start rotation
        this.interval = setInterval(() => {
            this.currentIndex = (this.currentIndex + 1) % LoadingMessageService.messages.length;
            
            // Fade out
            this.element.style.opacity = '0';
            
            setTimeout(() => {
                // Update text
                this.element.textContent = LoadingMessageService.messages[this.currentIndex];
                // Fade in
                this.element.style.opacity = '1';
            }, 200);
            
        }, 3000);
    }

    stop() {
        if (this.interval) {
            clearInterval(this.interval);
            this.interval = null;
        }
    }
}

// Export services for global use
window.AnimationService = AnimationService;
window.APIService = APIService;
window.ToastService = ToastService;
window.LoadingMessageService = LoadingMessageService; 
