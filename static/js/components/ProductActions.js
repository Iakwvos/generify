// ProductActions.js - Handles all product-related actions
class ProductActions {
    constructor() {
        this.loadingModal = null;
        this.messageRotator = null;
        this.createModal = document.getElementById('createProductModal');
        this.initializeHeaders();
        this.bindEvents();
    }

    initializeHeaders() {
        const apiKey = this.getApiKey();
        if (!apiKey) {
            console.warn('No API key found. Some features may not work correctly.');
        }

        this.headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        };

        if (apiKey) {
            this.headers['X-API-KEY'] = apiKey;
        }
    }

    getApiKey() {
        try {
            // Try localStorage first
            const localKey = localStorage.getItem('api_key');
            if (localKey) return localKey;

            // Try sessionStorage next
            const sessionKey = sessionStorage.getItem('api_key');
            if (sessionKey) return sessionKey;

            // If no key is found, return null
            return null;
        } catch (error) {
            console.error('Error accessing storage:', error);
            return null;
        }
    }

    bindEvents() {
        // Bind create product modal events
        const createBtn = document.querySelector('.create-product-btn');
        
        if (this.createModal) {
            const closeButtons = this.createModal.querySelectorAll('.close-modal');
            const form = document.getElementById('createProductForm');

            if (createBtn) {
                createBtn.addEventListener('click', () => {
                    this.createModal.classList.remove('hidden');
                });
            }

            closeButtons.forEach(button => {
                button.addEventListener('click', () => {
                    this.createModal.classList.add('hidden');
                });
            });

            if (form) {
                form.addEventListener('submit', this.handleCreateProduct.bind(this));
            }
        }
    }

    showLoadingModal(message = 'Creating your product...') {
        this.loadingModal = document.createElement('div');
        this.loadingModal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        this.loadingModal.innerHTML = `
            <div class="bg-gray-800 p-8 rounded-lg shadow-xl max-w-md w-full">
                <div class="flex flex-col items-center">
                    <div class="loading mb-4"></div>
                    <p id="loading-status" class="text-white text-center mb-4">${message}</p>
                    <div class="w-full bg-gray-700 rounded-full h-2 mb-2">
                        <div id="loading-progress" class="bg-primary h-2 rounded-full transition-all duration-300" style="width: 0%"></div>
                    </div>
                    <p id="loading-percent" class="text-sm text-gray-400">0%</p>
                </div>
            </div>
        `;
        document.body.appendChild(this.loadingModal);
        
        // Initialize progress animation
        this.initializeProgressBar();
        
        // Initialize message rotator
        this.messageRotator = new LoadingMessageRotator('loading-status');
        this.messageRotator.start();
    }

    initializeProgressBar() {
        const progressBar = this.loadingModal.querySelector('#loading-progress');
        const percentText = this.loadingModal.querySelector('#loading-percent');
        
        // Configuration
        const duration = Math.random() * 5000 + 20000; // Random duration between 20-25 seconds
        const startTime = Date.now();
        const fps = 30; // Update 30 times per second
        const interval = 1000 / fps;
        
        // Progress state
        let currentProgress = 0;
        let targetProgress = 0;
        let lastUpdate = 0;
        
        // Easing function for smooth progress
        const easeOutQuad = t => t * (2 - t);
        
        const updateProgress = () => {
            if (!this.loadingModal) return; // Stop if modal is closed
            
            const currentTime = Date.now();
            const elapsed = currentTime - startTime;
            
            // Only update if enough time has passed
            if (currentTime - lastUpdate >= interval) {
                // Calculate target progress (0-1)
                targetProgress = Math.min(elapsed / duration, 0.99);
                
                // Apply easing
                const easedProgress = easeOutQuad(targetProgress);
                
                // Smoothly interpolate current progress towards target
                const delta = easedProgress - currentProgress;
                currentProgress += delta * 0.1; // Smooth lerp factor
                
                // Apply a subtle random variation (much smaller than before)
                const randomFactor = 1 + (Math.random() * 0.02 - 0.01); // ±1% variation
                const displayProgress = Math.min(currentProgress * randomFactor * 100, 99);
                
                // Update DOM
                progressBar.style.width = `${displayProgress}%`;
                percentText.textContent = `${Math.round(displayProgress)}%`;
                
                lastUpdate = currentTime;
            }
            
            if (currentProgress < 0.99) {
                requestAnimationFrame(updateProgress);
            }
        };
        
        requestAnimationFrame(updateProgress);
    }

    hideLoadingModal() {
        if (this.messageRotator) {
            this.messageRotator.stop();
            this.messageRotator = null;
        }
        if (this.loadingModal && this.loadingModal.parentNode) {
            // Show 100% briefly before closing
            const progressBar = this.loadingModal.querySelector('#loading-progress');
            const percentText = this.loadingModal.querySelector('#loading-percent');
            if (progressBar && percentText) {
                progressBar.style.width = '100%';
                percentText.textContent = '100%';
                
                // Small delay before closing to show 100%
                setTimeout(() => {
                    this.loadingModal.remove();
                    this.loadingModal = null;
                }, 200);
            } else {
                this.loadingModal.remove();
                this.loadingModal = null;
            }
        }
    }

    async handleCreateProduct(e) {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);
        const toastId = ToastService.info('Creating product...', { autoClose: false });
        let responseTime = null;

        try {
            this.showLoadingModal();

            const url = formData.get('url');
            if (url) {
                // Generate content and analyze URL
                const contentResponse = await fetch('/api/ai/generate-content2', {
                    method: 'POST',
                    headers: this.headers,
                    body: JSON.stringify({ 
                        url: formData.get('url'), 
                        language: formData.get('language') 
                    })
                });

                if (!contentResponse.ok) {
                    throw new Error('Failed to generate content and analyze URL');
                }

                const analysisData = await contentResponse.json();
                responseTime = analysisData.metrics.response_time;

                // Check if no product images were found
                if (!analysisData.analysis.product_images || analysisData.analysis.product_images.length === 0) {
                    this.hideLoadingModal();
                    const shouldContinue = await this.showNoImagesWarning();
                    if (!shouldContinue) {
                        ToastService.dismiss(toastId);
                        return;
                    }
                    this.showLoadingModal();
                }

                // Create product with AI-analyzed product images
                const productResponse = await fetch('/api/products/', {
                    method: 'POST',
                    headers: this.headers,
                    body: JSON.stringify({
                        title: formData.get('title'),
                        price: parseFloat(formData.get('price')),
                        status: 'active',
                        url: formData.get('url'),
                        language: formData.get('language'),
                        images: analysisData.analysis.product_images.map(url => ({
                            src: url.startsWith('//') ? `https:${url}` : url,
                            alt: '', // Product images are pre-filtered by AI
                            width: '', // Dimensions not needed for product images
                            height: ''
                        }))
                    })
                });

                if (!productResponse.ok) {
                    const errorData = await productResponse.json();
                    throw new Error(errorData.error || 'Failed to create product');
                }

                const productData = await productResponse.json();

                // Create template with AI-generated content
                const templateResponse = await fetch('/api/templates/create', {
                    method: 'POST',
                    headers: this.headers,
                    body: JSON.stringify({
                        source: 'product.template.json',
                        content: analysisData.analysis.content,
                        images: productData.images.map(img => ({
                            src: img.src,
                            alt: img.alt || '',
                            width: img.width || '',
                            height: img.height || ''
                        }))
                    })
                });

                if (!templateResponse.ok) {
                    throw new Error('Failed to create template');
                }

                const templateData = await templateResponse.json();

                // Update product with template suffix
                const updateResponse = await fetch(`/api/products/${productData.id}`, {
                    method: 'PATCH',
                    headers: this.headers,
                    body: JSON.stringify({
                        template_suffix: templateData.template_suffix
                    })
                });

                if (!updateResponse.ok) {
                    const errorData = await updateResponse.json();
                    throw new Error(errorData.message || 'Failed to update product template');
                }

                // Show congratulatory modal after successful creation
                if (responseTime) {
                    this.showCongratulateModal(responseTime);
                }
            } else {
                // Create product without reference URL
                const productResponse = await fetch('/api/products/create', {
                    method: 'POST',
                    headers: this.headers,
                    body: JSON.stringify({
                        title: formData.get('title'),
                        status: 'active'
                    })
                });

                if (!productResponse.ok) {
                    const errorData = await productResponse.json();
                    throw new Error(errorData.error || 'Failed to create product');
                }
            }

            ToastService.success('Product created successfully');
            if (this.createModal) {
                this.createModal.classList.add('hidden');
                form.reset();
            }
            if (window.productGrid) {
                await window.productGrid.updateGrid();
            }

        } catch (error) {
            console.error('Error:', error);
            ToastService.error(error.message || 'An error occurred while creating the product');
        } finally {
            this.hideLoadingModal();
            ToastService.dismiss(toastId);
            if (this.createModal) {
                this.createModal.classList.add('hidden');
                form.reset();
            }
        }
    }

    showPlatformWarning() {
        return new Promise((resolve) => {
            const warningModal = document.createElement('div');
            warningModal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
            warningModal.innerHTML = `
                <div class="bg-gray-800 p-8 rounded-lg shadow-xl max-w-md w-full">
                    <div class="flex flex-col items-center">
                        <div class="text-yellow-400 text-5xl mb-4">⚠️</div>
                        <h3 class="text-white text-xl font-semibold mb-4">Platform Warning</h3>
                        <p class="text-gray-300 text-center mb-6">
                            The provided URL does not appear to be a WordPress or Shopify site. 
                            Image extraction may not be accurate and manual review is highly recommended.
                        </p>
                        <div class="flex space-x-4 w-full">
                            <button class="flex-1 py-2 px-4 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors duration-200" id="cancelBtn">
                                Cancel
                            </button>
                            <button class="flex-1 py-2 px-4 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg transition-colors duration-200" id="continueBtn">
                                Continue Anyway
                            </button>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(warningModal);

            warningModal.querySelector('#cancelBtn').addEventListener('click', () => {
                warningModal.remove();
                resolve(false);
            });

            warningModal.querySelector('#continueBtn').addEventListener('click', () => {
                warningModal.remove();
                resolve(true);
            });
        });
    }

    showNoImagesWarning() {
        return new Promise((resolve) => {
            const warningModal = document.createElement('div');
            warningModal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
            warningModal.innerHTML = `
                <div class="bg-gray-800 p-8 rounded-lg shadow-xl max-w-md w-full">
                    <div class="flex flex-col items-center">
                        <div class="text-yellow-400 text-5xl mb-4">⚠️</div>
                        <h3 class="text-white text-xl font-semibold mb-4">No Images Found</h3>
                        <p class="text-gray-300 text-center mb-6">
                            No product images could be extracted from the provided URL. 
                            The product will be created without images. Would you like to continue?
                        </p>
                        <div class="flex space-x-4 w-full">
                            <button class="flex-1 py-2 px-4 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors duration-200" id="cancelBtn">
                                Cancel
                            </button>
                            <button class="flex-1 py-2 px-4 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg transition-colors duration-200" id="continueBtn">
                                Continue Without Images
                            </button>
                        </div>
                    </div>
                </div>
            `;
            document.body.appendChild(warningModal);

            warningModal.querySelector('#cancelBtn').addEventListener('click', () => {
                warningModal.remove();
                resolve(false);
            });

            warningModal.querySelector('#continueBtn').addEventListener('click', () => {
                warningModal.remove();
                resolve(true);
            });
        });
    }

    async duplicate(productId) {
        const toastId = ToastService.info('Duplicating product...', { autoClose: false });
        
        try {
            const response = await fetch(`/api/products/${productId}`, {
                method: 'POST',
                headers: this.headers
            });
            
            if (response.ok) {
                const data = await response.json();
                ToastService.success('Product duplicated successfully');
                if (window.productGrid) {
                    await window.productGrid.updateGrid();
                }
            } else {
                const data = await response.json();
                ToastService.error(data.error || 'Failed to duplicate product');
            }
        } catch (error) {
            console.error('Error:', error);
            ToastService.error('An error occurred while duplicating the product');
        } finally {
            ToastService.dismiss(toastId);
        }
    }

    showDeleteModal(productId) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-gray-800 border border-gray-700 p-6 rounded-lg w-full max-w-md">
                <h3 class="text-xl font-bold text-white mb-4">Delete Product</h3>
                <p class="text-gray-300 mb-6">Are you sure you want to delete this product? This action cannot be undone.</p>
                <div class="flex justify-end space-x-4">
                    <button class="cancel-delete py-2 px-4 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors duration-200">
                        Cancel
                    </button>
                    <button class="confirm-delete py-2 px-4 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors duration-200">
                        Delete
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        const cancelBtn = modal.querySelector('.cancel-delete');
        const confirmBtn = modal.querySelector('.confirm-delete');

        cancelBtn.addEventListener('click', () => {
            modal.remove();
        });

        confirmBtn.addEventListener('click', () => {
            this.confirmDelete(productId, modal);
        });
    }

    async confirmDelete(productId, modal) {
        const toastId = ToastService.info('Deleting product...', { autoClose: false });
        
        try {
            const response = await fetch(`/api/products/${productId}`, {
                method: 'DELETE',
                headers: this.headers
            });
            
            if (response.ok) {
                ToastService.success('Product deleted successfully');
                modal.remove();
                if (window.productGrid) {
                    await window.productGrid.updateGrid();
                }
            } else {
                const data = await response.json();
                ToastService.error(data.error || 'Failed to delete product');
            }
        } catch (error) {
            console.error('Error:', error);
            ToastService.error('An error occurred while deleting the product');
        } finally {
            ToastService.dismiss(toastId);
        }
    }

    edit(handle) {
        const url = `https://admin.shopify.com/store/${window.config.SHOP_URL.split('.')[0]}/themes/${window.config.active_theme_id}/editor?previewPath=/products/${handle}`;
        window.open(url, '_blank');
    }

    showCongratulateModal(responseTime) {
        const manualTime = 3 * 60 * 60; // 3 hours in seconds
        const timesFaster = Math.round((manualTime / responseTime) * 100) / 100; // Round to 2 decimal places
        
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-gray-800 p-8 rounded-lg shadow-xl max-w-2xl w-full mx-4">
                <div class="flex flex-col items-center">
                    <div class="text-green-400 text-6xl mb-6">🎉</div>
                    <h3 class="text-white text-2xl font-semibold mb-6">Congratulations!</h3>
                    <p class="text-gray-300 text-center text-lg mb-8">
                        The creation of your product took <span class="text-primary font-semibold">${responseTime.toFixed(2)} seconds</span>.<br>
                        <span class="text-sm text-gray-400 mt-2 block">Average manual creation time: 3 hours</span>
                        <span class="text-primary font-semibold text-xl mt-4 block">
                            That's ${timesFaster.toFixed(2)}x faster than manual creation!
                        </span>
                    </p>
                    <div class="flex space-x-6 w-full max-w-md">
                        <button class="continue-btn flex-1 py-3 px-6 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors duration-200 text-lg">
                            Continue
                        </button>
                        <button class="new-product-btn flex-1 py-3 px-6 bg-primary hover:bg-primary/80 text-white rounded-lg transition-colors duration-200 text-lg">
                            Create New Product
                        </button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        // Handle continue button click
        modal.querySelector('.continue-btn').addEventListener('click', async () => {
            modal.remove();
            if (window.productGrid) {
                await window.productGrid.updateGrid();
            }
        });

        // Handle create new product button click
        modal.querySelector('.new-product-btn').addEventListener('click', async () => {
            modal.remove();
            if (window.productGrid) {
                await window.productGrid.updateGrid();
            }
            if (this.createModal) {
                this.createModal.classList.remove('hidden');
            }
        });
    }
}

// Make ProductActions globally available
window.ProductActions = ProductActions;

// Initialize ProductActions when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.productActions = new ProductActions();
});

async function detectPlatform(url) {
    try {
        const response = await fetch('/api/ai/generate-content2', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-KEY': getApiKey()
            },
            body: JSON.stringify({ 
                url,
                language: 'en'
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data.analysis.platform_detection || { platform: 'unknown', confidence: 0 };
    } catch (error) {
        console.error('Error detecting platform:', error);
        return { platform: 'unknown', confidence: 0 };
    }
}

async function extractProductImages(url) {
    try {
        const response = await fetch('/api/ai/generate-content2', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-KEY': getApiKey()
            },
            body: JSON.stringify({ 
                url,
                language: 'en'
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return {
            images: data.scraping.images || [],
            productImages: data.analysis.product_images || []
        };
    } catch (error) {
        console.error('Error extracting images:', error);
        return { images: [], productImages: [] };
    }
} 