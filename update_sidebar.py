"""Update admin.html for operator role additions."""
import os

path = r'app\templates\admin.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Management section visibility
html = html.replace("{% if current_user.role != 'operator' %}\n                <!-- Management -->", "<!-- Management -->")
# The closing endif for Management was placed right before SFIS Stations
html = html.replace("{% endif %}\n                <!-- SFIS Stations -->", "<!-- SFIS Stations -->")

# 2. Revert active states for nav
html = html.replace(
    '<button class="sidebar-item{% if current_user.role != \'operator\' %} active{% endif %}" data-panel="worksched" id="nav-worksched">',
    '<button class="sidebar-item active" data-panel="worksched" id="nav-worksched">'
)
html = html.replace(
    '<button class="sidebar-item{% if current_user.role == \'operator\' %} active{% endif %}" data-panel="crs" id="nav-crs">',
    '<button class="sidebar-item" data-panel="crs" id="nav-crs">'
)

# 3. Quality Control section visibility
html = html.replace("{% if current_user.role != 'operator' %}\n                <!-- Quality Control -->", "<!-- Quality Control -->")
# The closing endif for Quality Control was placed right before System Configuration
html = html.replace("{% endif %}\n                {% if current_user.role != 'operator' %}\n                <!-- System Configuration -->", "<!-- System Configuration -->")

# Wait, previously I had two `endif` and one `if`?
# Let's check exactly what the previous string replace did.
# It did:
# old_qc = '                <!-- Quality Control -->\n                <div class="sidebar-separator">Quality Control</div>'
# new_qc = '                {% if current_user.role != \'operator\' %}\n                <!-- Quality Control -->\n                <div class="sidebar-separator">Quality Control</div>'
#
# old_sys = '                <!-- System Configuration -->\n                <div class="sidebar-separator">System Configuration</div>'
# new_sys = '                {% endif %}\n                {% if current_user.role != \'operator\' %}\n                <!-- System Configuration -->\n                <div class="sidebar-separator">System Configuration</div>'
#
# old_nav_close = '            </nav>'
# new_nav_close = '                {% endif %}\n            </nav>'
#
# So the block looks like:
# {% endif %}
# {% if current_user.role != 'operator' %}
# <!-- System Configuration -->
# ...
# {% endif %}
# </nav>

# Okay, I will fix the QC and System Config replacements differently using regex or exact block replacement.
