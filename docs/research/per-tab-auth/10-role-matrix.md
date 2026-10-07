Base commit: 0d7b700

# A10 ROLES

Roles that exist: [PENDING OWNER RESULT]


## Matrix of Route x Role (What code allows today)
| Route | Permitted Roles (Based on Decorators / Body Checks) |
|---|---|
| /admin (['GET']) | Checked in body |
| /admin/api/lines (['GET']) | Logged In |
| /admin/api/schedules (['GET']) | Logged In |
| /admin/api/wip-resolve (['POST']) | Logged In |
| /admin/api/next-sequence (['GET']) | Logged In |
| /admin/api/schedule (['POST']) | Logged In |
| /admin/api/schedule/<int:sid> (['PUT', 'DELETE']) | Logged In |
| /admin/api/module-schedules (['GET', 'PUT', 'DELETE']) | Logged In |
| /admin/api/models (['GET']) | Logged In |
| /admin/api/model (['POST']) | Logged In |
| /admin/api/model/<modelcode> (['DELETE']) | Logged In |
| /admin/api/modelref/<modelcode> (['GET']) | Logged In |
| /admin/api/modelref (['GET']) | Logged In |
| /admin/api/modelref/<modelcode> (['PUT']) | Logged In |
| /admin/api/model-gas-target/<modelcode> (['GET']) | Logged In |
| /admin/api/bom (['GET']) | Logged In |
| /admin/api/is-production-running (['GET']) | Logged In |
| /admin/api/bom (['POST']) | Logged In |
| /admin/api/bom/<int:bid> (['PUT', 'DELETE']) | Logged In |
| /admin/api/settings (['GET']) | Logged In |
| /admin/api/settings (['PUT']) | Logged In |
| /admin/api/scoreboard-data (['GET']) | Logged In |
| /admin/api/reopen-day (['POST']) | Logged In |
| /admin/api/crs-data (['GET']) | Logged In |
| /admin/api/crs-data/<int:id> (['PUT', 'DELETE']) | Logged In |
| /admin/api/gms-data (['GET']) | Logged In |
| /admin/api/gms-data/<int:id> (['PUT', 'DELETE']) | Logged In |
| /admin/api/att-data (['GET']) | Logged In |
| /admin/api/att-data/<int:id> (['PUT', 'DELETE']) | Logged In |
| /admin/print-tag/<serial> (['GET']) | Logged In |
| /internal/print-tag/<serial> (['GET']) | All (No Check) |
| /admin/api/trigger-pdf/<serial> (['POST']) | Logged In |
| /admin/api/spamsi-data (['GET']) | Logged In |
| /admin/api/spamso-data (['GET']) | Logged In |
| /admin/api/wci-data (['GET']) | Logged In |
| /admin/api/rit-data (['GET']) | Logged In |
| /admin/api/pit-data (['GET']) | All (No Check) |
| /admin/api/pit-data/<int:id> (['PUT', 'DELETE']) | All (No Check) |
| /admin/api/fit-data (['GET']) | Logged In |
| /admin/api/prod-tag-tracker (['GET']) | Logged In |
| /sys/api/lines (['GET']) | Logged In |
| /sys/api/line (['POST']) | Logged In |
| /sys/api/line/<int:lid> (['PUT', 'DELETE']) | Logged In |
| /api/lines/active (['GET']) | Logged In |
| /sys/api/modules (['GET']) | Logged In |
| /sys/api/module (['POST']) | Logged In |
| /sys/api/module/<int:mid> (['PUT', 'DELETE']) | Logged In |
| /api/modules/active (['GET']) | Logged In |
| /sys/api/tags (['GET']) | Logged In |
| /sys/api/tag (['POST']) | Logged In |
| /sys/api/tag/<int:tid> (['PUT', 'DELETE']) | Logged In |
| /api/tags/active (['GET']) | Logged In |
| /sys/api/areas (['GET']) | Logged In |
| /sys/api/area (['POST']) | Logged In |
| /sys/api/area/<int:area_id> (['PUT', 'DELETE']) | Logged In |
| /api/areas/active (['GET']) | Logged In |
| /sys/api/users (['GET']) | Logged In |
| /sys/api/user (['POST']) | Logged In |
| /sys/api/user/<int:uid> (['PUT', 'DELETE']) | Logged In |
| /admin/print-specific-qc (['GET']) | Logged In |
| /admin/api/linestat-viewer (['GET']) | Logged In |
| /admin/api/conveyor/status/<line_code> (['GET']) | Logged In |
| /admin/api/conveyor/action (['POST']) | Logged In |
| /admin/api/shifts (['GET', 'POST']) | Logged In |
| /admin/api/shifts/<int:shift_id> (['PUT', 'DELETE']) | Logged In |
| /admin/api/transfer-slips/available-dates (['GET']) | Logged In |
| /admin/api/transfer-slips/available-params (['GET']) | Logged In |
| /admin/api/transfer-slips (['GET']) | Logged In |
| /admin/api/transfer-slips (['POST']) | Logged In |
| /admin/api/trigger-transfer-csv/<int:slip_id> (['POST']) | Logged In |
| /admin/print-transfer-slip/<int:slip_id> (['GET']) | Logged In |
| /admin/api/qc-print-units (['GET']) | Logged In |
| /admin/print-qc-report (['GET']) | Logged In |
| /unit/<serial> (['GET']) | Logged In |
| /bom/<model_number>/<module_code> (['GET']) | Logged In |
| /serialref/<modelcode> (['GET']) | Logged In |
| /schedule/<int:lid>/<date_str> (['GET']) | Logged In |
| /scoreboard/<int:line_id> (['GET']) | Logged In |
| /station/<station_code>/submit (['POST']) | Logged In |
| /weight/current (['GET']) | Logged In |
| / (['GET']) | All (No Check) |
| /auth/login (['GET', 'POST']) | All (No Check) |
| /dashboard (['GET']) | Logged In |
| /auth/logout (['GET']) | Logged In |
| /auth/change-password (['POST']) | Logged In |
| /scoreboard (['GET']) | All (No Check) |
| /scoreboard/line/<line_no> (['GET']) | All (No Check) |
| /api/scoreboard/data (['GET']) | All (No Check) |
| /api/scoreboard/logs (['GET']) | All (No Check) |
| /api/scoreboard/models (['GET']) | All (No Check) |

*Hidden UI mapping pending A2 template analysis.*