path = r'app\templates\admin\components\modals.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Header replacement
old_header = """            <!-- Header Info -->
            <div
                style="display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 20px; background: var(--bg-main); padding: 12px 16px; border-radius: 8px; border: 1px solid var(--border-light);">
                <div style="flex: 1; min-width: 120px;">
                    <span
                        style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Date
                        / Time</span>
                    <strong id="crs-det-date" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span
                        style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Line
                        No</span>
                    <strong id="crs-det-lineno" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span
                        style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Model
                        Code</span>
                    <strong id="crs-det-model" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span
                        style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Serial</span>
                    <strong id="crs-det-serial" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span
                        style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Inspector</span>
                    <strong id="crs-det-inspector" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
            </div>"""

new_header = """            <!-- Header Info -->
            <div
                style="display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 20px; background: var(--bg-main); padding: 12px 16px; border-radius: 8px; border: 1px solid var(--border-light);">
                <div style="flex: 1; min-width: 120px;">
                    <span style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Date / Time</span>
                    <strong id="crs-det-date" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Model Code</span>
                    <strong id="crs-det-model" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Serial</span>
                    <strong id="crs-det-serial" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Status</span>
                    <div style="margin-top: 4px;">
                        <span id="crs-det-status" class="status-badge status-ok" style="font-size: 13px; padding: 4px 10px;">MATCHED</span>
                    </div>
                </div>
            </div>"""
html = html.replace(old_header, new_header)

# 2. Add Footer & Sticky button
old_actions = """            <div class="modal-actions" style="margin-top: 24px;">
                <button class="btn btn-secondary" onclick="closeCRSDetailsModal()">Close</button>
            </div>"""

new_actions = """            <!-- Meta info -->
            <div style="margin-top: 16px; padding: 12px; background: var(--bg-main); border: 1px solid var(--border-light); border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; font-size: 13px;">
                    <div><span style="color:var(--text-secondary);">Inspector:</span> <strong id="crs-det-inspector" style="color: var(--text-primary);"></strong></div>
                    <div style="text-align: right;"><span style="color:var(--text-secondary);">Line No.:</span> <strong id="crs-det-lineno" style="color: var(--text-primary);"></strong></div>
                </div>
            </div>

            <div class="modal-actions" style="margin-top: 24px; position: sticky; bottom: -20px; background: white; padding: 16px 0; border-top: 1px solid var(--border-light); z-index: 10;">
                <button class="btn btn-secondary" onclick="closeCRSDetailsModal()">Close</button>
            </div>"""

html = html.replace(old_actions, new_actions)

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated CRS modal layout")
