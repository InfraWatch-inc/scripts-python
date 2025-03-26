import mysql.connector

connection = mysql.connector.connect(
    host="ec2-54-227-50-104.compute-1.amazonaws.com",
    user="admin",
    password="urubu100",
    database="infrawatch"
)

cursor = connection.cursor()
