import telebot
import cx_Oracle
import re
import os
import configparser
from ORACLE_DB import select_MC_by_UPD, UPD_data, UIT_data
from CHECK_MC import check_mc
from CREATE_EXCEL import create_excel
from TXT_FILE_PROCESSING import find_good_mc, find_bad_mc
from GLOBAL_VAR import global_var

config = configparser.ConfigParser()  # create of parser object
config.read(global_var())
lib_dir = config["ORACLE_DB"]["lib_dir"]  #get oracle DB connection string from settings
telebot_token = config["TELEGRAM_BOT"]["telebot_token"] #get telebot token from settings
support_chat_id = config["TELEGRAM_BOT"]["support_chat_id"] #get support chat id to send message in case of exception

cx_Oracle.init_oracle_client(lib_dir) #initiate of oracle DB client connection
bot = telebot.TeleBot(telebot_token) #connect to telebot

@bot.message_handler(commands=['start'])  #handle of /start command
def send_welcome(message):
	bot.send_message(message.from_user.id, 'Привет, ' + message.from_user.first_name + '!\n\nВы попали в гости к боту по проверке кодов маркировки.\n\nДля того, чтобы узнать на что способен этот бот, используйте команду /help \n\nК сожалению, данный сервис доступен не для всех.\n\nДля получения доступа к сервису сообщите, пожалуйста, в Service Desk\nсвой user ID в Telegram = ' + str(message.from_user.id))

@bot.message_handler(commands=['help']) #handle of /help command
def send_help(message):
	bot.send_message(message.from_user.id, 'Вот что я умею:\n\n1.Проверять один КМ. Для этого просто введите код маркировки.\n\n2.Проверять список КМ по номеру УПД. Для этого необходимо указать номер УПД.\n\n3.Проверять КМ по списку из текстового файла. Для этого отправьте мне txt файл (каждый КМ должен быть в новой строке)')


@bot.message_handler(content_types=["text"]) #handle of text message
def text_message(message):
	import configparser
	config = configparser.ConfigParser()
	config.read(global_var())
	users = config["TELEGRAM_BOT"]["users"].split(';')
	if str(message.from_user.id) not in users:   #check if user can use telebot or not
		bot.send_message(message.from_user.id, 'К сожалению, вы не в списке подтверждённых пользователей.\nПопробуйте воспользоваться командой /start')
	else:
		if len(re.sub("^\s+|\n|\r|\s+$", '', message.text)) == 11 and message.text[:2]=='20' and message.text.isnumeric():  #check for UPD number format
			try:
				upd_data = UPD_data(message.text)  #run procedure to get additional data from Oracle DB
				bot.send_message(message.from_user.id, 'UPD additional data:')
				message_result = '################' + '\n'
				for dict in upd_data:   #creating a message for user with data from Oracle DB
					for x in dict:
						message_result = message_result + '*' + str(x) + ':*  [' + str(dict.get(x)) + ']\n'
					message_result = message_result + '################' + '\n'
				bot.send_message(message.from_user.id, message_result,parse_mode= "Markdown")
				bot.send_message(message.from_user.id, 'Ожидайте ответа...')
				mc_list = select_MC_by_UPD(message.text)  #get marking codes list from Oracle DB
			except Exception as err:
				bot.send_message(message.from_user.id, 'Не удалось подключиться к БД Oracle, обратитесь в поддержку')
				bot.send_message(message.from_user.id, 'Ошибка: '+str(err))
				bot.send_message(support_chat_id,'Кое-кто попытался сломать бота!\n Вот это пользователь: '+str(message.from_user.id)+'\n'+str(message.from_user.first_name)+str(message.from_user.last_name)+'\n'+'Ошибка: '+str(err))
			if mc_list !=[]:
				try:
					data_for_user = check_mc(mc_list)  #send marking codes list to GISMT in order to get the data
				except Exception as err:
					bot.send_message(message.from_user.id, 'Не удалось подключиться к ГИСМТ, обратитесь в поддержку')
					bot.send_message(message.from_user.id, 'Ошибка: ' + str(err))
					bot.send_message(support_chat_id, 'Кое-кто попытался сломать бота!\n Вот это пользователь: ' + str(message.from_user.id) + '\n' + str(message.from_user.first_name) + str(message.from_user.last_name) + '\n' + 'Ошибка: ' + str(err))
			else:
				bot.send_message(message.from_user.id, 'Указанный УПД не содержит ни одного кода маркировки')
			if data_for_user != {}:
				result_file = create_excel(mc_list,data_for_user,message.text+'_result.xlsx')  #create Excel report with marking codes list
				tmp_file = open(result_file, 'rb')
				bot.send_document(message.from_user.id, tmp_file)
				tmp_file.close()
				os.remove(result_file)

		elif len(re.sub("^\s+|\n|\r|\s+$", '', message.text)) == 31 and message.text[:2]=='01' and message.text[16:18]=='21':  #check for UIT marking code format
			try:
				bot.send_message(message.from_user.id, 'Additional UIT data:')
				uit_data = UIT_data(message.text)  # get additional data from Oracle DB
				message_result = '################' + '\n'
				for dict in uit_data:  #creating a message for user with data from Oracle DB
					for x in dict:
						message_result = message_result + '*' + str(x) + ':*  [' + str(dict.get(x)) + ']\n'
					message_result = message_result + '################' + '\n'
				bot.send_message(message.from_user.id, message_result, parse_mode= "Markdown")
			except Exception as err:
				bot.send_message(message.from_user.id, 'Не удалось подключиться к БД Oracle, обратитесь в поддержку')
				bot.send_message(message.from_user.id, 'Ошибка: ' + str(err))
				bot.send_message(support_chat_id, 'Кое-кто попытался сломать бота!\n Вот это пользователь: ' + str(message.from_user.id) + '\n' + str(message.from_user.first_name) + str(message.from_user.last_name) + '\n' + 'Ошибка: ' + str(err))
			mc_list = []
			mc_list.append(message.text)
			try:
				data_for_user = check_mc(mc_list)   #send marking code to GISMT in order to check it
			except Exception as err:
				bot.send_message(message.from_user.id, 'Не удалось подключиться к ГИСМТ, обратитесь в поддержку')
				bot.send_message(message.from_user.id, 'Ошибка: ' + str(err))
				bot.send_message(support_chat_id, 'Кое-кто попытался сломать бота!\n Вот это пользователь: ' + str(message.from_user.id) + '\n' + str(message.from_user.first_name) + str(message.from_user.last_name) + '\n' + 'Ошибка: ' + str(err))
			if data_for_user == {}:   # in case user sent wrong MC
				bot.send_message(message.from_user.id, 'Такого кода маркировки не существует в ГИСМТ')
			else:
				message_result = ''
				for x in data_for_user.get(message.text):  #creating a message for user with data from GISMT
					message_result = message_result + '*'+str(x) + ':* [' + str(data_for_user.get(message.text).get(x)) + ']\n'
				bot.send_message(message.from_user.id, message_result, parse_mode= "Markdown")
		elif message.text.lower().find("привет") != -1:  #check for 'hello'
			bot.send_sticker(message.from_user.id, 'CAACAgIAAxkBAAECo0lg_n6BDazemB16T4YlCDcrjCMeIwACUw0AAk8zeUlbToMKNIIVcCAE')
			bot.send_message(message.from_user.id, 'Вот что я умею:\n\n1.Проверять один КМ. Для этого просто введите код маркировки.\n\n2.Проверять список КМ по номеру УПД. Для этого необходимо указать номер УПД.\n\n3.Проверять КМ по списку из текстового файла. Для этого отправьте мне txt файл (каждый КМ должен быть в новой строке)')
		elif message.text.lower().find("дурак") != -1 or message.text.lower().find("тупой") != -1 or message.text.lower().find("тупица") != -1:  #check for rude
			bot.send_sticker(message.from_user.id, 'CAACAgIAAxkBAAECoyxg_nynhc34Q3XdDGp0BpKLZdoV-wAClQUAAiMFDQABt0k_ZMWu768gBA')
		elif message.text.lower().find("класс") != -1 or message.text.lower().find("супер") != -1 or message.text.lower().find("спасибо") != -1:  #check for thanks
			bot.send_sticker(message.from_user.id, 'CAACAgIAAxkBAAECozdg_n1XvL7Pbcr--_5iIfg72IeoVwACAwADkp8eEXErN798EUMfIAQ')
		else:
			bot.send_sticker(message.from_user.id,'CAACAgIAAxkBAAECoyhg_nxSIPUY753MX_LTa21rfeTbJwAChwUAAiMFDQABE-Nhq6tbXOMgBA')
			bot.send_message(message.from_user.id, 'Что-то я вас не понимаю, перепроверьте данные, которые вводите, пожалуйста. Для более детальной информации ты всегда можешь использовать команду /help')


@bot.message_handler(content_types=["document"])
def handle_docs(message):
	import configparser
	config = configparser.ConfigParser()
	config.read(global_var())
	users = config["TELEGRAM_BOT"]["users"].split(';')
	if str(message.from_user.id) not in users:    #check if user can use telebot or not
		bot.send_message(message.from_user.id, 'К сожалению, вы не в списке подтверждённых пользователей.\nПопробуйте воспользоваться командой /start')
	else:
		import configparser
		config = configparser.ConfigParser()
		config.read(global_var())
		document_id = message.document.file_id
		file_info = bot.get_file(document_id)  #getting document_id from telegram
		downloaded_file = bot.download_file(file_info.file_path)  #download file
		dowloaded_file_path = str(config["TELEGRAM_BOT"]["file_path"]) + message.document.file_name
		filename, file_extension = os.path.splitext(dowloaded_file_path)
		with open(dowloaded_file_path, 'wb') as new_file:   #write the data to the file
			new_file.write(downloaded_file)
		new_file.close()
		if file_extension != '.txt':   #check for file extaention
			bot.send_message(message.from_user.id, 'Я умею обрабатывать только .txt файлы, попробуйте ещё раз')
			os.remove(dowloaded_file_path)
		else:
			mc_list_good = find_good_mc(dowloaded_file_path)   #getting marking codes list we can try to check in GISMT
			mc_list_bad = find_bad_mc(dowloaded_file_path)     #getting marking codes list we can't try to check in GISMT
			os.remove(dowloaded_file_path)
			bot.send_message(message.from_user.id,'File has ' + str(len(mc_list_good)+len(mc_list_bad)) + ' lines TOTAL')
			bot.send_message(message.from_user.id, 'File has ' + str(len(mc_list_good)) + ' MCs')
			bot.send_message(message.from_user.id, 'Bad MCs: ' + str(mc_list_bad))
			bot.send_message(message.from_user.id, 'Ожидайте ответа...')
			try:
				data_for_user = check_mc(mc_list_good)  #sending marking codes from txt file to GISMT in order to check them
			except Exception as err:
				bot.send_message(message.from_user.id, 'Не удалось подключиться к ГИСМТ, обратитесь в поддержку')
				bot.send_message(message.from_user.id, 'Ошибка: ' + str(err))
				bot.send_message(support_chat_id, 'Кое-кто попытался сломать бота!\n Вот это пользователь: ' + str(message.from_user.id) + '\n' + str(message.from_user.first_name) + str(message.from_user.last_name) + '\n' + 'Ошибка: ' + str(err))
			result_file = create_excel(mc_list_good, data_for_user, message.document.file_name + '_result.xlsx')   #creating an Excel report for user
			tmp_file = open(result_file, 'rb')
			bot.send_document(message.from_user.id, tmp_file)
			tmp_file.close()
			os.remove(result_file)

while True:
	try:
		bot.polling()
	except Exception as e:
		print(e)