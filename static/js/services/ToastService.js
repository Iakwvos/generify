// ToastService.js - Handles toast notifications
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
        
        // Base classes for all toasts
        const baseClasses = 'flex items-center p-4 rounded-lg shadow-lg transform transition-all duration-300 max-w-md';
        
        // Type-specific classes
        const typeClasses = {
            success: 'bg-green-600 text-white',
            error: 'bg-red-600 text-white',
            info: 'bg-blue-600 text-white',
            warning: 'bg-yellow-600 text-white'
        };

        // Icon based on type
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

        // Add to container with animation
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        this.container.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => {
            toast.style.opacity = '1';
            toast.style.transform = 'translateY(0)';
        }, 10);

        this.toasts.set(id, toast);

        // Add click handler for close button
        const closeBtn = toast.querySelector('button');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.dismiss(id));
        }

        // Auto dismiss after delay if autoClose is true
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
            // Animate out
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(20px)';
            
            // Remove after animation
            setTimeout(() => {
                toast.remove();
                this.toasts.delete(id);
            }, 300);
        }
    }
}

// Make it globally available
window.ToastService = ToastService; 