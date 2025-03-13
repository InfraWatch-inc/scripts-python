import mysql.connector

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Gui#2020",
    database="infrawatch"
)



cursor = connection.cursor()
