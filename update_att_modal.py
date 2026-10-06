path = r'app\templates\admin\components\modals.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Header Info replacement for ATT
old_att_header = """            <!-- Header Info -->
            <div
                style="display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 20px; background: var(--bg-main); padding: 12px 16px; border-radius: 8px; border: 1px solid var(--border-light);">
                <div style="flex: 1; min-width: 120px;">
                    <span
                        style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Date
                        / Time</span>
                    <strong id="att-det-date" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span
                        style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Model
                        Code</span>
                    <strong id="att-det-model" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span
                        style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Serial</span>
                    <strong id="att-det-serial" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span
                        style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Line
                        No</span>
                    <strong id="att-det-lineno" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span
                        style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Inspector</span>
                    <strong id="att-det-inspector" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
            </div>"""

new_att_header = """            <!-- Header Info -->
            <div
                style="display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 20px; background: var(--bg-main); padding: 12px 16px; border-radius: 8px; border: 1px solid var(--border-light);">
                <div style="flex: 1; min-width: 120px;">
                    <span style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Date / Time</span>
                    <strong id="att-det-date" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Model Code</span>
                    <strong id="att-det-model" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Serial</span>
                    <strong id="att-det-serial" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Status</span>
                    <div style="margin-top: 4px;" id="att-det-top-status">
                    </div>
                </div>
            </div>"""

html = html.replace(old_att_header, new_att_header)

# 2. Replace Inspection Statuses H4
old_h4_att1 = """                    <h4
                        style="margin: 0 0 12px 0; font-size: 13px; color: #333; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid var(--border-light); padding-bottom: 8px;">
                        Inspection Statuses</h4>"""
new_h4_att1 = """                    <h4
                        style="margin: 0 0 12px 0; font-size: 13px; color: #333; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid var(--border-light); padding-bottom: 8px; height: 38px; display: flex; align-items: center; justify-content: center; text-align: center;">
                        Inspection Statuses</h4>"""
html = html.replace(old_h4_att1, new_h4_att1)

# 3. Replace Brazzer Operators H4
old_h4_att2 = """                    <h4
                        style="margin: 0 0 12px 0; font-size: 13px; color: #333; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid var(--border-light); padding-bottom: 8px;">
                        Brazzer Operators</h4>"""
new_h4_att2 = """                    <h4
                        style="margin: 0 0 12px 0; font-size: 13px; color: #333; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid var(--border-light); padding-bottom: 8px; height: 38px; display: flex; align-items: center; justify-content: center; text-align: center;">
                        Brazzer Operators</h4>"""
html = html.replace(old_h4_att2, new_h4_att2)


# 4. Insert Footer before the modal actions (close button)
# We need to find the close button for ATT details
old_actions_att = """            <div class="modal-actions" style="margin-top: 24px;">
                <button class="btn btn-secondary" onclick="closeATTDetailsModal()">Close</button>
            </div>"""

new_actions_att = """            <!-- Meta info -->
            <div style="margin-top: 16px; padding: 12px; background: var(--bg-main); border: 1px solid var(--border-light); border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; font-size: 13px;">
                    <div><span style="color:var(--text-secondary);">Inspector:</span> <strong id="att-det-inspector" style="color: var(--text-primary);"></strong></div>
                    <div style="text-align: right;"><span style="color:var(--text-secondary);">Line No.:</span> <strong id="att-det-lineno" style="color: var(--text-primary);"></strong></div>
                </div>
            </div>

            <div class="modal-actions" style="margin-top: 24px;">
                <button class="btn btn-secondary" onclick="closeATTDetailsModal()">Close</button>
            </div>"""

html = html.replace(old_actions_att, new_actions_att)


with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated ATT modal layout in modals.html")
