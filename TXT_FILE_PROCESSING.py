import re
from GLOBAL_VAR import global_var
import os

def find_good_mc(dowloaded_file_path):
    file = open(dowloaded_file_path, 'r')
    mc_list_good = []
    count = 0
    s = file.readline()
    while s != '':
        if len(re.sub("^\s+|\n|\r|\s+$", '', s)) == 31:  # delete characters we don't need
            mc_list_good.append(re.sub("^\s+|\n|\r|\s+$", '', s))  # add mc to good array
        s = file.readline()
        count = count + 1
    file.close()
    return (mc_list_good)

def find_bad_mc(dowloaded_file_path):
    file = open(dowloaded_file_path, 'r')
    mc_list_bad = []
    count = 0
    s = file.readline()
    while s != '':
        if len(re.sub("^\s+|\n|\r|\s+$", '', s)) != 31:  # delete characters we don't need
            mc_list_bad.append(re.sub("^\s+|\n|\r|\s+$", '', s))  # add mc to bad array
        s = file.readline()
        count = count + 1
    file.close()
    return (mc_list_bad)

def usage_log(data):
    import configparser
    config = configparser.ConfigParser()
    config.read(global_var())
    file_path = config["TXT_FILE_PROCESSING"]["file_path"]
    file = open(file_path, 'a')
    file.write(data)
    file.close()

def csv_to_txt(csv_file_path):
    file = open(csv_file_path, 'r', encoding='utf-8')
    MC_list = []
    count = 0
    s = file.readline()
    while s != '':
        if s[:6] == """"01064""":
            MC_list.append(s[1:32])
        s = file.readline()
        count = count + 1
    file.close()
    os.remove(csv_file_path)
    file = open(csv_file_path.replace(".csv", ".txt"), 'w')
    for s in MC_list:
        file.write("%s\n" % s)
    file.close()
