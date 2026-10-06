path = r'app\templates\admin\components\modals.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update the header of SPAMSI
old_header = """            <!-- Header Info -->
            <div
                style="display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 20px; background: var(--bg-main); padding: 12px 16px; border-radius: 8px; border: 1px solid var(--border-light);">
                <div style="flex: 1; min-width: 120px;">
                    <span
                        style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Date
                        / Time</span>
                    <strong id="spamsi-det-date" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span
                        style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Line
                        No</span>
                    <strong id="spamsi-det-lineno" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span
                        style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Model
                        Code</span>
                    <strong id="spamsi-det-model" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span
                        style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Serial</span>
                    <strong id="spamsi-det-serial" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span
                        style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Indoor
                        Serial</span>
                    <strong id="spamsi-det-inserial" style="font-size: 14px; color: var(--accent-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span
                        style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Inspector</span>
                    <strong id="spamsi-det-inspector" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span
                        style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Arrival Date</span>
                    <strong id="spamsi-det-arvdate" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span
                        style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Mfg Date</span>
                    <strong id="spamsi-det-mfgdate" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
            </div>"""

new_header = """            <!-- Header Info -->
            <div
                style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; background: var(--bg-main); padding: 12px 16px; border-radius: 8px; border: 1px solid var(--border-light);">
                <div style="flex: 1; min-width: 120px;">
                    <span style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Date / Time</span>
                    <strong id="spamsi-det-date" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Model Code</span>
                    <strong id="spamsi-det-model" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Serial</span>
                    <strong id="spamsi-det-serial" style="font-size: 14px; color: var(--text-primary);"></strong>
                </div>
                <div style="flex: 1; min-width: 120px;">
                    <span style="display:block; font-size: 11px; color: #333; text-transform: uppercase; font-weight: 600;">Indoor Serial</span>
                    <strong id="spamsi-det-inserial" style="font-size: 14px; color: var(--accent-primary);"></strong>
                </div>
            </div>"""

html = html.replace(old_header, new_header)

# 2. Add Meta info and Sticky Close button for SPAMSI
# Need to find the end of the SPAMSI modal body.
old_footer = """            </div>
        </div>
    </div>
</div>

<!-- SPAMSO Details Modal -->"""

new_footer = """            </div>

            <!-- Meta info -->
            <div style="margin-top: 16px; padding: 12px; background: var(--bg-main); border: 1px solid var(--border-light); border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; font-size: 13px;">
                    <div style="display: flex; gap: 24px;">
                        <div><span style="color:var(--text-secondary);">Inspector:</span> <strong id="spamsi-det-inspector" style="color: var(--text-primary);"></strong></div>
                        <div><span style="color:var(--text-secondary);">Arrival Date:</span> <strong id="spamsi-det-arvdate" style="color: var(--text-primary);"></strong></div>
                        <div><span style="color:var(--text-secondary);">Mfg Date:</span> <strong id="spamsi-det-mfgdate" style="color: var(--text-primary);"></strong></div>
                    </div>
                    <div style="text-align: right;"><span style="color:var(--text-secondary);">Line No.:</span> <strong id="spamsi-det-lineno" style="color: var(--text-primary);"></strong></div>
                </div>
            </div>

            <div class="modal-actions" style="margin-top: 24px; position: sticky; bottom: 0; background: var(--bg-main); padding: 16px 0 0 0; box-shadow: 0 -10px 10px -10px var(--bg-main), 0 20px 0 20px var(--bg-main); z-index: 10;">
                <button class="btn btn-secondary" onclick="closeSPAMSIDetailsModal()">Close</button>
            </div>
        </div>
    </div>
</div>

<!-- SPAMSO Details Modal -->"""

html = html.replace(old_footer, new_footer)

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated SPAMSI layout in modals.html")
