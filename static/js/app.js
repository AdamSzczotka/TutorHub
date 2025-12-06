// HTMX configuration
document.addEventListener('DOMContentLoaded', function() {
    // Configure HTMX
    if (typeof htmx !== 'undefined') {
        htmx.config.defaultSwapStyle = 'innerHTML';
        htmx.config.historyCacheSize = 10;

        // Global error handling
        document.body.addEventListener('htmx:responseError', function(event) {
            console.error('HTMX Error:', event.detail);
            const toast = document.getElementById('toast-container');
            if (toast) {
                toast.innerHTML = `
                    <div class="alert alert-error">
                        <span>Wystąpił błąd. Spróbuj ponownie.</span>
                    </div>
                `;
            }
        });

        // Loading indicator
        htmx.on('htmx:beforeRequest', function(event) {
            event.target.classList.add('loading');
        });

        htmx.on('htmx:afterRequest', function(event) {
            event.target.classList.remove('loading');
        });
    }
});

// Modal helper functions
function openModal() {
    const modal = document.getElementById('modal');
    if (modal) {
        modal.showModal();
    }
}

function closeModal() {
    const modal = document.getElementById('modal');
    if (modal) {
        modal.close();
    }
}
