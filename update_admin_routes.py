import re

path = r'app\routes\admin.py'
with open(path, 'r', encoding='utf-8') as f:
    code = f.read()

# List of functions to remove @admin_required from
targets = [
    'sys_get_lines',
    'get_modules',
    'get_tags',
    'get_areas',
    'get_users',
    'add_schedule',
    'edit_delete_schedule',
    'module_schedules',
    'add_model',
    'delete_model',
    'update_modelref',
    'add_bom',
    'edit_delete_bom',
    'api_shift_detail',
]

for target in targets:
    # Match: @admin_required\ndef target(
    pattern = r'@admin_required\s+(def ' + target + r'\()'
    code = re.sub(pattern, r'\1', code)

# Remove the POST restriction I added to api_shifts
post_restriction = """    if request.method == 'POST':
        if current_user.role == 'operator':
            return jsonify({'error': 'Forbidden - admin access required.'}), 403
        try:"""
original_post = """    if request.method == 'POST':
        try:"""
code = code.replace(post_restriction, original_post)

with open(path, 'w', encoding='utf-8') as f:
    f.write(code)

print("admin.py updated")
