from GLOBAL_VAR import global_var
import psycopg2
import configparser
config = configparser.ConfigParser()
config.read(global_var())
host = config["POSTGRES_DB"]["host"]
db_name = config["POSTGRES_DB"]["db_name"]
user = config["POSTGRES_DB"]["user"]
password = config["POSTGRES_DB"]["password"]
connection = psycopg2.connect(host=host,user=user,password=password,database=db_name)

def check_user(telegram_user_id):
    with connection.cursor() as cursor:
        cursor.execute("""SELECT approveflag from telebot_users_v where telegramuserid="""+str(telegram_user_id)+""";""")
        user_status=cursor.fetchone()
        if user_status is None:
            user_status = False
        else:
            user_status = user_status[0]
    connection.close
    return user_status

def admin_user_id_list():
    with connection.cursor() as cursor:
        cursor.execute("""SELECT telegramuserid from telebot_users_v where adminflag = 'True';""")
        data=cursor.fetchall()
        admin_list = []
        for i in range (0, len(data)):
            admin_list.append(data[i][0])
    connection.close
    return admin_list

def register_user(user_data):
    with connection.cursor() as cursor:
        cursor.execute("""INSERT INTO telebot_users (telegramuserid, lastname, firstname, email, adminflag, userstatusid) values ("""+str(user_data[0])+""",'"""+str(user_data[1])+"""','"""+str(user_data[2])+"""','"""+str(user_data[3])+"""','n',1); COMMIT;""")
    connection.close

def usage_log(log_data):
    with connection.cursor() as cursor:
        cursor.execute("""INSERT INTO telebot_usage_log (telegramuserid, messagetext) values ("""+str(log_data[0])+""",$$"""+str(log_data[1])+"""$$); COMMIT;""")
    connection.close
