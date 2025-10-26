// Main JavaScript for Tsuru Groups

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize fade-in animations
    const fadeElements = document.querySelectorAll('.fade-in, .fade-in-delay');
    fadeElements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
    });

    // Trigger animations when elements are in view
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                entry.target.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            }
        });
    });

    fadeElements.forEach(element => {
        observer.observe(element);
    });

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', function(event) {
            // Always add validation classes
            form.classList.add('was-validated');
            
            // Only prevent submission if form is invalid
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                console.log('Formulário inválido - envio cancelado');
                return false;
            }
            
            console.log('Formulário válido - permitindo envio');
            // Form is valid, let it submit naturally
        });
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Loading button states
    const loadingButtons = document.querySelectorAll('[data-loading-text]');
    loadingButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            // Check if this is a submit button in a form
            if (this.type === 'submit') {
                const form = this.closest('form');
                if (form && !form.checkValidity()) {
                    // Form is invalid, don't show loading state
                    return;
                }
            }
            
            const originalText = this.innerHTML;
            const loadingText = this.getAttribute('data-loading-text');
            
            this.innerHTML = loadingText;
            this.classList.add('loading');
            
            // Don't disable submit buttons to allow form submission
            if (this.type !== 'submit') {
                this.disabled = true;
            }

            // Reset after timeout (form submission will redirect anyway)
            setTimeout(() => {
                this.innerHTML = originalText;
                this.classList.remove('loading');
                this.disabled = false;
            }, 5000);
        });
    });
});

// Utility functions
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
}

// Export functions for use in other scripts
window.TsuruGroups = {
    showToast: showToast
};