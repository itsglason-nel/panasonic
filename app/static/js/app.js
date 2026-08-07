/**
 * PMPC Data Logger — Core Application JavaScript
 * 100% Offline — No CDN dependencies
 */

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss flash alerts after 5 seconds
    document.querySelectorAll('.alert').forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-10px)';
            setTimeout(function() { alert.remove(); }, 300);
        }, 5000);
    });

    // Login form loading state
    var loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function() {
            var btn = document.getElementById('login-btn');
            if (btn) {
                btn.disabled = true;
                btn.textContent = 'Signing in...';
            }
        });
    }
});


/**
 * Show scan result overlay (GOOD / NO GOOD)
 * @param {string} result - 'good' or 'no-good'
 * @param {number} duration - ms to show (default 1500)
 */
function showScanResult(result, duration) {
    duration = duration || 1500;

    // Remove existing overlay
    var existing = document.getElementById('scan-result-overlay');
    if (existing) existing.remove();

    var overlay = document.createElement('div');
    overlay.id = 'scan-result-overlay';
    overlay.className = 'scan-result-overlay';
    overlay.innerHTML = '<div class="scan-result-card ' + result + '">' +
        '<div class="result-icon">' + (result === 'good' ? '✓' : '✗') + '</div>' +
        '<div class="result-text">' + (result === 'good' ? 'GOOD' : 'NO GOOD') + '</div>' +
        '</div>';

    document.body.appendChild(overlay);

    // Trigger animation
    requestAnimationFrame(function() {
        overlay.classList.add('show');
    });

    // Auto-hide
    setTimeout(function() {
        overlay.classList.remove('show');
        setTimeout(function() { overlay.remove(); }, 300);
    }, duration);
}


/**
 * Format serial number for display
 * @param {string} serial
 * @returns {string}
 */
function formatSerial(serial) {
    return serial ? serial.toUpperCase().trim() : '';
}


/**
 * API helper — fetch JSON from local server
 * @param {string} url
 * @param {object} options
 * @returns {Promise<object>}
 */
function apiGet(url) {
    return fetch(url, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        credentials: 'same-origin',
    }).then(function(r) { return r.json(); });
}

function apiPost(url, data) {
    return fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
        credentials: 'same-origin',
        body: JSON.stringify(data),
    }).then(function(r) { return r.json(); });
}

/**
 * Automatically inject data-label to table cells for responsive card layout
 */
function applyTableDataLabels() {
    document.querySelectorAll('.data-table').forEach(function(table) {
        var headers = Array.from(table.querySelectorAll('thead th')).map(function(th) {
            return th.textContent.trim();
        });
        table.querySelectorAll('tbody tr').forEach(function(row) {
            Array.from(row.querySelectorAll('td')).forEach(function(td, index) {
                // Ignore colspan elements (like empty state messages)
                if (td.hasAttribute('colspan')) return;
                
                if (headers[index] && !td.hasAttribute('data-label')) {
                    td.setAttribute('data-label', headers[index]);
                }
            });
        });
    });
}

// Run on initial load
document.addEventListener('DOMContentLoaded', applyTableDataLabels);

// Observe DOM for dynamically loaded tables
var observer = new MutationObserver(function(mutations) {
    var shouldUpdate = false;
    for (var i = 0; i < mutations.length; i++) {
        if (mutations[i].type === 'childList') {
            shouldUpdate = true;
            break;
        }
    }
    if (shouldUpdate) applyTableDataLabels();
});

document.addEventListener('DOMContentLoaded', function() {
    observer.observe(document.body, { childList: true, subtree: true });
});
