import psycopg2
import os
from config import *
import datetime


dir_path = os.path.dirname(os.path.realpath(__file__))




# def charge_1month(user_id):
user_id = '5871240110'
con = psycopg2.connect(host=PGHOST, user=PGUSER, password=PGPASSWORD, database=PGDATABASE)
cursor = con.cursor()
# cursor.execute('''CREATE TABLE IF NOT EXISTS customers
#             (user_id BIGINT NOT NULL UNIQUE,
#             authority BIGINT,
#             ref_id BIGINT,
#             status_pay INT,
#             purchase_time TIMESTAMP,
#             remaining_time TIMESTAMP,
#             usage BIGINT);''')
current_datetime = f'{datetime.date.today().year}-{datetime.date.today().month}-{datetime.date.today().day} 00:00:00+00:00'
current_datetime = datetime.datetime.strptime(current_datetime, "%Y-%m-%d %H:%M:%S%z")
remaining_time_str =f'{datetime.date.today().year}-{datetime.date.today().month+1}-{datetime.date.today().day+1} 00:00:00+00:00'
remaining_time = datetime.datetime.strptime(remaining_time_str, "%Y-%m-%d %H:%M:%S%z")
#
insert_query = (f'''
UPDATE customers
SET purchase_time = %s,
remaining_time = %s
WHERE user_id = %s;
''')
cursor.execute(insert_query, (current_datetime,remaining_time,user_id))

# insert_query = 'select purchase_time from customers where user_id = %s;'
# cursor.execute(insert_query,(user_id,))

insert_query = "SELECT * FROM customers where user_id = %s "
# cursor.execute(insert_query,(user_id,))
# cursor.execute('drop table customers;')
# r = cursor.fetchall()
con.commit()
cursor.close()
con.close()
# print(r)


