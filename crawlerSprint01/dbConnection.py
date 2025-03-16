import mysql.connector

connection = mysql.connector.connect(
    host="ec2-54-163-222-83.compute-1.amazonaws.com",
    user="admin",
    password="urubu100",
    database="infrawatch"
)



cursor = connection.cursor()
