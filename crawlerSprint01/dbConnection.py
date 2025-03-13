import mysql.connector

connection = mysql.connector.connect(
    host="44.222.223.79",
    user="admin",
    password="urubu100",
    database="infrawatch"
)



cursor = connection.cursor()
