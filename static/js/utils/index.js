// Utility Functions Bundle

// Additional Helper Functions
const HelperUtils = {
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    generateId: () => {
        return Math.random().toString(36).substring(2) + Date.now().toString(36);
    },

    deepClone: (obj) => {
        return JSON.parse(JSON.stringify(obj));
    },

    truncateText: (text, maxLength = 100) => {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    },

    formDataToObject: (formData) => {
        const object = {};
        formData.forEach((value, key) => {
            if (object[key] !== undefined) {
                if (!Array.isArray(object[key])) {
                    object[key] = [object[key]];
                }
                object[key].push(value);
            } else {
                object[key] = value;
            }
        });
        return object;
    },

    retry: async (fn, retries = 3, delay = 1000) => {
        try {
            return await fn();
        } catch (error) {
            if (retries === 0) throw error;
            await new Promise(resolve => setTimeout(resolve, delay));
            return HelperUtils.retry(fn, retries - 1, delay);
        }
    }
};

// Error Handling
class ApiError extends Error {
    constructor(message, status, data) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.data = data;
    }
}

const ErrorUtils = {
    handleApiError: async (error) => {
        console.error('API Error:', error);
        
        if (error instanceof ApiError) {
            ToastService.error(`API Error: ${error.message}`);
            return;
        }

        if (error.name === 'TypeError' && !navigator.onLine) {
            ToastService.error('Network Error: Please check your internet connection');
            return;
        }

        ToastService.error('An unexpected error occurred. Please try again later.');
    },

    validateResponse: async (response) => {
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new ApiError(
                data.error || `HTTP error! status: ${response.status}`,
                response.status,
                data
            );
        }
        return response;
    }
};

// Type Checking
const TypeUtils = {
    isValidUrl: (string) => {
        try {
            new URL(string);
            return true;
        } catch {
            return false;
        }
    },

    isValidPrice: (number) => {
        return !isNaN(number) && 
               parseFloat(number) >= 0 && 
               /^\d+(\.\d{0,2})?$/.test(number.toString());
    },

    isValidProductData: (data) => {
        const required = ['title', 'status'];
        const hasRequired = required.every(field => 
            Object.prototype.hasOwnProperty.call(data, field) && 
            data[field] !== null && 
            data[field] !== undefined
        );

        if (!hasRequired) {
            throw new Error('Missing required product fields');
        }

        if (data.price && !TypeUtils.isValidPrice(data.price)) {
            throw new Error('Invalid price format');
        }

        if (data.url && !TypeUtils.isValidUrl(data.url)) {
            throw new Error('Invalid URL format');
        }

        return true;
    }
};

// Performance Monitoring
const PerformanceUtils = {
    metrics: {},

    measureApiCall: async (name, promise) => {
        const start = performance.now();
        try {
            const result = await promise;
            const duration = performance.now() - start;
            PerformanceUtils.logPerformanceMetric(name, duration);
            return result;
        } catch (error) {
            const duration = performance.now() - start;
            PerformanceUtils.logPerformanceMetric(`${name}_error`, duration);
            throw error;
        }
    },

    logPerformanceMetric: (name, duration) => {
        if (!PerformanceUtils.metrics[name]) {
            PerformanceUtils.metrics[name] = {
                count: 0,
                total: 0,
                min: Infinity,
                max: -Infinity
            };
        }

        const metric = PerformanceUtils.metrics[name];
        metric.count++;
        metric.total += duration;
        metric.min = Math.min(metric.min, duration);
        metric.max = Math.max(metric.max, duration);

        // Log to console in development
        if (process.env.NODE_ENV === 'development') {
            console.log(`Performance metric - ${name}:`, {
                duration: `${duration.toFixed(2)}ms`,
                average: `${(metric.total / metric.count).toFixed(2)}ms`,
                min: `${metric.min.toFixed(2)}ms`,
                max: `${metric.max.toFixed(2)}ms`,
                count: metric.count
            });
        }
    }
};

// DOM Utilities
const DOMUtils = {
    createElement: (tag, props = {}) => {
        const element = document.createElement(tag);
        Object.entries(props).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'dataset') {
                Object.entries(value).forEach(([dataKey, dataValue]) => {
                    element.dataset[dataKey] = dataValue;
                });
            } else if (key === 'style' && typeof value === 'object') {
                Object.assign(element.style, value);
            } else if (key === 'text') {
                element.textContent = value;
            } else if (key === 'html') {
                element.innerHTML = value;
            } else if (key.startsWith('on') && typeof value === 'function') {
                element.addEventListener(key.slice(2).toLowerCase(), value);
            } else {
                element.setAttribute(key, value);
            }
        });
        return element;
    },

    appendChildren: (parent, ...children) => {
        children.forEach(child => {
            if (typeof child === 'string') {
                parent.appendChild(document.createTextNode(child));
            } else if (child instanceof Node) {
                parent.appendChild(child);
            }
        });
        return parent;
    },

    removeElement: (element) => {
        if (element && element.parentNode) {
            element.parentNode.removeChild(element);
            return true;
        }
        return false;
    }
};

// Data Formatting
const FormatUtils = {
    formatPrice: (number, currency = 'USD') => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(number);
    },

    formatDate: (date, format = 'medium') => {
        const d = date instanceof Date ? date : new Date(date);
        return new Intl.DateTimeFormat('en-US', {
            dateStyle: format,
            timeStyle: format
        }).format(d);
    },

    slugify: (string) => {
        return string
            .toLowerCase()
            .replace(/[^\w\s-]/g, '')
            .replace(/[\s_-]+/g, '-')
            .replace(/^-+|-+$/g, '');
    }
};

// Export utilities for global use
window.ErrorUtils = ErrorUtils;
window.TypeUtils = TypeUtils;
window.PerformanceUtils = PerformanceUtils;
window.DOMUtils = DOMUtils;
window.FormatUtils = FormatUtils;
window.HelperUtils = HelperUtils; 