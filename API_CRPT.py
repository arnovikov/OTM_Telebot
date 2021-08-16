from GLOBAL_VAR import global_var
def check_mc (mc_list):
    import requests
    import json
    import configparser
    import subprocess
    import datetime
    import os
    config = configparser.ConfigParser()
    config.read(global_var())
    url = config["API_CRPT"]["url_check_mc"]
    token_path = config["API_CRPT"]["token_path"]
    script_path = config["API_CRPT"]["script_path"]
    mc_maxamount_to_check = int(config["API_CRPT"]["mc_maxamount_to_check"])
    file_time = datetime.datetime.fromtimestamp(os.stat(token_path).st_mtime)
    delta_time = datetime.timedelta(hours=10)
    if file_time+delta_time <= datetime.datetime.now():
        subprocess.check_call('powershell -file "' + script_path + '"')
    token_file = open(token_path,'r',encoding='utf_16')
    bearer = token_file.read()
    token_file.close()
    data = {}
    count = 1
    num_of_runs = len(mc_list)//mc_maxamount_to_check + 1
    for run in range(num_of_runs):
        headers = {'Authorization': 'Bearer '+bearer, 'content-type':'application/json', 'charset':'utf-8'}
        body = {"cises":mc_list[(count-1)*mc_maxamount_to_check:count*mc_maxamount_to_check]}
        req = requests.post(url, headers=headers,  data=json.dumps(body))
        data_run = json.loads(req.text)
        data = {**data, **data_run}
        count = count+1
    return data

def check_doc_status(doc_id):
    import requests
    import json
    import configparser
    import subprocess
    import datetime
    import os
    config = configparser.ConfigParser()
    config.read(global_var())
    url2 = config["API_CRPT"]["url_check_doc"]
    token_path = config["API_CRPT"]["token_path"]
    script_path = config["API_CRPT"]["script_path"]
    file_time = datetime.datetime.fromtimestamp(os.stat(token_path).st_mtime)
    delta_time = datetime.timedelta(hours=10)
    if file_time + delta_time <= datetime.datetime.now():
        subprocess.check_call('powershell -file "' + script_path + '"')
    token_file = open(token_path, 'r', encoding='utf_16')
    bearer = token_file.read()
    token_file.close()
    headers = {'Authorization': 'Bearer ' + bearer, 'content-type': 'application/json', 'charset': 'utf-8'}
    req = requests.get(url2 + doc_id + '/body', headers=headers)
    doc_status = json.dumps(req.json()['downloadStatus'])
    return doc_status