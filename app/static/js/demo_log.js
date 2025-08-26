/**
 * AdCP Demo Console Logger
 * Logs user interactions and page events for demo debugging
 */

(function() {
    'use strict';
    
    // Configuration
    const LOG_PREFIX = '[ADCP]';
    const REQUEST_ID_META = 'request-id';
    const LOGS_ENABLED_META = 'adcp-demo-logs';
    const FORM_LOG_ATTR = 'data-log';
    
    // Get configuration from meta tags
    function getMetaContent(name) {
        const meta = document.querySelector(`meta[name="${name}"]`);
        return meta ? meta.getAttribute('content') : null;
    }
    
    // Check if logging is enabled
    function isLoggingEnabled() {
        return getMetaContent(LOGS_ENABLED_META) === 'on';
    }
    
    // Get request ID
    function getRequestId() {
        return getMetaContent(REQUEST_ID_META) || 'unknown';
    }
    
    // Safe logging function
    function log(message) {
        if (isLoggingEnabled()) {
            console.log(`${LOG_PREFIX} ${message}`);
        }
    }
    
    // Log page load
    function logPageLoad() {
        const path = window.location.pathname;
        const requestId = getRequestId();
        log(`page-load path=${path} rid=${requestId}`);
    }
    
    // Log form submissions
    function setupFormLogging() {
        const forms = document.querySelectorAll(`form[${FORM_LOG_ATTR}="true"]`);
        
        forms.forEach(form => {
            const formId = form.id || form.getAttribute('action') || 'unknown';
            
            form.addEventListener('submit', function(e) {
                const requestId = getRequestId();
                const startTime = Date.now();
                
                log(`submit id=${formId} rid=${requestId}`);
                
                // Log completion after page loads
                setTimeout(() => {
                    const duration = Date.now() - startTime;
                    log(`submit-complete id=${formId} ${duration}ms`);
                }, 100);
            });
        });
    }
    
    // Log HTMX events if available
    function setupHtmxLogging() {
        if (typeof htmx !== 'undefined') {
            document.addEventListener('htmx:afterOnLoad', function(event) {
                const target = event.target.id || event.target.tagName;
                log(`htmx-load target=${target}`);
            });
        }
    }
    
    // Initialize logging when DOM is ready
    function init() {
        try {
            logPageLoad();
            setupFormLogging();
            setupHtmxLogging();
        } catch (error) {
            // Never throw errors from logging
            console.warn('AdCP logging initialization failed:', error);
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
