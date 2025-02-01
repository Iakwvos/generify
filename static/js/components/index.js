// components/index.js - Core UI components bundle

// Base Modal Component
class ModalComponent {
    constructor(modalId) {
        this.modal = document.getElementById(modalId);
        this.boundHandleEscape = this.handleEscape.bind(this);
    }

    show() {
        if (!this.modal) return;
        this.modal.classList.remove('hidden');
        document.addEventListener('keydown', this.boundHandleEscape);
        document.body.classList.add('modal-open');
    }

    hide() {
        if (!this.modal) return;
        this.modal.classList.add('hidden');
        document.removeEventListener('keydown', this.boundHandleEscape);
        document.body.classList.remove('modal-open');
    }

    handleEscape(event) {
        if (event.key === 'Escape') {
            this.hide();
        }
    }
}

// Loading Modal Component
class LoadingModal extends ModalComponent {
    constructor() {
        super('loadingModal');
        this.messageRotator = null;
        this.progressInterval = null;
    }

    show(message = 'Loading...') {
        // Create modal if it doesn't exist
        if (!this.modal) {
            this.modal = document.createElement('div');
            this.modal.id = 'loadingModal';
            this.modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 opacity-0 transition-opacity duration-300';
            document.body.appendChild(this.modal);
        }

        this.modal.innerHTML = `
            <div class="bg-gray-800 p-8 rounded-lg shadow-xl max-w-md w-full mx-4 transform transition-all duration-300 scale-95 opacity-0">
                <div class="flex flex-col items-center">
                    <div class="loading mb-4"></div>
                    <p id="loading-status" class="text-white text-center mb-4">${message}</p>
                    <div class="w-full bg-gray-700 rounded-full h-2 mb-2">
                        <div id="loading-progress" 
                             class="bg-primary h-2 rounded-full transition-all duration-300"
                             style="width: 0%">
                        </div>
                    </div>
                    <p id="loading-percent" class="text-sm text-gray-400">0%</p>
                </div>
            </div>
        `;

        // Show with animation
        requestAnimationFrame(() => {
            this.modal.classList.remove('opacity-0');
            const content = this.modal.querySelector('.bg-gray-800');
            if (content) {
                content.classList.remove('scale-95', 'opacity-0');
            }
        });

        // Initialize progress animation
        this.initializeProgressBar();
        
        // Initialize message rotator
        this.messageRotator = new LoadingMessageService('loading-status');
        this.messageRotator.start();

        super.show();
    }

    hide() {
        if (this.messageRotator) {
            this.messageRotator.stop();
            this.messageRotator = null;
        }

        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }

        // Hide with animation
        if (this.modal) {
            const content = this.modal.querySelector('.bg-gray-800');
            if (content) {
                content.classList.add('scale-95', 'opacity-0');
            }
            this.modal.classList.add('opacity-0');

            // Remove after animation
            setTimeout(() => {
                super.hide();
                this.modal.remove();
                this.modal = null;
            }, 300);
        }
    }

    startTimer() {
        const timeElement = this.modal.querySelector('#loading-time');
        const startTime = Date.now();
        
        this.progressInterval = setInterval(() => {
            if (!this.modal) {
                clearInterval(this.progressInterval);
                return;
            }

            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            timeElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    initializeProgressBar() {
        const progressBar = this.modal.querySelector('#loading-progress');
        const percentText = this.modal.querySelector('#loading-percent');
        
        const duration = Math.random() * 5000 + 15000; // Random duration between 15-20 seconds
        const startTime = Date.now();
        const fps = 30;
        const interval = 1000 / fps;
        
        let currentProgress = 0;
        let targetProgress = 0;
        let lastUpdate = 0;
        
        const easeOutQuad = t => t * (2 - t);
        
        const updateProgress = () => {
            if (!this.modal) return;
            
            const currentTime = Date.now();
            const elapsed = currentTime - startTime;
            
            if (currentTime - lastUpdate >= interval) {
                targetProgress = Math.min(elapsed / duration, 0.99);
                const easedProgress = easeOutQuad(targetProgress);
                const delta = easedProgress - currentProgress;
                currentProgress += delta * 0.1;
                
                const randomFactor = 1 + (Math.random() * 0.01 - 0.005); // Reduced randomness
                const displayProgress = Math.min(currentProgress * randomFactor * 100, 99);
                
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
}

// Product Form Component
class ProductForm extends ModalComponent {
    constructor() {
        super('createProductModal');
        this.form = document.getElementById('createProductForm');
        this.loadingModal = new LoadingModal();
        this.warningModal = new WarningModal();
        this.bindEvents();
    }

    bindEvents() {
        if (this.modal) {
            const closeXButton = this.modal.querySelector('.modal-close-x');
            const closeCancelButton = this.modal.querySelector('.modal-close-cancel');

            if (closeXButton) {
                closeXButton.addEventListener('click', () => this.hide());
            }

            if (closeCancelButton) {
                closeCancelButton.addEventListener('click', () => this.hide());
            }

            this.modal.addEventListener('click', (e) => {
                if (e.target === this.modal) {
                    this.hide();
                }
            });

            if (this.form) {
                this.form.addEventListener('submit', this.handleSubmit.bind(this));
            }
        }
    }

    async handleSubmit(e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const toastId = ToastService.info('Creating product...', { autoClose: false });
        let responseTime = null;

        try {
            this.loadingModal.show('Creating your product...');

            const url = formData.get('url');
            if (url) {
                // Generate content and analyze URL
                const contentResponse = await APIService.generateContent(url, formData.get('language'));
                responseTime = contentResponse.metrics.response_time;

                // Check if no product images were found
                if (!contentResponse.analysis.product_images || contentResponse.analysis.product_images.length === 0) {
                    this.loadingModal.hide();
                    const shouldContinue = await this.warningModal.show({
                        title: 'No Images Found',
                        message: 'No product images could be extracted from the provided URL. The product will be created without images. Would you like to continue?',
                        confirmText: 'Continue Without Images',
                        cancelText: 'Cancel',
                        type: 'warning'
                    });
                    if (!shouldContinue) {
                        ToastService.dismiss(toastId);
                        return;
                    }
                    this.loadingModal.show('Creating your product...');
                }

                // Create product with AI-analyzed product images
                const productData = await this.createProductWithImages(formData, contentResponse);
                const templateData = await this.createTemplate(productData, contentResponse);
                await this.updateProductTemplate(productData.id, templateData.template_suffix);

                // Hide loading modal before showing congratulations
                await new Promise(resolve => {
                    this.loadingModal.hide();
                    // Wait for hide animation to complete
                    setTimeout(resolve, 300);
                });

                // Show congratulatory modal
                if (responseTime) {
                    this.showCongratulateModal(responseTime);
                }
            } else {
                // Create product without reference URL
                await this.createBasicProduct(formData);
            }

            ToastService.success('Product created successfully');
            this.hide();
            if (window.productGrid) {
                await window.productGrid.updateGrid();
            }

        } catch (error) {
            console.error('Error:', error);
            ToastService.error(error.message || 'An error occurred while creating the product');
        } finally {
            this.loadingModal.hide();
            ToastService.dismiss(toastId);
            this.hide();
        }
    }

    async createProductWithImages(formData, contentResponse) {
        const response = await fetch('/api/products/', {
            method: 'POST',
            headers: APIService.headers,
            body: JSON.stringify({
                title: formData.get('title'),
                price: parseFloat(formData.get('price')),
                status: 'active',
                url: formData.get('url'),
                language: formData.get('language'),
                images: contentResponse.analysis.product_images.map(url => ({
                    src: url.startsWith('//') ? `https:${url}` : url,
                    alt: '',
                    width: '',
                    height: ''
                }))
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to create product');
        }

        return await response.json();
    }

    async createTemplate(productData, contentResponse) {
        const response = await fetch('/api/templates/create', {
            method: 'POST',
            headers: APIService.headers,
            body: JSON.stringify({
                source: 'product.template.json',
                content: contentResponse.analysis.content,
                images: productData.images.map(img => ({
                    src: img.src,
                    alt: img.alt || '',
                    width: img.width || '',
                    height: img.height || ''
                }))
            })
        });

        if (!response.ok) {
            throw new Error('Failed to create template');
        }

        return await response.json();
    }

    async updateProductTemplate(productId, templateSuffix) {
        const response = await fetch(`/api/products/${productId}`, {
            method: 'PATCH',
            headers: APIService.headers,
            body: JSON.stringify({
                template_suffix: templateSuffix
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Failed to update product template');
        }
    }

    async createBasicProduct(formData) {
        const response = await fetch('/api/products/create', {
            method: 'POST',
            headers: APIService.headers,
            body: JSON.stringify({
                title: formData.get('title'),
                status: 'active'
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to create product');
        }
    }

    showCongratulateModal(responseTime) {
        const manualTime = 3 * 60 * 60; // 3 hours in seconds
        const timesFaster = Math.round((manualTime / responseTime) * 100) / 100;
        
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-gray-800 p-8 rounded-lg shadow-xl max-w-2xl w-full mx-4">
                <div class="flex flex-col items-center">
                    <div class="text-[#50B83C] text-6xl mb-6">🎉</div>
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

        // Handle continue button click - just close the modal
        modal.querySelector('.continue-btn').addEventListener('click', () => {
            modal.remove();
        });

        // Handle create new product button click - close modal and show form
        modal.querySelector('.new-product-btn').addEventListener('click', () => {
            modal.remove();
            this.show();
        });
    }
}

// Warning Modal Component
class WarningModal extends ModalComponent {
    constructor(options = {}) {
        super('warningModal');
        this.options = {
            title: options.title || 'Warning',
            message: options.message || '',
            confirmText: options.confirmText || 'Continue',
            cancelText: options.cancelText || 'Cancel',
            confirmClass: options.confirmClass || 'bg-yellow-600 hover:bg-yellow-700',
            type: options.type || 'warning'
        };
    }

    show() {
        return new Promise((resolve) => {
            // Create modal if it doesn't exist
            if (!this.modal) {
                this.modal = document.createElement('div');
                this.modal.id = 'warningModal';
                this.modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
                document.body.appendChild(this.modal);
            }

            // Set modal content
            this.modal.innerHTML = `
                <div class="bg-gray-800 p-8 rounded-lg shadow-xl max-w-md w-full mx-4">
                    <div class="flex flex-col items-center">
                        <div class="text-${this.options.type === 'warning' ? 'yellow' : 'red'}-400 text-5xl mb-4">
                            ${this.options.type === 'warning' ? '⚠️' : '🗑️'}
                        </div>
                        <h3 class="text-white text-xl font-semibold mb-4">${this.options.title}</h3>
                        <div class="text-gray-300 text-center mb-6">${this.options.message}</div>
                        <div class="flex space-x-4 w-full">
                            <button class="flex-1 py-3 px-4 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors duration-200 text-sm font-medium" id="cancelBtn">
                                ${this.options.cancelText}
                            </button>
                            <button class="flex-1 py-3 px-4 ${this.options.confirmClass} text-white rounded-lg transition-colors duration-200 text-sm font-medium" id="confirmBtn">
                                ${this.options.confirmText}
                            </button>
                        </div>
                    </div>
                </div>
            `;

            // Add click handlers
            const cancelBtn = this.modal.querySelector('#cancelBtn');
            const confirmBtn = this.modal.querySelector('#confirmBtn');
            const modalContent = this.modal.querySelector('.bg-gray-800');

            // Prevent clicks on modal content from closing the modal
            modalContent?.addEventListener('click', (e) => e.stopPropagation());

            // Close modal on background click
            this.modal.addEventListener('click', (e) => {
                if (e.target === this.modal) {
                    this.hide();
                    resolve(false);
                }
            });

            // Handle button clicks
            cancelBtn?.addEventListener('click', () => {
                this.hide();
                resolve(false);
            });

            confirmBtn?.addEventListener('click', () => {
                this.hide();
                resolve(true);
            });

            // Handle escape key
            const handleEscape = (e) => {
                if (e.key === 'Escape') {
                    this.hide();
                    resolve(false);
                    document.removeEventListener('keydown', handleEscape);
                }
            };
            document.addEventListener('keydown', handleEscape);

            // Show modal
            this.modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        });
    }

    hide() {
        if (this.modal) {
            this.modal.classList.add('hidden');
            document.body.style.overflow = '';
            
            // Remove modal after animation
            setTimeout(() => {
                this.modal.remove();
                this.modal = null;
            }, 300);
        }
    }
}

// ProductGrid Component
class ProductGrid {
    constructor() {
        this.container = document.querySelector('.products-grid');
        this.searchInput = document.getElementById('product-search');
        this.minPriceInput = document.getElementById('min-price');
        this.maxPriceInput = document.getElementById('max-price');
        this.templateFilter = document.getElementById('template-filter');
        this.warningModal = new WarningModal();
        
        // Bind events for existing cards
        if (this.container) {
            this.bindCardEvents();
            this.bindFilterEvents();
        }
    }

    async updateGrid() {
        try {
            console.log('🔄 Refreshing product grid...');
            const response = await fetch('/api/products');
            if (!response.ok) {
                throw new Error('Failed to fetch products');
            }
            const data = await response.json();
            
            // Log the raw data for debugging
            console.log('📦 Raw product data:', data);
            
            if (this.container) {
                // Ensure we have an array of products
                const products = Array.isArray(data) ? data : (data.products || []);
                console.log(`📊 Processing ${products.length} products`);
                
                // Update the grid with the products
                this.container.innerHTML = products.map((product, index) => {
                    console.log(`🏷️ Processing product ${index + 1}/${products.length}:`, product);
                    return this.renderProductCard(product);
                }).join('');
                
                this.bindCardEvents();
                console.log('✅ Grid refresh complete');
            }
        } catch (error) {
            console.error('❌ Error updating products grid:', error);
            ToastService.error('Failed to update products grid');
        }
    }

    bindCardEvents() {
        // Add event listeners to all product cards
        this.container.querySelectorAll('.product-card').forEach(card => {
            const productId = card.dataset.productId;
            const productHandle = card.dataset.productHandle;

            // Product handle link
            const handleLink = card.querySelector('.meta');
            if (handleLink) {
                handleLink.addEventListener('click', (e) => {
                    e.preventDefault();
                    window.open(`https://${window.config.SHOP_URL}/products/${productHandle}`, '_blank', 'noopener');
                });
            }

            // Preview button
            card.querySelector('.preview-btn')?.addEventListener('click', () => {
                window.open(`https://${window.config.SHOP_URL}/products/${productHandle}`, '_blank', 'noopener');
            });

            // Edit button
            card.querySelector('.edit-btn')?.addEventListener('click', () => {
                this.editProduct(productHandle);
            });

            // Duplicate button
            card.querySelector('.duplicate-btn')?.addEventListener('click', () => {
                this.duplicateProduct(productId);
            });

            // Delete button
            card.querySelector('.delete-btn')?.addEventListener('click', () => {
                this.deleteProduct(productId);
            });
        });
    }

    bindFilterEvents() {
        // Add event listeners for filters
        [this.searchInput, this.minPriceInput, this.maxPriceInput, this.templateFilter].forEach(input => {
            if (input) {
                input.addEventListener('input', () => this.filterProducts());
                input.addEventListener('change', () => this.filterProducts());
            }
        });
    }

    filterProducts() {
        const searchTerm = this.searchInput?.value.toLowerCase() || '';
        const minPrice = this.minPriceInput?.value ? parseFloat(this.minPriceInput.value) : 0;
        const maxPrice = this.maxPriceInput?.value ? parseFloat(this.maxPriceInput.value) : Infinity;
        const templateFilter = this.templateFilter?.value || '';

        const productCards = this.container?.querySelectorAll('.product-card');
        if (!productCards) return;

        productCards.forEach(card => {
            let show = true;

            // Title search filter
            const title = card.querySelector('.title')?.textContent.toLowerCase() || '';
            const handle = card.querySelector('.meta')?.textContent.toLowerCase() || '';
            if (searchTerm && !title.includes(searchTerm) && !handle.includes(searchTerm)) {
                show = false;
            }

            // Price filter
            const priceEl = card.querySelector('.price')?.textContent || '';
            const price = parseFloat(priceEl.replace('$', '')) || 0;
            if (price < minPrice || price > maxPrice) {
                show = false;
            }

            // Template filter
            const hasTemplate = card.querySelector('.template-badge') !== null;
            if (templateFilter === 'has-template' && !hasTemplate) {
                show = false;
            } else if (templateFilter === 'no-template' && hasTemplate) {
                show = false;
            }

            // Show/hide card with animation
            if (show) {
                card.style.display = 'flex';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            } else {
                card.style.opacity = '0';
                card.style.transform = 'translateY(10px)';
                setTimeout(() => {
                    card.style.display = 'none';
                }, 300);
            }
        });
    }

    renderProductCard(product) {
        // Validate product object
        if (!product || typeof product !== 'object') {
            console.error('Invalid product object:', product);
            return ''; // Skip rendering invalid products
        }

        // Default values and validation
        const safeProduct = {
            id: product.id || 'unknown',
            title: product.title || 'Untitled Product',
            handle: product.handle || this._generateHandle(product.title || 'untitled'),
            template_suffix: product.template_suffix || '',
            variants: Array.isArray(product.variants) ? product.variants : [],
            images: Array.isArray(product.images) ? product.images : [],
            status: product.status || 'draft',
            updated_at: product.updated_at || new Date().toISOString()
        };

        // Image section with status badge
        const imageSection = `
            <div class="image-container">
                ${safeProduct.images.length > 0 
                    ? `<img src="${safeProduct.images[0].src}" alt="${safeProduct.title}" class="image">`
                    : `<div class="product-placeholder">
                        <i class="fas fa-image text-4xl text-gray-400"></i>
                       </div>`
                }
            </div>`;

        return `
            <div class="product-card" data-product-id="${safeProduct.id}" data-product-handle="${safeProduct.handle}">
                ${this._renderStatusBadge(safeProduct.status)}
                ${imageSection}
                <div class="content">
                    <h3 class="title">${safeProduct.title}</h3>
                    <a href="https://${window.config.SHOP_URL}/products/${safeProduct.handle}" 
                       class="meta" 
                       target="_blank"
                       title="View product page">
                        <i class="fas fa-link text-sm mr-1"></i>
                        ${safeProduct.handle}
                    </a>
                    ${safeProduct.template_suffix ? `
                        <div class="template-badge">
                            <span class="bg-primary/20 text-primary px-2 py-1 rounded-lg text-sm font-medium">
                                ${safeProduct.template_suffix}
                            </span>
                        </div>` : ''
                    }
                    <div class="last-updated">
                        <i class="far fa-clock mr-1"></i>
                        Updated ${this._formatDate(safeProduct.updated_at)}
                    </div>
                    <div class="flex justify-between items-center">
                        <p class="price">
                            ${safeProduct.variants.length > 0 
                                ? `$${parseFloat(safeProduct.variants[0].price).toFixed(2)}`
                                : 'No price set'
                            }
                        </p>
                        <span class="text-sm text-gray-400">
                            ${safeProduct.variants.length} variant(s)
                        </span>
                    </div>
                    <div class="actions border-t border-gray-700 mt-4 pt-4">
                        <div class="grid grid-cols-2 gap-2 mb-2">
                            <button class="preview-btn flex items-center justify-center py-2 px-4 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors duration-200 text-sm">
                                <i class="fas fa-eye mr-2"></i>
                                Preview
                            </button>
                            <button class="edit-btn flex items-center justify-center py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors duration-200 text-sm">
                                <i class="fas fa-edit mr-2"></i>
                                Edit
                            </button>
                        </div>
                        <div class="grid grid-cols-2 gap-2">
                            <button class="duplicate-btn flex items-center justify-center py-2 px-4 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors duration-200 text-sm">
                                <i class="fas fa-copy mr-2"></i>
                                Duplicate
                            </button>
                            <button class="delete-btn flex items-center justify-center py-2 px-4 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors duration-200 text-sm">
                                <i class="fas fa-trash mr-2"></i>
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            </div>`;
    }

    _renderStatusBadge(status) {
        const statusMap = {
            active: { icon: 'check-circle', text: 'Active' },
            draft: { icon: 'pencil-alt', text: 'Draft' },
            archived: { icon: 'archive', text: 'Archived' }
        };

        const statusInfo = statusMap[status] || statusMap.draft;
        return `
            <div class="status-badge ${status}" title="${statusInfo.text} product">
                <i class="fas fa-${statusInfo.icon}"></i>
                ${statusInfo.text}
            </div>`;
    }

    _formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) {
            return 'Today';
        } else if (diffDays === 1) {
            return 'Yesterday';
        } else if (diffDays < 7) {
            return `${diffDays} days ago`;
        } else {
            return date.toLocaleDateString();
        }
    }

    _generateHandle(title) {
        // Convert to lowercase and replace spaces with hyphens
        let handle = title.toLowerCase().replace(/\s+/g, '-');
        
        // Remove special characters
        handle = handle.replace(/[^a-z0-9-]/g, '');
        
        // Remove multiple consecutive hyphens
        handle = handle.replace(/-+/g, '-');
        
        // Remove leading/trailing hyphens
        handle = handle.replace(/^-+|-+$/g, '');
        
        // If empty, return a default
        return handle || 'untitled-product';
    }

    editProduct(handle) {
        const url = `https://admin.shopify.com/store/${window.config.SHOP_URL.split('.')[0]}/themes/${window.config.active_theme_id}/editor?previewPath=/products/${handle}`;
        window.open(url, '_blank');
    }

    async duplicateProduct(productId) {
        const toastId = ToastService.info('Duplicating product...', { autoClose: false });
        
        try {
            const response = await fetch(`/api/products/${productId}`, {
                method: 'POST',
                headers: APIService.headers
            });
            
            if (response.ok) {
                const data = await response.json();
                ToastService.success('Product duplicated successfully');
                await this.updateGrid();
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

    async deleteProduct(productId) {
        // Create a new warning modal instance for each delete operation
        const deleteWarningModal = new WarningModal({
            title: 'Confirm Product Deletion',
            message: `
                <div class="space-y-4">
                    <p class="text-red-400 font-medium">This action cannot be undone.</p>
                    <p>When you delete a product:</p>
                    <ul class="list-disc list-inside space-y-2 text-gray-300">
                        <li>The product will be permanently removed from your store</li>
                        <li>All variants and images will be deleted</li>
                        <li>Product URLs will stop working</li>
                        <li>Associated templates will be removed</li>
                    </ul>
                    <p class="mt-4 text-gray-400">Are you sure you want to proceed?</p>
                </div>
            `,
            confirmText: 'Yes, Delete Product',
            cancelText: 'No, Keep Product',
            confirmClass: 'bg-red-500 hover:bg-red-600',
            type: 'danger'
        });

        const shouldDelete = await deleteWarningModal.show();

        if (shouldDelete) {
            const toastId = ToastService.info('Deleting product...', { autoClose: false });
            
            try {
                const response = await fetch(`/api/products/${productId}`, {
                    method: 'DELETE',
                    headers: APIService.headers
                });
                
                if (response.ok) {
                    ToastService.success('Product deleted successfully');
                    await this.updateGrid();
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
    }
}

// Export components for global use
window.ModalComponent = ModalComponent;
window.ProductForm = ProductForm;
window.WarningModal = WarningModal;
window.LoadingModal = LoadingModal;
window.ProductGrid = ProductGrid; 