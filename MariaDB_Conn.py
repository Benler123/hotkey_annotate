import mysql.connector
import os
from datetime import datetime

pw = os.getenv("MARIADB_PW")

config = {
  'user': 'root',
  'password': pw,
  'host': '0.0.0.0',
  'database': 'annotationsDB',
  'raise_on_warnings': True
}

class MariaDB_Conn():

  def __init__(self):
    try:
      self.cnx = mysql.connector.connect(**config)
      self.cursor = self.cnx.cursor()
      print("Database connection established")

    except mysql.connector.Error as err:
      self.cnx = None
      print("Database connection failed.", err)

  def __del__(self):
    if self.cnx:
      self.cnx.close()
      print("Database connection closed")

  def execute_query(self, query, parameters):
    result = None
    try:
      result = self.cursor.execute(query, parameters)
      self.cnx.commit()
    except mysql.connector.Error as err:
      print("Amending DB failed with error ", err)
    return result
  

  def add_sign(self, sign):
    query = "INSERT INTO sign_table (Sign, Complete) Values (%s, false)"
    parameters = (sign,)
    self.execute_query(query, parameters)

  def add_annotation(self, full_annotation: list):
    curent_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    query = "Insert INTO annotation_table (sign, fileName, user, sessionId, dateTime, good, unrecognizable, wrong_variant, flag) Values (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    parameters = (full_annotation[0], full_annotation[1], "not implemented", "not implemented", curent_time, full_annotation[2]=='x', full_annotation[3]=='x', full_annotation[4]=='x', full_annotation[5]=='x')
    self.execute_query(query, parameters)


  def get_sign(self, sign):
    query = "SELECT * FROM sign_table WHERE Sign = %s"
    parameters = (sign,)
    self.cursor.execute(query, parameters)
    result = self.cursor.fetchall()
    return len(result) > 0

  
