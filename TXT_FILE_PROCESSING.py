import re
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