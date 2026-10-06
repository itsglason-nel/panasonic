path = r'app\templates\admin.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Work Schedule action-btns
ws_hidden = """                        <div class="action-btns">
                            {% if current_user.role != 'operator' %}
                            <button class="btn btn-primary" onclick="openScheduleModal('add')">Add</button>
                            <button class="btn btn-secondary" onclick="openScheduleModal('edit')">Edit</button>
                            <button class="btn btn-danger" onclick="deleteSchedule()">Delete</button>
                            <button class="btn btn-secondary" onclick="openModuleScheduleModal()">Module
                                WorkSched</button>
                            {% endif %}
                        </div>"""

ws_unhidden = """                        <div class="action-btns">
                            <button class="btn btn-primary" onclick="openScheduleModal('add')">Add</button>
                            <button class="btn btn-secondary" onclick="openScheduleModal('edit')">Edit</button>
                            <button class="btn btn-danger" onclick="deleteSchedule()">Delete</button>
                            <button class="btn btn-secondary" onclick="openModuleScheduleModal()">Module
                                WorkSched</button>
                        </div>"""
html = html.replace(ws_hidden, ws_unhidden)

# 2. Part Reference bom-action-btns
bom_hidden = """                            <div class="action-btns" id="bom-action-btns">
                                {% if current_user.role != 'operator' %}
                                <button class="btn btn-primary" onclick="openBomModal('add')">Add Part</button>
                                <button class="btn btn-secondary" onclick="openBomModal('edit')">Edit</button>
                                <button class="btn btn-danger" onclick="deleteBom()">Delete</button>
                                <button class="btn btn-danger" onclick="deleteEntireModel()"
                                    style="margin-left: auto;">Delete Model</button>
                                {% endif %}
                            </div>"""

bom_unhidden = """                            <div class="action-btns" id="bom-action-btns">
                                <button class="btn btn-primary" onclick="openBomModal('add')">Add Part</button>
                                <button class="btn btn-secondary" onclick="openBomModal('edit')">Edit</button>
                                <button class="btn btn-danger" onclick="deleteBom()">Delete</button>
                                <button class="btn btn-danger" onclick="deleteEntireModel()"
                                    style="margin-left: auto;">Delete Model</button>
                            </div>"""
html = html.replace(bom_hidden, bom_unhidden)

# 3. Shifts edit button
shift_hidden = """                            <div style="display: flex; gap: 8px; align-items: center;">
                            {% if current_user.role != 'operator' %}
                            <button class="btn btn-secondary" disabled="" id="shift-edit-btn"
                                onclick="openShiftModal('edit')">Edit</button>
                            {% endif %}"""

shift_unhidden = """                            <div style="display: flex; gap: 8px; align-items: center;">
                            <button class="btn btn-secondary" disabled="" id="shift-edit-btn"
                                onclick="openShiftModal('edit')">Edit</button>"""
html = html.replace(shift_hidden, shift_unhidden)

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print("admin.html updated")
