Base commit: 0d7b700

# A1 ROUTES

| URL | Methods | Blueprint | File:Line | Decorators | Returns | Reads User/Session |
|---|---|---|---|---|---|---|
| /admin | ['GET'] | admin_bp | app\routes\admin.py:100 | login_required | Redirect | True / False |
| /admin/api/lines | ['GET'] | admin_bp | app\routes\admin.py:107 | login_required | JSON | False / False |
| /admin/api/schedules | ['GET'] | admin_bp | app\routes\admin.py:117 | login_required | JSON | False / True |
| /admin/api/wip-resolve | ['POST'] | admin_bp | app\routes\admin.py:302 | login_required, admin_required | JSON | False / True |
| /admin/api/next-sequence | ['GET'] | admin_bp | app\routes\admin.py:557 | login_required | JSON | False / False |
| /admin/api/schedule | ['POST'] | admin_bp | app\routes\admin.py:576 | login_required | JSON | False / True |
| /admin/api/schedule/<int:sid> | ['PUT', 'DELETE'] | admin_bp | app\routes\admin.py:637 | login_required | JSON | False / True |
| /admin/api/module-schedules | ['GET', 'PUT', 'DELETE'] | admin_bp | app\routes\admin.py:872 | login_required | JSON | False / False |
| /admin/api/models | ['GET'] | admin_bp | app\routes\admin.py:883 | login_required | JSON | False / True |
| /admin/api/model | ['POST'] | admin_bp | app\routes\admin.py:898 | login_required | JSON | False / False |
| /admin/api/model/<modelcode> | ['DELETE'] | admin_bp | app\routes\admin.py:906 | login_required | JSON | False / True |
| /admin/api/modelref/<modelcode> | ['GET'] | admin_bp | app\routes\admin.py:923 | login_required | JSON | False / False |
| /admin/api/modelref | ['GET'] | admin_bp | app\routes\admin.py:933 | login_required | JSON | False / False |
| /admin/api/modelref/<modelcode> | ['PUT'] | admin_bp | app\routes\admin.py:943 | login_required | JSON | False / True |
| /admin/api/model-gas-target/<modelcode> | ['GET'] | admin_bp | app\routes\admin.py:1052 | login_required | JSON | False / False |
| /admin/api/bom | ['GET'] | admin_bp | app\routes\admin.py:1060 | login_required | JSON | False / False |
| /admin/api/is-production-running | ['GET'] | admin_bp | app\routes\admin.py:1092 | login_required | JSON | False / False |
| /admin/api/bom | ['POST'] | admin_bp | app\routes\admin.py:1097 | login_required | JSON | False / True |
| /admin/api/bom/<int:bid> | ['PUT', 'DELETE'] | admin_bp | app\routes\admin.py:1122 | login_required | JSON | False / True |
| /admin/api/settings | ['GET'] | admin_bp | app\routes\admin.py:1157 | login_required | JSON | False / False |
| /admin/api/settings | ['PUT'] | admin_bp | app\routes\admin.py:1174 | login_required, admin_required | JSON | False / False |
| /admin/api/scoreboard-data | ['GET'] | admin_bp | app\routes\admin.py:1182 | login_required | JSON | False / False |
| /admin/api/reopen-day | ['POST'] | admin_bp | app\routes\admin.py:1231 | login_required, admin_required | JSON | False / True |
| /admin/api/crs-data | ['GET'] | admin_bp | app\routes\admin.py:1264 | login_required | JSON | False / False |
| /admin/api/crs-data/<int:id> | ['PUT', 'DELETE'] | admin_bp | app\routes\admin.py:1350 | login_required, admin_required | JSON | False / True |
| /admin/api/gms-data | ['GET'] | admin_bp | app\routes\admin.py:1371 | login_required | JSON | False / False |
| /admin/api/gms-data/<int:id> | ['PUT', 'DELETE'] | admin_bp | app\routes\admin.py:1403 | login_required, admin_required | JSON | False / True |
| /admin/api/att-data | ['GET'] | admin_bp | app\routes\admin.py:1424 | login_required | JSON | False / False |
| /admin/api/att-data/<int:id> | ['PUT', 'DELETE'] | admin_bp | app\routes\admin.py:1466 | login_required, admin_required | JSON | False / True |
| /admin/print-tag/<serial> | ['GET'] | admin_bp | app\routes\admin.py:1496 | login_required | HTML | False / False |
| /internal/print-tag/<serial> | ['GET'] | admin_bp | app\routes\admin.py:1502 |  | HTML | False / False |
| /admin/api/trigger-pdf/<serial> | ['POST'] | admin_bp | app\routes\admin.py:1512 | login_required | JSON | False / False |
| /admin/api/spamsi-data | ['GET'] | admin_bp | app\routes\admin.py:1696 | login_required | JSON | False / False |
| /admin/api/spamso-data | ['GET'] | admin_bp | app\routes\admin.py:1729 | login_required | JSON | False / False |
| /admin/api/wci-data | ['GET'] | admin_bp | app\routes\admin.py:1762 | login_required | JSON | False / False |
| /admin/api/rit-data | ['GET'] | admin_bp | app\routes\admin.py:1780 | login_required | JSON | False / False |
| /admin/api/pit-data | ['GET'] | admin_bp | app\routes\admin.py:1800 |  | JSON | False / False |
| /admin/api/pit-data/<int:id> | ['PUT', 'DELETE'] | admin_bp | app\routes\admin.py:1853 |  | JSON | False / True |
| /admin/api/fit-data | ['GET'] | admin_bp | app\routes\admin.py:1875 | login_required | JSON | False / False |
| /admin/api/prod-tag-tracker | ['GET'] | admin_bp | app\routes\admin.py:1895 | login_required | JSON | False / True |
| /sys/api/lines | ['GET'] | admin_bp | app\routes\admin.py:2002 | login_required | JSON | False / False |
| /sys/api/line | ['POST'] | admin_bp | app\routes\admin.py:2016 | login_required, admin_required | JSON | False / True |
| /sys/api/line/<int:lid> | ['PUT', 'DELETE'] | admin_bp | app\routes\admin.py:2036 | login_required, admin_required | JSON | False / True |
| /api/lines/active | ['GET'] | admin_bp | app\routes\admin.py:2056 | login_required | JSON | False / False |
| /sys/api/modules | ['GET'] | admin_bp | app\routes\admin.py:2070 | login_required | JSON | False / False |
| /sys/api/module | ['POST'] | admin_bp | app\routes\admin.py:2083 | login_required, admin_required | JSON | False / True |
| /sys/api/module/<int:mid> | ['PUT', 'DELETE'] | admin_bp | app\routes\admin.py:2102 | login_required, admin_required | JSON | False / True |
| /api/modules/active | ['GET'] | admin_bp | app\routes\admin.py:2122 | login_required | JSON | False / False |
| /sys/api/tags | ['GET'] | admin_bp | app\routes\admin.py:2131 | login_required | JSON | False / False |
| /sys/api/tag | ['POST'] | admin_bp | app\routes\admin.py:2144 | login_required, admin_required | JSON | False / True |
| /sys/api/tag/<int:tid> | ['PUT', 'DELETE'] | admin_bp | app\routes\admin.py:2163 | login_required, admin_required | JSON | False / True |
| /api/tags/active | ['GET'] | admin_bp | app\routes\admin.py:2183 | login_required | JSON | False / False |
| /sys/api/areas | ['GET'] | admin_bp | app\routes\admin.py:2192 | login_required | JSON | False / False |
| /sys/api/area | ['POST'] | admin_bp | app\routes\admin.py:2206 | login_required, admin_required | JSON | False / True |
| /sys/api/area/<int:area_id> | ['PUT', 'DELETE'] | admin_bp | app\routes\admin.py:2227 | login_required, admin_required | JSON | False / True |
| /api/areas/active | ['GET'] | admin_bp | app\routes\admin.py:2268 | login_required | JSON | False / False |
| /sys/api/users | ['GET'] | admin_bp | app\routes\admin.py:2277 | login_required | JSON | False / False |
| /sys/api/user | ['POST'] | admin_bp | app\routes\admin.py:2292 | login_required, admin_required | JSON | False / True |
| /sys/api/user/<int:uid> | ['PUT', 'DELETE'] | admin_bp | app\routes\admin.py:2319 | login_required, admin_required | JSON | True / True |
| /admin/print-specific-qc | ['GET'] | admin_bp | app\routes\admin.py:2371 | login_required | HTML | False / False |
| /admin/api/linestat-viewer | ['GET'] | admin_bp | app\routes\admin.py:2465 | login_required | JSON | False / False |
| /admin/api/conveyor/status/<line_code> | ['GET'] | admin_bp | app\routes\admin.py:2551 | login_required | JSON | False / False |
| /admin/api/conveyor/action | ['POST'] | admin_bp | app\routes\admin.py:2585 | login_required, admin_required | JSON | False / True |
| /admin/api/shifts | ['GET', 'POST'] | admin_bp | app\routes\admin.py:2736 | login_required | JSON | False / True |
| /admin/api/shifts/<int:shift_id> | ['PUT', 'DELETE'] | admin_bp | app\routes\admin.py:2774 | login_required | JSON | False / True |
| /admin/api/transfer-slips/available-dates | ['GET'] | admin_bp | app\routes\admin.py:2817 | login_required | JSON | False / False |
| /admin/api/transfer-slips/available-params | ['GET'] | admin_bp | app\routes\admin.py:2832 | login_required | JSON | False / False |
| /admin/api/transfer-slips | ['GET'] | admin_bp | app\routes\admin.py:2871 | login_required | JSON | False / False |
| /admin/api/transfer-slips | ['POST'] | admin_bp | app\routes\admin.py:2917 | login_required | JSON | False / True |
| /admin/api/trigger-transfer-csv/<int:slip_id> | ['POST'] | admin_bp | app\routes\admin.py:2998 | login_required | JSON | False / False |
| /admin/print-transfer-slip/<int:slip_id> | ['GET'] | admin_bp | app\routes\admin.py:3010 | login_required | HTML | False / False |
| /admin/api/qc-print-units | ['GET'] | admin_bp | app\routes\admin.py:3075 | login_required | JSON | False / False |
| /admin/print-qc-report | ['GET'] | admin_bp | app\routes\admin.py:3112 | login_required | HTML | False / False |
| /unit/<serial> | ['GET'] | api_bp | app\routes\api.py:39 | login_required | JSON | False / False |
| /bom/<model_number>/<module_code> | ['GET'] | api_bp | app\routes\api.py:73 | login_required | JSON | False / False |
| /serialref/<modelcode> | ['GET'] | api_bp | app\routes\api.py:91 | login_required | JSON | False / False |
| /schedule/<int:lid>/<date_str> | ['GET'] | api_bp | app\routes\api.py:111 | login_required | JSON | False / False |
| /scoreboard/<int:line_id> | ['GET'] | api_bp | app\routes\api.py:144 | login_required | JSON | False / False |
| /station/<station_code>/submit | ['POST'] | api_bp | app\routes\api.py:181 | login_required | JSON | True / True |
| /weight/current | ['GET'] | api_bp | app\routes\api.py:362 | login_required | JSON | False / False |
| / | ['GET'] | auth_bp | app\routes\auth.py:46 |  | Redirect | True / False |
| /auth/login | ['GET', 'POST'] | auth_bp | app\routes\auth.py:53 |  | Redirect | True / True |
| /dashboard | ['GET'] | auth_bp | app\routes\auth.py:117 | login_required | Redirect | False / False |
| /auth/logout | ['GET'] | auth_bp | app\routes\auth.py:123 | login_required | Redirect | False / True |
| /auth/change-password | ['POST'] | auth_bp | app\routes\auth.py:132 | login_required | JSON | True / True |
| /scoreboard | ['GET'] | scoreboard_bp | app\routes\scoreboard.py:23 |  | HTML | False / False |
| /scoreboard/line/<line_no> | ['GET'] | scoreboard_bp | app\routes\scoreboard.py:29 |  | HTML | False / False |
| /api/scoreboard/data | ['GET'] | scoreboard_bp | app\routes\scoreboard.py:35 |  | JSON | False / False |
| /api/scoreboard/logs | ['GET'] | scoreboard_bp | app\routes\scoreboard.py:162 |  | JSON | False / False |
| /api/scoreboard/models | ['GET'] | scoreboard_bp | app\routes\scoreboard.py:250 |  | JSON | False / True |

Total routes found: 90

**Reconciliation**: Searched .py files in app/routes using AST parsing. (Positive control: /auth/login found).