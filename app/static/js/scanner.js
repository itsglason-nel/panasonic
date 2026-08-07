/**
 * PMPC Data Logger — Part Scanner Logic
 * Handles BOM validation and part scanning for operator stations.
 */

var ScannerApp = (function() {
    var state = {
        unitId: null,
        serial: null,
        modelNumber: null,
        stationCode: null,
        moduleCode: null,
        requiredParts: [],
        scannedParts: [] // { part_id, part_number, tag, part_qr_raw, part_lot_id, quantity }
    };

    function init(stationCode, moduleCode) {
        state.stationCode = stationCode;
        state.moduleCode = moduleCode;
        
        // Hook into the serial scan success (from app.js)
        var originalShowUnitInfo = window.showUnitInfo;
        window.showUnitInfo = function(data) {
            if (originalShowUnitInfo) originalShowUnitInfo(data);
            
            state.unitId = data.id;
            state.serial = data.serial;
            state.modelNumber = data.model_number;
            state.scannedParts = []; // Reset
            
            // Fetch BOM for this model and module
            loadBOM(data.model_number, state.moduleCode);
        };
    }

    function loadBOM(modelNumber, moduleCode) {
        var scanArea = document.getElementById('part-scan-area');
        scanArea.innerHTML = '<p class="text-center text-muted">Loading required parts...</p>';
        
        apiGet('/api/bom/' + encodeURIComponent(modelNumber) + '/' + encodeURIComponent(moduleCode))
            .then(function(data) {
                state.requiredParts = data.parts || [];
                renderPartScanUI();
            })
            .catch(function(err) {
                console.error('BOM fetch error:', err);
                scanArea.innerHTML = '<div class="alert alert-danger">Error loading parts list.</div>';
            });
    }

    function renderPartScanUI() {
        var scanArea = document.getElementById('part-scan-area');
        
        if (state.requiredParts.length === 0) {
            // No parts required for this station/module
            scanArea.innerHTML = '<div class="alert alert-info">No parts required to be scanned for this station. You can submit the result.</div>';
            checkSubmitStatus();
            return;
        }

        var html = '<div class="mt-4">';
        html += '<h4 class="mb-2">Required Parts</h4>';
        html += '<table class="data-table" id="parts-table">';
        html += '<thead><tr><th>Type</th><th>Expected Part</th><th>Status</th></tr></thead>';
        html += '<tbody>';
        
        state.requiredParts.forEach(function(part, index) {
            html += '<tr id="part-row-' + index + '">';
            html += '<td>' + part.part_type + '</td>';
            html += '<td><div class="text-mono">' + part.part_number + '</div><div class="text-xs text-muted">' + part.description + '</div></td>';
            html += '<td id="part-status-' + index + '"><span class="badge badge-pending">PENDING</span></td>';
            html += '</tr>';
        });
        
        // Dynamic Fan Motor Area (Specific for SFIS1)
        if (state.stationCode === 'SFIS1') {
            html += '<tr class="bg-hover">';
            html += '<td>Fan Motor(s)</td>';
            html += '<td colspan="2">';
            html += '<div id="dynamic-fan-motors" class="flex flex-col gap-2"></div>';
            html += '<div class="mt-2 text-xs text-muted">Scan additional fan motors if needed. System accepts multiple.</div>';
            html += '</td>';
            html += '</tr>';
        }
        
        html += '</tbody></table>';
        
        // Part Scan Input
        html += '<div class="form-group mt-6">';
        html += '<label class="form-label" for="part-input">Scan Part Barcode</label>';
        html += '<input type="text" id="part-input" class="form-input" placeholder="Scan part..." autocomplete="off">';
        html += '</div>';
        
        html += '</div>';
        
        scanArea.innerHTML = html;
        
        // Setup part input listener
        var partInput = document.getElementById('part-input');
        if (partInput) {
            partInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    var barcode = this.value.trim();
                    if (barcode) {
                        processPartScan(barcode);
                        this.value = ''; // clear
                    }
                }
            });
            partInput.focus();
        }
        
        checkSubmitStatus();
    }

    function processPartScan(barcode) {
        // Decode barcode (for safety parts it might be | delimited)
        // For standard parts, we assume the barcode is exactly the part number
        var partNumber = barcode;
        if (barcode.indexOf('|') !== -1 || barcode.indexOf(',') !== -1) {
            var parts = barcode.split(/[|,]/);
            partNumber = parts[0].trim();
        }
        
        // Check if this part matches any required part
        var matchedIndex = -1;
        var matchedPart = null;
        
        for (var i = 0; i < state.requiredParts.length; i++) {
            var rp = state.requiredParts[i];
            if (rp.part_number === partNumber) {
                // Check if already scanned (unless it's a fan motor on SFIS1 which is dynamic)
                var alreadyScanned = state.scannedParts.some(function(sp) {
                    return sp.req_index === i;
                });
                
                if (!alreadyScanned || (state.stationCode === 'SFIS1' && rp.part_type === 'Fan Motor')) {
                    matchedIndex = i;
                    matchedPart = rp;
                    break;
                }
            }
        }
        
        if (matchedPart) {
            // Add to scanned parts
            state.scannedParts.push({
                req_index: matchedIndex,
                part_id: matchedPart.part_id,
                part_number: matchedPart.part_number,
                tag: matchedPart.tag,
                part_qr_raw: barcode,
                quantity: 1.0
            });
            
            // Update UI
            if (state.stationCode === 'SFIS1' && matchedPart.part_type === 'Fan Motor') {
                // Add to dynamic list
                var fanList = document.getElementById('dynamic-fan-motors');
                var fanDiv = document.createElement('div');
                fanDiv.className = 'badge badge-good';
                fanDiv.innerHTML = '✓ ' + partNumber;
                fanList.appendChild(fanDiv);
                
                // Mark the main row as good if it wasn't already
                var statusCell = document.getElementById('part-status-' + matchedIndex);
                statusCell.innerHTML = '<span class="badge badge-good">VERIFIED</span>';
            } else {
                // Standard row update
                var statusCell = document.getElementById('part-status-' + matchedIndex);
                statusCell.innerHTML = '<span class="badge badge-good">VERIFIED</span>';
            }
            
        } else {
            // Error - mismatch
            alert('INCORRECT PART SCANNED!\n\nExpected one of the pending required parts, but got: ' + partNumber);
            // In a real environment, this might print a label
            // window.print(); // (trigger error label print)
        }
        
        checkSubmitStatus();
    }

    function checkSubmitStatus() {
        var btnGood = document.getElementById('btn-good');
        if (!btnGood) return;
        
        // Ensure all required parts (at least 1 of each) are scanned
        var allSatisfied = true;
        for (var i = 0; i < state.requiredParts.length; i++) {
            var hasScanned = state.scannedParts.some(function(sp) { return sp.req_index === i; });
            if (!hasScanned) {
                allSatisfied = false;
                break;
            }
        }
        
        btnGood.disabled = !allSatisfied;
    }
    
    function getScannedPartsData() {
        // Return cleaned up data for API submission
        return state.scannedParts.map(function(sp) {
            return {
                part_id: sp.part_id,
                tag: sp.tag,
                quantity: sp.quantity,
                part_qr_raw: sp.part_qr_raw
            };
        });
    }

    return {
        init: init,
        getScannedPartsData: getScannedPartsData,
        getState: function() { return state; }
    };
})();
