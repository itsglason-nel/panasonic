modal_html = """
<!-- QC Report Print Modal -->
<div id="modal-qc-print" class="modal-overlay">
    <div class="modal-content" style="max-width: 400px;">
        <div class="modal-header">
            <h3 class="modal-title">Print Specific QC Report</h3>
            <button class="modal-close" onclick="closeQCReportModal()">&times;</button>
        </div>
        <div class="modal-body">
            <div class="form-group">
                <label>Model Code</label>
                <input type="text" id="qc-print-model" class="form-control" placeholder="e.g. CW-U921JPH">
            </div>
            <div class="form-group" style="margin-top: 15px;">
                <label>Serial Number</label>
                <input type="text" id="qc-print-serial" class="form-control" placeholder="e.g. 0000000001">
            </div>
            <div class="modal-actions" style="margin-top: 20px;">
                <button class="btn btn-secondary" onclick="closeQCReportModal()">Cancel</button>
                <button class="btn btn-primary" onclick="submitQCReportPrint()">Print</button>
            </div>
        </div>
    </div>
</div>
"""

with open('app/templates/admin/components/modals.html', 'a') as f:
    f.write(modal_html)
