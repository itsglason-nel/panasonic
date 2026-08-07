with open('app/routes/admin.py', 'r') as f:
    code = f.read()

code = code.replace("\\'remarks\\': (r.remarks or \\'\\') + (\\' [Past NG History]\\' if ng.get(r.serial) else \\'\\')", 
                    "'remarks': (r.remarks or '') + (' [Past NG History]' if ng.get(r.serial) else '')")

with open('app/routes/admin.py', 'w') as f:
    f.write(code)
