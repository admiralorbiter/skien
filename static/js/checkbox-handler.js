// Global Checkbox Handler
// This script provides consistent checkbox styling across the application

document.addEventListener('DOMContentLoaded', function() {
    // Function to update checkbox visual state
    function updateCheckboxStyle(checkbox) {
        if (checkbox.checked) {
            checkbox.style.setProperty('background-color', '#B75D69', 'important');
            checkbox.style.setProperty('border-color', '#B75D69', 'important');
            checkbox.style.setProperty('background-image', 'url("data:image/svg+xml,%3csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 20 20\'%3e%3cpath fill=\'none\' stroke=\'%23fff\' stroke-linecap=\'round\' stroke-linejoin=\'round\' stroke-width=\'3\' d=\'m6 10 3 3 6-6\'/%3e%3c/svg%3e")', 'important');
        } else {
            checkbox.style.setProperty('background-color', '#fff', 'important');
            checkbox.style.setProperty('border-color', 'rgba(0, 0, 0, 0.25)', 'important');
            checkbox.style.setProperty('background-image', 'none', 'important');
        }
    }
    
    // Apply styling to all checkboxes on the page
    function initializeCheckboxes() {
        const checkboxes = document.querySelectorAll('input[type="checkbox"].form-check-input');
        checkboxes.forEach(checkbox => {
            // Apply initial styling
            updateCheckboxStyle(checkbox);
            
            // Add event listener for changes
            checkbox.addEventListener('change', function(e) {
                updateCheckboxStyle(e.target);
            });
        });
    }
    
    // Initialize checkboxes when page loads
    initializeCheckboxes();
    
    // Re-initialize checkboxes if new content is loaded dynamically
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        const newCheckboxes = node.querySelectorAll ? node.querySelectorAll('input[type="checkbox"].form-check-input') : [];
                        newCheckboxes.forEach(checkbox => {
                            updateCheckboxStyle(checkbox);
                            checkbox.addEventListener('change', function(e) {
                                updateCheckboxStyle(e.target);
                            });
                        });
                    }
                });
            }
        });
    });
    
    // Start observing
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});
