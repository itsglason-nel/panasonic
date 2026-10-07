Base commit: 0d7b700

# A2 TEMPLATES

## Render Template Calls

- **error.html** (in app\__init__.py:153)
  - kwargs: {'error_code': "'404'", 'error_title': "'Not Found'", 'error_desc': "'The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.'"}
- **error.html** (in app\__init__.py:157)
  - kwargs: {'error_code': "'403'", 'error_title': "'Forbidden'", 'error_desc': '"You don\'t have the permission to access the requested resource. It is either read-protected or not readable by the server."'}
- **error.html** (in app\__init__.py:162)
  - kwargs: {'error_code': "'500'", 'error_title': "'Internal Server Error'", 'error_desc': "'The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.'"}
- **admin.html** (in app\routes\admin.py:103)
  - kwargs: {}
- **admin/print_tag.html** (in app\routes\admin.py:1499)
  - kwargs: {'unit': 'unit_data'}
- **admin/print_tag.html** (in app\routes\admin.py:1508)
  - kwargs: {'unit': 'unit_data'}
- **admin/qc_report_print.html** (in app\routes\admin.py:2457)
  - kwargs: {'units_data': 'units_data', 'current_time': 'datetime.now()'}
- **admin/print_transfer_slip.html** (in app\routes\admin.py:3060)
  - kwargs: {'slip': 'slip', 'pages': 'pages', 'total_pages': 'total_pages', 'print_date': 'print_date', 'finished_date': 'finished_date', 'start_time': 'start_time', 'end_time': 'end_time'}
- **admin/qc_report_print.html** (in app\routes\admin.py:3168)
  - kwargs: {'units_data': 'units_data', 'current_time': 'datetime.now()'}
- **login.html** (in app\routes\auth.py:77)
  - kwargs: {}
- **login.html** (in app\routes\auth.py:113)
  - kwargs: {}
- **scoreboard/all_lines.html** (in app\routes\scoreboard.py:26)
  - kwargs: {'lines': 'lines'}
- **scoreboard/line.html** (in app\routes\scoreboard.py:32)
  - kwargs: {'line': 'line'}

## Template Features

| Template | Uses | Loops | Ifs | |safe | |tojson | Inline JS w/ Jinja | Forms | CSRF |
|---|---|---|---|---|---|---|---|---|
| admin.html | current_user, session, g | 0 | 22 | 0 | 0 | True | 0 | False |
| base.html | current_user, request, get_flashed_messages | 1 | 8 | 0 | 0 | True | 0 | False |
| dashboard.html | current_user | 0 | 0 | 0 | 0 | False | 0 | False |
| error.html |  | 0 | 0 | 0 | 0 | False | 0 | False |
| login.html | session, get_flashed_messages | 1 | 1 | 0 | 0 | True | 1 | True |
| admin/print_qc_report.html |  | 2 | 7 | 0 | 0 | False | 0 | False |
| admin/print_tag.html | g | 0 | 2 | 0 | 0 | True | 0 | False |
| admin/print_transfer_slip.html |  | 4 | 5 | 0 | 0 | False | 0 | False |
| admin/qc_report_print.html |  | 4 | 23 | 0 | 0 | False | 0 | False |
| admin/components/modals.html | current_user, session, g | 0 | 0 | 0 | 0 | False | 0 | False |
| admin/components/scripts.html | current_user, session, g | 0 | 0 | 0 | 0 | True | 0 | False |
| scoreboard/all_lines.html |  | 1 | 0 | 0 | 0 | True | 0 | False |
| scoreboard/line.html | g | 0 | 0 | 0 | 0 | True | 0 | False |

**Reconciliation**:
- Total templates in folder: 13
- Templates used by render_template: 8
- Unused templates: 5