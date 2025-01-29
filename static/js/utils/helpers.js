// helpers.js - Common utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

async function fetchData(endpoint) {
    try {
        const response = await fetch(endpoint);
        if (!response.ok) throw new Error('Network response was not ok');
        return await response.json();
    } catch (error) {
        toast.error('Error fetching data: ' + error.message);
        return null;
    }
}

function showLoading(message = 'Loading...') {
    const loading = document.createElement('div');
    loading.id = 'loadingIndicator';
    loading.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    loading.innerHTML = `
        <div class="bg-secondary p-6 rounded-lg text-center">
            <div class="loading mx-auto mb-4"></div>
            <p>${message}</p>
        </div>
    `;
    document.body.appendChild(loading);
}

function hideLoading() {
    const loading = document.getElementById('loadingIndicator');
    if (loading) {
        loading.remove();
    }
}

// Export for use in other files
window.helpers = {
    debounce,
    fetchData,
    showLoading,
    hideLoading
}; 