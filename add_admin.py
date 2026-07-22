import sqlite3
import bcrypt

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

pwd = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')

cursor.execute("INSERT INTO users (full_name, email, phone, password_hash, role) VALUES ('System Administrator', 'admin@smarthire.com', '0771234567', ?, 'admin')", (pwd,))

conn.commit()
print('Admin recreated successfully')
