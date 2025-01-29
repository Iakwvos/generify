// ProductGrid.js - Handles all product grid related functionality
class ProductGrid {
    constructor() {
        this.container = document.querySelector('.products-grid');
        this.searchInput = document.getElementById('product-search');
        this.minPriceInput = document.getElementById('min-price');
        this.maxPriceInput = document.getElementById('max-price');
        this.templateFilter = document.getElementById('template-filter');
    }

    async updateGrid() {
        try {
            const response = await fetch('/api/products');
            if (!response.ok) {
                throw new Error('Failed to fetch products');
            }
            const data = await response.json();
            
            if (this.container) {
                // Check if data.products exists, if not, use data directly
                const products = data.products || data;
                if (!Array.isArray(products)) {
                    throw new Error('Invalid products data structure');
                }
                this.container.innerHTML = products.map(product => this.renderProductCard(product)).join('');
            }
        } catch (error) {
            console.error('Error updating products grid:', error);
            ToastService.error('Failed to update products grid');
        }
    }

    renderProductCard(product) {
        return `
            <div class="dashboard-card product-card group">
                <div class="flex flex-col h-full">
                    <div class="relative">
                        ${product.images && product.images.length > 0 
                            ? `<img src="${product.images[0].src}" alt="${product.title}" class="product-image rounded-t-lg">`
                            : `<div class="product-placeholder bg-gray-700 rounded-t-lg flex items-center justify-center">
                                <i class="fas fa-image text-4xl text-gray-400"></i>
                               </div>`
                        }
                    </div>
                    <div class="p-4 flex-grow flex flex-col">
                        <div class="flex-grow">
                            <h3 class="text-lg font-semibold mb-2">${product.title}</h3>
                            <p class="text-gray-400 text-sm mb-2">${product.handle}</p>
                            ${product.template_suffix 
                                ? `<div class="mb-3">
                                    <span class="bg-primary/20 text-primary px-2 py-1 rounded-lg text-sm font-medium">
                                        ${product.template_suffix}
                                    </span>
                                   </div>`
                                : ''
                            }
                            ${product.variants && product.variants.length > 0 
                                ? `<div class="flex justify-between items-center mb-4">
                                    <p class="text-lg font-bold text-primary">$${product.variants[0].price}</p>
                                    <span class="text-sm text-gray-400">${product.variants.length} variant(s)</span>
                                   </div>`
                                : ''
                            }
                        </div>
                        <div class="mt-4 pt-4 border-t border-gray-700">
                            <div class="grid grid-cols-2 gap-2 mb-2">
                                <button onclick="window.open('https://${window.config.SHOP_URL}/products/${product.handle}', '_blank')" 
                                        class="flex-1 py-2 px-4 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors duration-200 flex items-center justify-center text-sm">
                                    <i class="fas fa-eye mr-2"></i>
                                    Preview
                                </button>
                                ${window.config.active_theme_id 
                                    ? `<button onclick="productActions.edit('${product.handle}')"
                                            class="flex-1 py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors duration-200 flex items-center justify-center text-sm">
                                        <i class="fas fa-edit mr-2"></i>
                                        Edit
                                       </button>`
                                    : `<button disabled
                                            class="flex-1 py-2 px-4 bg-gray-400 text-white rounded-lg flex items-center justify-center text-sm cursor-not-allowed">
                                        <i class="fas fa-edit mr-2"></i>
                                        Edit
                                       </button>`
                                }
                            </div>
                            <div class="grid grid-cols-2 gap-2">
                                <button onclick="productActions.duplicate('${product.id}')" 
                                        class="flex-1 py-2 px-4 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors duration-200 flex items-center justify-center text-sm">
                                    <i class="fas fa-copy mr-2"></i>
                                    Duplicate
                                </button>
                                <button onclick="productActions.showDeleteModal('${product.id}')" 
                                        class="flex-1 py-2 px-4 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors duration-200 flex items-center justify-center text-sm">
                                    <i class="fas fa-trash mr-2"></i>
                                    Delete
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    filterProducts() {
        const searchTerm = this.searchInput?.value.toLowerCase();
        const minPrice = this.minPriceInput?.value ? parseFloat(this.minPriceInput.value) : 0;
        const maxPrice = this.maxPriceInput?.value ? parseFloat(this.maxPriceInput.value) : Infinity;
        const templateFilter = this.templateFilter?.value;

        const productCards = this.container?.querySelectorAll('.product-card');
        if (!productCards) return;

        productCards.forEach(card => {
            const title = card.querySelector('h3')?.textContent.toLowerCase();
            const priceEl = card.querySelector('.product-price');
            const price = priceEl ? parseFloat(priceEl.textContent.replace('$', '')) : 0;
            const hasTemplate = card.querySelector('.template-badge') !== null;

            let show = true;

            // Apply search filter
            if (searchTerm && !title?.includes(searchTerm)) {
                show = false;
            }

            // Apply price filter
            if (price < minPrice || price > maxPrice) {
                show = false;
            }

            // Apply template filter
            if (templateFilter === 'has-template' && !hasTemplate) {
                show = false;
            } else if (templateFilter === 'no-template' && hasTemplate) {
                show = false;
            }

            card.style.display = show ? 'block' : 'none';
        });
    }
}

// Initialize ProductGrid when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.productGrid = new ProductGrid();
}); 