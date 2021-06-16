import psycopg2

conn = psycopg2.connect("dbname=fablab_development host=db user=postgres pass=postgres")

cur = conn.cursor()

cur.execute('select * from users;')
