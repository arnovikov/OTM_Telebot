import telebot
from telebot import types
import cx_Oracle
import re
import os
import configparser
from ORACLE_DB import select_MC_by_UPD
from CHECK_MC import check_mc
from CREATE_EXCEL import create_excel
from TXT_FILE_PROCESSING import find_good_mc, find_bad_mc

config = configparser.ConfigParser()  # создаём объекта парсера
config.read("C:/Users/arnovikov/OneDrive - Nokian Tyres/Documents/_Работа/OTM Project/MC_Check/settings.ini")
lib_dir = config["ORACLE_DB"]["lib_dir"]
telebot_token = config["TELEGRAM_BOT"]["telebot_token"]

cx_Oracle.init_oracle_client(lib_dir) #https://ru.stackoverflow.com/questions/1185282/%D0%9E%D1%88%D0%B8%D0%B1%D0%BA%D0%B0-dpi-1047-oracle-client-library-cannot-be-loaded
bot = telebot.TeleBot(telebot_token)

@bot.message_handler(commands=['start'])
def send_welcome(message):
	bot.send_message(message.from_user.id, 'Привет, ' + message.from_user.first_name + '!\n\nВы попали в гости к боту по проверке кодов маркировки.\n\nДля того, чтобы узнать на что способен этот бот, используйте команду /help\n\nК сожалению, данный сервис доступен не для всех.\nДля получения доступа к сервису сообщите, пожалуйста, в Service Desk\nсвой user ID в Telegram = ' + str(message.from_user.id))
	# markup = types.ReplyKeyboardMarkup(row_width=2)
	# itembtn1 = types.KeyboardButton('/UPD_Number')
	# itembtn2 = types.KeyboardButton('/TXT_file')
	# markup.add(itembtn1, itembtn2)
	# bot.send_message(message.from_user.id, "Choose one letter:", reply_markup=markup)

@bot.message_handler(commands=['help'])
def send_help(message):
	#markup = types.ReplyKeyboardRemove()
	bot.send_message(message.from_user.id, 'Вот что я умею:\n\n1.Проверять один КМ. Для этого просто введите код маркировки.\n\n2.Проверять список КМ по номеру УПД. Для этого необходимо указать номер УПД.\n\n3.Проверять КМ по списку из текстового файла. Для этого отправьте мне txt файл (каждый КМ должен быть в новой строке)')


@bot.message_handler(content_types=["text"])
def text_message(message):
	import configparser
	config = configparser.ConfigParser()  # создаём объекта парсера
	config.read("C:/Users/arnovikov/OneDrive - Nokian Tyres/Documents/_Работа/OTM Project/MC_Check/settings.ini")
	users = config["TELEGRAM_BOT"]["users"].split(';')
	if str(message.from_user.id) not in users:
		bot.send_message(message.from_user.id, 'К сожалению, вы не в списке подтверждённых пользователей.\nПопробуйте воспользоваться командой /start')
	else:
		if len(re.sub("^\s+|\n|\r|\s+$", '', message.text)) == 11 and message.text[:2]=='20':
			bot.send_message(message.from_user.id, 'Ожидайте ответа...')
			try:
				mc_list = select_MC_by_UPD(message.text)
			except Exception:
				bot.send_message(message.from_user.id, 'Не удалось подключиться к БД Oracle, обратитесь в поддержку')
			if mc_list !=[]:
				try:
					data_for_user = check_mc(mc_list)
				except Exception:
					bot.send_message(message.from_user.id, 'Не удалось подключиться к ГИСМТ, обратитесь в поддержку')
			if data_for_user != {}:
				try:
					result_file = create_excel(mc_list,data_for_user,message.text+'_result.xlsx')
					tmp_file = open(result_file, 'rb')
					bot.send_document(message.from_user.id, tmp_file)
					tmp_file.close()
					os.remove(result_file)
				except Exception:
					bot.send_message(message.from_user.id, 'Не удалось сформирвоать Excel файл, обратитесь в поддержку')
		elif len(re.sub("^\s+|\n|\r|\s+$", '', message.text)) == 31 and message.text[:2]=='01' and message.text[16:18]=='21':
			mc_list = []
			mc_list.append(message.text)
			data_for_user = check_mc(mc_list)
			message_result = ''
			for x in data_for_user.get(message.text):
				message_result = message_result + str(x) + ':  ' + str(data_for_user.get(message.text).get(x)) + '\n'
			bot.send_message(message.from_user.id, message_result)
		else:
			bot.send_message(message.from_user.id, 'Что-то я вас не понимаю, перепроверьте данные, которые вводите, пожалуйста. Для более детальной информации ты всегда можешь использовать команду /help')


@bot.message_handler(content_types=["document"])
def handle_docs(message):
	import configparser
	config = configparser.ConfigParser()  # создаём объекта парсера
	config.read("C:/Users/arnovikov/OneDrive - Nokian Tyres/Documents/_Работа/OTM Project/MC_Check/settings.ini")
	users = config["TELEGRAM_BOT"]["users"].split(';')
	if str(message.from_user.id) not in users:
		bot.send_message(message.from_user.id, 'К сожалению, вы не в списке подтверждённых пользователей.\nПопробуйте воспользоваться командой /start')
	else:
		import configparser
		config = configparser.ConfigParser()  # создаём объекта парсера
		config.read("C:/Users/arnovikov/OneDrive - Nokian Tyres/Documents/_Работа/OTM Project/MC_Check/settings.ini")
		document_id = message.document.file_id
		file_info = bot.get_file(document_id)
		downloaded_file = bot.download_file(file_info.file_path)
		dowloaded_file_path = str(config["TELEGRAM_BOT"]["file_path"]) + message.document.file_name
		filename, file_extension = os.path.splitext(dowloaded_file_path)
		with open(dowloaded_file_path, 'wb') as new_file:
			new_file.write(downloaded_file)  # записываем данные в файл
		new_file.close()
		if file_extension != '.txt':
			bot.send_message(message.from_user.id, 'Я умею обрабатывать только .txt файлы, попробуйте ещё раз')
			os.remove(dowloaded_file_path)
		else:
			mc_list_good = find_good_mc(dowloaded_file_path)
			mc_list_bad = find_bad_mc(dowloaded_file_path)
			os.remove(dowloaded_file_path)
			bot.send_message(message.from_user.id,'File has ' + str(len(mc_list_good)+len(mc_list_bad)) + ' lines TOTAL')
			bot.send_message(message.from_user.id, 'File has ' + str(len(mc_list_good)) + ' MCs')
			bot.send_message(message.from_user.id, 'Bad MCs: ' + str(mc_list_bad))
			bot.send_message(message.from_user.id, 'Ожидайте ответа...')
			data_for_user = check_mc(mc_list_good)
			result_file = create_excel(mc_list_good, data_for_user, message.document.file_name + '_result.xlsx')
			tmp_file = open(result_file, 'rb')
			bot.send_document(message.from_user.id, tmp_file)
			tmp_file.close()
			os.remove(result_file)

bot.polling()