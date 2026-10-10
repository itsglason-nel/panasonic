# Test Steps

1. Run `scratch\make_test_db.bat` once at a quiet moment.
2. Run `scratch\start_test_server.bat`.
3. Open an INCOGNITO Chrome window at http://127.0.0.1:8090/ (not localhost).
4. Log in with 3 different accounts in 3 tabs (create two test users on the test copy through the admin page).
5. Click every menu item in each tab.
6. Open the print windows and a CSV or PDF export.
7. Open a scoreboard page and check live updates and a `/t/<id>/socket.io/` connection in DevTools.
8. Look for 401 responses or requests without `/t/` that are not static files (each is a call the shim missed).
9. Log out in one tab and check the others.
10. Delete a session cookie in one tab and check it returns to its own login page.
11. Leave a scoreboard open for an hour.
