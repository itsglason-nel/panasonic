path = r'app\templates\admin\components\modals.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Header Info replacement for GMS
old_header = """            <div
                style="display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 20px; background: var(--bg-main); padding: 12px 16px; border-radius: 8px; border: 1px solid var(--border-light);">
                <div style="flex: 1; min-width: 120px;">
                    <span
                        style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Date
                        / Time</span>
                    <strong id="gms-det-date" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span
                        style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Model
                        Code</span>
                    <strong id="gms-det-model" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span
                        style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Serial</span>
                    <strong id="gms-det-serial" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span
                        style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Line
                        No</span>
                    <strong id="gms-det-lineno" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
            </div>"""

new_header = """            <!-- Header Info -->
            <div
                style="display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 20px; background: var(--bg-main); padding: 12px 16px; border-radius: 8px; border: 1px solid var(--border-light);">
                <div style="flex: 1; min-width: 120px;">
                    <span style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Date / Time</span>
                    <strong id="gms-det-date" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Model Code</span>
                    <strong id="gms-det-model" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Serial</span>
                    <strong id="gms-det-serial" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Status</span>
                    <div style="margin-top: 4px;" id="gms-det-top-status">
                    </div>
                </div>
            </div>"""

html = html.replace(old_header, new_header)

# 2. Grid and Additional Info replacement for GMS
old_grid = """            <div style="display: grid; grid-template-columns: 1fr; gap: 16px;">
                <div
                    style="background: var(--bg-card); border: 1px solid var(--border-light); border-radius: 8px; padding: 16px;">
                    <h4
                        style="margin: 0 0 16px 0; font-size: 13px; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border-light); padding-bottom: 8px;">
                        Inspection Status</h4>
                    <div style="display: flex; flex-direction: column; gap: 12px; font-size: 14px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color:var(--text-secondary);">Gas Charge (kg):</span>
                            <strong id="gms-det-gascharge" style="color: var(--text-primary);"></strong>
                        </div>
                        <div
                            style="display: flex; justify-content: space-between; align-items: center; padding-top: 12px; border-top: 1px dashed var(--border-light);">
                            <span style="color:var(--text-secondary); font-weight: 600;">Overall Result:</span>
                            <span id="gms-det-status" style="font-weight: 600;"></span>
                        </div>
                    </div>
                </div>
                <div
                    style="background: var(--bg-card); border: 1px solid var(--border-light); border-radius: 8px; padding: 16px;">
                    <h4
                        style="margin: 0 0 16px 0; font-size: 13px; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border-light); padding-bottom: 8px;">
                        Additional Information</h4>
                    <div style="display: flex; flex-direction: column; gap: 12px; font-size: 14px;">
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color:var(--text-secondary);">Inspector:</span>
                            <strong id="gms-det-inspector" style="color: var(--text-primary);"></strong>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <span style="color:var(--text-secondary);">Remarks:</span>
                            <strong id="gms-det-remarks"
                                style="color: var(--text-primary); max-width: 60%; text-align: right; word-wrap: break-word;"></strong>
                        </div>
                    </div>
                </div>
            </div>

            <div class="modal-actions" style="margin-top: 24px;">
                <button class="btn btn-secondary" onclick="closeGMSDetailsModal()">Close</button>
            </div>"""

new_grid = """            <div style="display: grid; grid-template-columns: 1fr; gap: 16px;">
                <div
                    style="background: var(--bg-card); border: 1px solid var(--border-light); border-radius: 8px; padding: 16px;">
                    <h4
                        style="margin: 0 0 16px 0; font-size: 13px; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border-light); padding-bottom: 8px; height: 38px; display: flex; align-items: center; justify-content: center; text-align: center;">
                        Inspection Status</h4>
                    <div style="display: flex; flex-direction: column; gap: 12px; font-size: 14px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color:var(--text-secondary);">Gas Charge (kg):</span>
                            <strong id="gms-det-gascharge" style="color: var(--text-primary);"></strong>
                        </div>
                        <div
                            style="display: flex; justify-content: space-between; align-items: center; padding-top: 12px; border-top: 1px dashed var(--border-light);">
                            <span style="color:var(--text-secondary); font-weight: 600;">Overall Result:</span>
                            <span id="gms-det-status" style="font-weight: 600;"></span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Meta info -->
            <div style="margin-top: 16px; padding: 12px; background: var(--bg-main); border: 1px solid var(--border-light); border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; font-size: 13px;">
                    <div><span style="color:var(--text-secondary);">Inspector:</span> <strong id="gms-det-inspector" style="color: var(--text-primary);"></strong></div>
                    <div style="text-align: right;"><span style="color:var(--text-secondary);">Line No.:</span> <strong id="gms-det-lineno" style="color: var(--text-primary);"></strong></div>
                </div>
            </div>

            <div class="modal-actions" style="margin-top: 24px;">
                <button class="btn btn-secondary" onclick="closeGMSDetailsModal()">Close</button>
            </div>"""

html = html.replace(old_grid, new_grid)

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated GMS modal layout in modals.html")
