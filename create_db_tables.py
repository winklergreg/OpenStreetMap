import sqlite3

path = "/Users/GW/Documents/Udacity/Data_Wrangling/project/"
file = path + "buffalo.db"

conn = sqlite3.connect(file)
curs = conn.cursor()

conn.execute("""
	CREATE TABLE Node_Tags(
	Uid INTEGER PRIMARY KEY AUTOINCREMENT,
	Id INTEGER NOT NULL,
	Key NVARCHAR(40),
	Value NVARCHAR(300),
	Type NVARCHAR(25),
	FOREIGN KEY (Id) REFERENCES Nodes (Id)
);""")


conn.execute("""
	CREATE TABLE Way_Tags(
	Uid INTEGER PRIMARY KEY AUTOINCREMENT,
	Id INTEGER NOT NULL,
	Key NVARCHAR(40),
	Value NVARCHAR(300),
	Type NVARCHAR(25),
	FOREIGN KEY (Id) REFERENCES Ways (Id)
);""")

conn.commit()
conn.close()