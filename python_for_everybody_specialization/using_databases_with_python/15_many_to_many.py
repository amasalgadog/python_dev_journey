import sqlite3

conn = sqlite3.connect('many-2-many.sqlite')
cur = conn.cursor()

cur.execute('DROP TABLE IF EXISTS Person')
cur.execute('''
            CREATE TABLE Person (
            id INTEGER NOT NULL UNIQUE,
            name TEXT, email TEXT,
            PRIMARY KEY (id AUTOINCREMENT)
            )''')

cur.execute('DROP TABLE IF EXISTS Book')
cur.execute('''
            CREATE TABLE Book (
            id INTEGER NOT NULL UNIQUE,
            title TEXT,
            PRIMARY KEY (id AUTOINCREMENT)
            )''')

# Author table is a junction table consisting in 2 foreign keys pointing to Book and Person
cur.execute('DROP TABLE IF EXISTS Author')
cur.execute('''
            CREATE TABLE Author (
            person_id INTEGER,
            book_id INTEGER,
            PRIMARY KEY (person_id, book_id)
            )''')
# this PRIMARY KEY operation with two fields (columns) is a combination that force it to be unique combination

conn.commit()

cur.execute("INSERT OR IGNORE INTO Person (name, email) VALUES ('J. R. R. Tolkien','jrrr@tolkien.com')")
cur.execute("INSERT OR IGNORE INTO Person (name, email) VALUES ('Christopher Tolkien','chris@tolkien.com')")
cur.execute("INSERT OR IGNORE INTO Person (name, email) VALUES ('Marc André Meyers','marc.meyers@biomaterials.com')")
cur.execute("INSERT OR IGNORE INTO Person (name, email) VALUES ('Po-Yu Chen','po-yu.chen@biomaterials.com')")

cur.execute("INSERT OR IGNORE INTO Book (title) VALUES ('The Lords of the Rings: The Fellowship of the Ring')")
cur.execute("INSERT OR IGNORE INTO Book (title) VALUES ('The Lords of the Rings: The Two Towers')")
cur.execute("INSERT OR IGNORE INTO Book (title) VALUES ('The Lords of the Rings: The Return of the King')")
cur.execute("INSERT OR IGNORE INTO Book (title) VALUES ('The Silmarillion')")
cur.execute("INSERT OR IGNORE INTO Book (title) VALUES ('Biological Materials Science: Biological Materials, Bioinspired Materials, and Biomaterials')")

cur.execute("INSERT OR IGNORE INTO Author (person_id, book_id) VALUES (1, 1)")
cur.execute("INSERT OR IGNORE INTO Author (person_id, book_id) VALUES (1, 2)")
cur.execute("INSERT OR IGNORE INTO Author (person_id, book_id) VALUES (1, 3)")
cur.execute("INSERT OR IGNORE INTO Author (person_id, book_id) VALUES (1, 4)")
cur.execute("INSERT OR IGNORE INTO Author (person_id, book_id) VALUES (2, 4)")
cur.execute("INSERT OR IGNORE INTO Author (person_id, book_id) VALUES (3, 5)")
cur.execute("INSERT OR IGNORE INTO Author (person_id, book_id) VALUES (4, 5)")

conn.commit()

cur.execute("SELECT Book.title, Person.name FROM Author JOIN Book JOIN Person ON Author.person_id=Person.id AND Author.book_id=Book.id ORDER BY Book.title ASC, Person.name DESC")
result = cur.fetchall()

for item in result:
    print(item)

cur.close()
conn.close()