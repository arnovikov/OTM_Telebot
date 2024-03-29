import telebot
from telebot import types
import cx_Oracle
import re
import os
import configparser
from datetime import datetime
from ORACLE_DB import select_MC_by_UPD, UPD_data, UIT_data, EDO_file_name
from API_CRPT import check_mc, check_doc_status, create_upload_task, get_upload_task_status, get_result_id, get_result_file
from API_TT import check_outs_doc_status, nt_mc_status_update
from CREATE_EXCEL import create_excel
from TXT_FILE_PROCESSING import find_good_mc, find_bad_mc, usage_log, csv_to_txt
from IC_STATISTIC import IC_STATISTIC
from TELEBOT_USERS import user_id_list,admin_user_id_list,register_user
from GLOBAL_VAR import global_var
from fnmatch import fnmatch
import zipfile

config = configparser.ConfigParser()  # create of parser object
config.read(global_var())
lib_dir = config["ORACLE_DB"]["lib_dir"]  #get oracle DB connection string from settings
telebot_token = config["TELEGRAM_BOT"]["telebot_token"] #get telebot token from settings
support_chat_id = admin_user_id_list() #get support chat id to send message in case of exception

cx_Oracle.init_oracle_client(lib_dir) #initiate of oracle DB client connection
bot = telebot.TeleBot(telebot_token) #connect to telebot

@bot.message_handler(commands=['start'])  #handle of /start command
def send_welcome(message):
	bot.send_message(message.from_user.id, 'Привет, ' + message.from_user.first_name + '!\n\nВы попали в гости к боту по проверке кодов маркировки.\n\nДля того, чтобы узнать на что способен этот бот, используйте команду /help \n\nК сожалению, данный сервис доступен не для всех. \n\nДля получения доступа к сервису необходимо пройти регистрацию по команде /registration ' )

@bot.message_handler(commands=['help']) #handle of /help command
def send_help(message):
	bot.send_message(message.from_user.id, 'Вот что я умею:\n\n1.Проверять один КМ. Для этого просто введите код маркировки.\n\n2.Проверять список КМ по номеру УПД. Для этого необходимо указать номер УПД.\n\n3.Проверять КМ по списку из текстового файла. Для этого отправьте мне txt файл (каждый КМ должен быть в новой строке)\n\n4.Статистика по подписанию Intercompany УПД за период С-ПО доступна по команде /ic_statistic\n\n5.Проверять статус документа вывода из оборота в Track&Trace системе. Для этого необходимо указать номер документа с префиксом "outs_"\n\n6. Создать задачу на выгрузку КМ в ГИСМТ - команда /gismt_task')

@bot.message_handler(commands=['ic_statistic']) #handle of /ic_statistic command
def ic_statistic(message):
	msg = bot.send_message(message.from_user.id, 'Укажите "Дату С" в формате ДД.ММ.ГГГГ')
	bot.register_next_step_handler(msg, date_from)

def date_from(message):
	try:
		date_from = datetime.strptime(message.text, "%d.%m.%Y")
		msg = bot.send_message(message.from_user.id, 'Укажите "Дату ПО" в формате ДД.ММ.ГГГГ')
		bot.register_next_step_handler(msg, date_to, date_from)
	except Exception as err:
		bot.send_message(message.from_user.id, 'Вы указали дату в неверном формате, попробуйте ещё раз, пожалуйста.')
		bot.send_message(message.from_user.id, 'Ошибка: ' + str(err))


def date_to(message, date_from):
	try:
		date_to = datetime.strptime(message.text, "%d.%m.%Y")
	except Exception as err:
		bot.send_message(message.from_user.id, 'Вы указали дату в неверном формате, попробуйте ещё раз, пожалуйста.')
		bot.send_message(message.from_user.id, 'Ошибка: ' + str(err))
	if date_from > date_to:
		bot.send_message(message.from_user.id, '"Дата С" больше "Дата ПО", попробуйте ещё раз, пожалуйста.')
	elif (date_to-date_from).days > 31:
		bot.send_message(message.from_user.id, 'Вы запросили статистику более чем за 31 день. Чтобы не превысить лимит запросов к ГИСМТ, выборка должна быть не более чем за 31 день, попробуйте ещё раз, пожалуйста.')
	else:
		bot.send_message(message.from_user.id, 'Ожидайте ответа...')
		try:
			result_file = IC_STATISTIC(date_from,date_to)
			tmp_file = open(result_file, 'rb')
			bot.send_document(message.from_user.id, tmp_file)
			tmp_file.close()
			os.remove(result_file)
		except Exception as err:
			bot.send_message(message.from_user.id,	 'К сожалению, возникла ошибка. Обратитесь, пожалуйста, в тех поддержку')
			bot.send_message(message.from_user.id, 'Ошибка: ' + str(err))
			for i in support_chat_id:
				bot.send_message(i, 'Кое-кто попытался сломать бота!\n Вот это пользователь: ' + str(message.from_user.id) + '\n' + str(message.from_user.first_name) + str(message.from_user.last_name) + '\n' + 'Ошибка: ' + str(err))

@bot.message_handler(commands=['registration']) #handle of /registration command
def registration(message):
	msg = bot.send_message(message.from_user.id, 'Укажите вашу фамилию')
	bot.register_next_step_handler(msg, get_last_name)

def get_last_name(message):
	user_data = []
	user_data.append(message.from_user.id)
	user_data.append(message.text)
	msg = bot.send_message(message.from_user.id, 'Укажите ваше имя')
	bot.register_next_step_handler(msg, get_first_name, user_data)

def get_first_name(message, user_data):
	user_data.append(message.text)
	msg = bot.send_message(message.from_user.id, 'Укажите ваш e-mail')
	bot.register_next_step_handler(msg, get_email, user_data)

def get_email(message, user_data):
	user_data.append(message.text)
	try:
		register_user(user_data)
		for i in support_chat_id:
			bot.send_message(i, 'Внимание, зарегестрирован новый пользователь')
		bot.send_message(message.from_user.id, 'Спасибо за регистрацию, ваша заявка принята. Обратитесь, пожалуйста, в ServiceDesk для завершения модерации заявки.')
	except Exception as err:
		bot.send_message(message.from_user.id, 'К сожалению, регистарция не удалась. Это фиаско. Попробуйте ещё раз позднее, пожалуйста')
		bot.send_message(message.from_user.id, 'Ошибка: ' + str(err))
		for i in support_chat_id:
			bot.send_message(i, 'Кое-кто попытался сломать бота!\n Вот это пользователь: ' + str(message.from_user.id) + '\n' + str(message.from_user.first_name) + str(message.from_user.last_name) + '\n' + 'Ошибка: ' + str(err))

@bot.message_handler(commands=['gismt_task']) #handle of /gismt_task command
def GISMT_task(message):
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
	btn1 = types.KeyboardButton("NS")
	btn2 = types.KeyboardButton("NT")
	markup.add(btn1, btn2)
	msg = bot.send_message(message.chat.id, text="Пожалуйста, выберете бизнес-юнит, по которому требуется выгрузка данных.", reply_markup=markup)
	bot.register_next_step_handler(msg, get_business_unit)

def get_business_unit(message):
	if message.text == '/reset':
		bot.send_message(message.from_user.id, 'Каждый имеет право на ошибку, можете опробовать ещё раз')
		exit()
	user_data = [message.text]
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
	btn1 = types.KeyboardButton("EMITTED")
	btn2 = types.KeyboardButton("APPLIED")
	btn3 = types.KeyboardButton("INTRODUCED")
	btn4 = types.KeyboardButton("WRITTEN_OFF")
	btn5 = types.KeyboardButton("RETIRED")
	markup.add(btn1, btn2, btn3, btn4, btn5)
	msg = bot.send_message(message.chat.id, text="Пожалуйста, выберете статус кодов маркировки для выгрузки.", reply_markup=markup)
	bot.register_next_step_handler(msg, get_MC_status, user_data)

def get_MC_status(message,user_data):
	if message.text == '/reset':
		bot.send_message(message.from_user.id, 'Каждый имеет право на ошибку, можете опробовать ещё раз')
		exit()
	user_data.append(message.text)
	msg = bot.send_message(message.chat.id, text='Укажите "Дату эмиссии С" в формате ДД.ММ.ГГГГ', reply_markup=types.ReplyKeyboardRemove())
	bot.register_next_step_handler(msg, get_start_date, user_data)

def get_start_date(message,user_data):
	try:
		start_date = datetime.strptime(message.text, "%d.%m.%Y")
		start_date_str = str(start_date)[:10]
		user_data.append(start_date_str)
		msg = bot.send_message(message.from_user.id, 'Укажите "Дату эмиссии ПО" в формате ДД.ММ.ГГГГ')
		bot.register_next_step_handler(msg, get_end_date, user_data, start_date)
	except Exception as err:
		if message.text == '/reset':
			bot.send_message(message.from_user.id,'Каждый имеет право на ошибку, можете опробовать ещё раз')
			exit()
		bot.send_message(message.from_user.id, 'Вы указали дату в неверном формате, попробуйте ещё раз, пожалуйста.')
		bot.send_message(message.from_user.id, 'Ошибка: ' + str(err))
		msg = bot.send_message(message.from_user.id, 'Укажите "Дату эмиссии C" в формате ДД.ММ.ГГГГ')
		bot.register_next_step_handler(msg, get_start_date, user_data)

def get_end_date(message, user_data, start_date):
	try:
		end_date = datetime.strptime(message.text, "%d.%m.%Y")
	except Exception as err:
		if message.text == '/reset':
			bot.send_message(message.from_user.id,'Каждый имеет право на ошибку, можете опробовать ещё раз')
			exit()
		bot.send_message(message.from_user.id, 'Вы указали дату в неверном формате, попробуйте ещё раз, пожалуйста.')
		bot.send_message(message.from_user.id, 'Ошибка: ' + str(err))
		msg = bot.send_message(message.from_user.id, 'Укажите "Дату эмиссии ПО" в формате ДД.ММ.ГГГГ')
		bot.register_next_step_handler(msg, get_end_date, user_data, start_date)
	if end_date < start_date:
		bot.send_message(message.from_user.id, '"Дата С" больше "Дата ПО", попробуйте ещё раз, пожалуйста.')
		msg = bot.send_message(message.from_user.id, 'Укажите "Дату эмиссии ПО" в формате ДД.ММ.ГГГГ')
		bot.register_next_step_handler(msg, get_end_date, user_data, start_date)
	elif (end_date-start_date).days > 185:
		bot.send_message(message.from_user.id, 'Вы запросили статистику более чем за пол года. ГИСМТ такого не вывозит. Попробуйте сократить диапазон (максимум пол года).')
		msg = bot.send_message(message.from_user.id, 'Укажите "Дату эмиссии ПО" в формате ДД.ММ.ГГГГ')
		bot.register_next_step_handler(msg, get_end_date, user_data, start_date)
	else:
		end_date_str = str(end_date)[:10]
		user_data.append(end_date_str)
		task_id = create_upload_task(user_data[0],user_data[1],user_data[2],user_data[3])
		bot.send_message(message.from_user.id, 'Задача на выгрузку данных успешно размещена в ГИСМТ, используйте этот ID для проверки статуса задания: \n\n'+ str(user_data[0])+'_'+task_id)


@bot.message_handler(content_types=["text"]) #handle of text message
def text_message(message):
	users = user_id_list()
	if message.from_user.id not in users:   #check if user can use telebot or not
		bot.send_message(message.from_user.id, 'К сожалению, вы не в списке подтверждённых пользователей.\nПопробуйте воспользоваться командой /start')
	else:
		log_data = str(message.from_user.id)+'\t'+str(message.from_user.first_name)+'\t'+str(message.from_user.last_name)+'\t'+str(datetime.now().strftime("%d-%m-%Y %H:%M"))+'\t'+str(message.text)+'\n'
		usage_log(log_data)
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
				edo_file_name = EDO_file_name(message.text)
				mc_list = select_MC_by_UPD(message.text)  #get marking codes list from Oracle DB
			except Exception as err:
				bot.send_message(message.from_user.id, 'Не удалось подключиться к БД Oracle, обратитесь в поддержку')
				bot.send_message(message.from_user.id, 'Ошибка: '+str(err))
				for i in support_chat_id:
					bot.send_message(i,'Кое-кто попытался сломать бота!\n Вот это пользователь: '+str(message.from_user.id)+'\n'+str(message.from_user.first_name)+str(message.from_user.last_name)+'\n'+'Ошибка: '+str(err))
			if edo_file_name !=None:
				try:
					doc_status = check_doc_status(edo_file_name)
					bot.send_message(message.from_user.id, 'Статус ЭДО документа в ГИСМТ: '+doc_status)
				except Exception:
					bot.send_message(message.from_user.id, 'Такого документа нет в ГИСМТ, скорее всего его ещё не подписали с двух сторон')
			else:
				bot.send_message(message.from_user.id, 'Статус ЭДО документа в ГИСМТ: это бумажный документ, в ГИСМТ такого нет')
			if mc_list !=[]:
				try:
					data_for_user = check_mc(mc_list)  #send marking codes list to GISMT in order to get the data
				except Exception as err:
					bot.send_message(message.from_user.id, 'Не удалось подключиться к ГИСМТ, обратитесь в поддержку')
					bot.send_message(message.from_user.id, 'Ошибка: ' + str(err))
					for i in support_chat_id:
						bot.send_message(i, 'Кое-кто попытался сломать бота!\n Вот это пользователь: ' + str(message.from_user.id) + '\n' + str(message.from_user.first_name) + str(message.from_user.last_name) + '\n' + 'Ошибка: ' + str(err))
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
				for i in support_chat_id:
					bot.send_message(i, 'Кое-кто попытался сломать бота!\n Вот это пользователь: ' + str(message.from_user.id) + '\n' + str(message.from_user.first_name) + str(message.from_user.last_name) + '\n' + 'Ошибка: ' + str(err))
			mc_list = []
			mc_list.append(message.text)
			try:
				data_for_user = check_mc(mc_list)   #send marking code to GISMT in order to check it
			except Exception as err:
				bot.send_message(message.from_user.id, 'Не удалось подключиться к ГИСМТ, обратитесь в поддержку')
				bot.send_message(message.from_user.id, 'Ошибка: ' + str(err))
				for i in support_chat_id:
					bot.send_message(i, 'Кое-кто попытался сломать бота!\n Вот это пользователь: ' + str(message.from_user.id) + '\n' + str(message.from_user.first_name) + str(message.from_user.last_name) + '\n' + 'Ошибка: ' + str(err))
			if data_for_user == {}:   # in case user sent wrong MC
				bot.send_message(message.from_user.id, 'Такого кода маркировки не существует в ГИСМТ')
			else:
				message_result = ''
				for x in data_for_user.get(message.text):  #creating a message for user with data from GISMT
					message_result = message_result + '*'+str(x) + ':* [' + str(data_for_user.get(message.text).get(x)) + ']\n'
				bot.send_message(message.from_user.id, message_result, parse_mode= "Markdown")

		elif message.text.lower()[:5] == 'outs_':  #check for UIT marking code format
			try:
				doc_number = re.sub("^\s+|\n|\r|\s+$", '', message.text[5:])
				data_for_user = check_outs_doc_status(doc_number)
				message_result = '################' + '\n'
				for x in data_for_user:  # creating a message for user with data from Track&Trace
					message_result = message_result + '*' + str(x) + ':*  [' + str(data_for_user.get(x)) + ']\n'
				message_result = message_result + '################' + '\n'
				bot.send_message(message.from_user.id, message_result, parse_mode="Markdown")
			except Exception as err:
				bot.send_message(message.from_user.id, 'Не удалось найти такой документ вывода из оборота в Track&Trace. Проверьте, пожалуйста, данные')
				bot.send_message(message.from_user.id, 'Ошибка: ' + str(err))
		elif fnmatch(message.text, '??_????????-????-????-????-????????????') == True:  #check for GISMT_task_id
			gismt_task_status = get_upload_task_status(message.text[:2], message.text[3:])
			bot.send_message(message.from_user.id, 'Status of task ' + message.text + ' is ' + gismt_task_status)
			if gismt_task_status == '"COMPLETED"':
				bot.send_message(message.from_user.id, 'Скачивание файла началось, ожидайте', reply_markup=types.ReplyKeyboardRemove())
				result_id = get_result_id(message.text[:2], message.text[3:])
				downloaded_file_path = get_result_file(message.text[:2],result_id)
				tmp_file = open(downloaded_file_path, 'rb')
				bot.send_message(message.from_user.id, 'Вот исходник:')
				bot.send_document(message.from_user.id, tmp_file)
				tmp_file.close()
				zip_file = zipfile.ZipFile(downloaded_file_path, 'r')
				zip_file_name = zip_file.infolist()[0].filename
				directory_to_extract = os.path.dirname(downloaded_file_path)
				zip_file.extractall(directory_to_extract)
				zip_file.close()
				os.remove(downloaded_file_path)  # delete zip file
				csv_file_path = directory_to_extract + '/' + zip_file_name
				csv_to_txt(csv_file_path)  # run function to convert csv to txt
				tmp_file = open(csv_file_path.replace(".csv", ".txt"), 'rb')
				bot.send_message(message.from_user.id, 'Вот лайтовая версия:')
				bot.send_document(message.from_user.id, tmp_file)
				tmp_file.close()
				os.remove(csv_file_path.replace(".csv", ".txt"))

		elif message.text.lower().find("привет") != -1:  #check for 'hello'
			bot.send_sticker(message.from_user.id, 'CAACAgIAAxkBAAECo0lg_n6BDazemB16T4YlCDcrjCMeIwACUw0AAk8zeUlbToMKNIIVcCAE')
			bot.send_message(message.from_user.id, 'Привет, ' + message.from_user.first_name + '!\n\nВы попали в гости к боту по проверке кодов маркировки.\n\nДля того, чтобы узнать на что способен этот бот, используйте команду /help')
		elif message.text.lower().find("дурак") != -1 or message.text.lower().find("тупой") != -1 or message.text.lower().find("тупица") != -1:  #check for rude
			bot.send_sticker(message.from_user.id, 'CAACAgIAAxkBAAECoyxg_nynhc34Q3XdDGp0BpKLZdoV-wAClQUAAiMFDQABt0k_ZMWu768gBA')
		elif message.text.lower().find("класс") != -1 or message.text.lower().find("супер") != -1 or message.text.lower().find("спасибо") != -1:  #check for thanks
			bot.send_sticker(message.from_user.id, 'CAACAgIAAxkBAAECozdg_n1XvL7Pbcr--_5iIfg72IeoVwACAwADkp8eEXErN798EUMfIAQ')
		else:
			bot.send_sticker(message.from_user.id,'CAACAgIAAxkBAAECoyhg_nxSIPUY753MX_LTa21rfeTbJwAChwUAAiMFDQABE-Nhq6tbXOMgBA')
			bot.send_message(message.from_user.id, 'К сожалению, я вас не понимаю. Проверьте данные, которые вводите, пожалуйста. Для более детальной информации вы всегда можете использовать команду /help')


@bot.message_handler(content_types=["document"])
def handle_docs(message):
	users = user_id_list()
	if message.from_user.id not in users:    #check if user can use telebot or not
		bot.send_message(message.from_user.id, 'К сожалению, вы не в списке подтверждённых пользователей.\nПопробуйте воспользоваться командой /start')
	else:
		log_data = str(message.from_user.id) + '\t' + str(message.from_user.first_name) + '\t' + str(message.from_user.last_name) + '\t' + str(datetime.now().strftime("%d-%m-%Y %H:%M")) + '\t' + str(message.document.file_name) + '\n'
		usage_log(log_data)
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
			subst = filename.lower().find('nt_status_update')
			if subst != -1:
				try:
					data_for_user = str(nt_mc_status_update(mc_list_good))
					bot.send_message(message.from_user.id, data_for_user)
				except Exception as err:
					bot.send_message(message.from_user.id, 'Не удалось подключиться к T&T, обратитесь в поддержку')
					bot.send_message(message.from_user.id, 'Ошибка: ' + str(err))
					for i in support_chat_id:
						bot.send_message(i, 'Кое-кто попытался сломать бота!\n Вот это пользователь: ' + str(message.from_user.id) + '\n' + str(message.from_user.first_name) + str(message.from_user.last_name) + '\n' + 'Ошибка: ' + str(err))
			else:
				try:
					data_for_user = check_mc(mc_list_good)  #sending marking codes from txt file to GISMT in order to check them
				except Exception as err:
					bot.send_message(message.from_user.id, 'Не удалось подключиться к ГИСМТ, обратитесь в поддержку')
					bot.send_message(message.from_user.id, 'Ошибка: ' + str(err))
					for i in support_chat_id:
						bot.send_message(i, 'Кое-кто попытался сломать бота!\n Вот это пользователь: ' + str(message.from_user.id) + '\n' + str(message.from_user.first_name) + str(message.from_user.last_name) + '\n' + 'Ошибка: ' + str(err))
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