from server.database import fetch_one

print(fetch_one("SELECT COUNT(*) AS c FROM users"))
