/**
 * Cluster Simulation Dashboard
 * Common JavaScript functionality
 */

// Set active nav link based on current page
document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('#sidebar .nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Initialize tooltips
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
});

/**
 * Format timestamp to readable date/time
 * @param {number} timestamp - Unix timestamp
 * @returns {string} Formatted date string
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString();
}

/**
 * Create a loading spinner element
 * @returns {HTMLElement} Spinner element
 */
function createSpinner() {
    const spinner = document.createElement('div');
    spinner.className = 'spinner mx-auto my-3';
    return spinner;
}

/**
 * Show a notification message
 * @param {string} message - Message to display
 * @param {string} type - Message type (success, warning, danger)
 * @param {number} duration - Duration in milliseconds
 */
function showNotification(message, type = 'success', duration = 3000) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `toast align-items-center text-white bg-${type} border-0 fade-in`;
    notification.setAttribute('role', 'alert');
    notification.setAttribute('aria-live', 'assertive');
    notification.setAttribute('aria-atomic', 'true');
    
    // Add content
    notification.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Add to document
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.appendChild(notification);
    document.body.appendChild(container);
    
    // Show notification
    const toast = new bootstrap.Toast(notification, { autohide: true, delay: duration });
    toast.show();
    
    // Remove from DOM when hidden
    notification.addEventListener('hidden.bs.toast', function() {
        container.remove();
    });
}

/**
 * Make an API call with loading indicator
 * @param {string} url - API endpoint
 * @param {Object} options - Fetch options
 * @param {HTMLElement} loadingElement - Element to show/hide loading indicator
 * @returns {Promise} Fetch promise
 */
function apiCall(url, options = {}, loadingElement = null) {
    if (loadingElement) {
        const spinner = createSpinner();
        loadingElement.innerHTML = '';
        loadingElement.appendChild(spinner);
    }
    
    return fetch(url, options)
        .then(response => {
            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }
            return response.json();
        })
        .finally(() => {
            if (loadingElement) {
                loadingElement.innerHTML = '';
            }
        });
}

/**
 * Get node status CSS class
 * @param {string} status - Node status
 * @returns {string} CSS class
 */
function getStatusClass(status) {
    switch (status.toLowerCase()) {
        case 'online':
            return 'success';
        case 'offline':
            return 'danger';
        case 'starting':
            return 'warning';
        default:
            return 'secondary';
    }
} 