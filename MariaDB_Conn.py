import mysql.connector
import os

pw = os.getenv("MARIADB_PW")

config = {
  'user': 'root',
  'password': 'tylerwashere',
  'host': '0.0.0.0',
  'database': 'annotationsDB',
  'raise_on_warnings': True
}

class MariaDB_Conn():

  def __init__(self):
    try:
      self.cnx = mysql.connector.connect(**config)
      self.cursor = self.cnx.cursor
      print("Database connection established")

    except mysql.connector.Error as err:
      self.cnx = None
      print("Database connection failed.", err)
  

  
conn = MariaDB_Conn()