from GLOBAL_VAR import global_var
import requests
import json
import configparser
from API_TT import get_CRPT_token
def check_mc (mc_list):
    #import subprocess
    #import datetime
    #import os
    config = configparser.ConfigParser()
    config.read(global_var())
    url = config["API_CRPT"]["url_check_mc"]
    mc_maxamount_to_check = int(config["API_CRPT"]["mc_maxamount_to_check"])
    #token_path = config["API_CRPT"]["token_path"]
    #script_path = config["API_CRPT"]["script_path"]
    #file_time = datetime.datetime.fromtimestamp(os.stat(token_path).st_mtime)
    #delta_time = datetime.timedelta(hours=10)
    #if file_time+delta_time <= datetime.datetime.now():
    #    subprocess.check_call('powershell -file "' + script_path + '"')
    #token_file = open(token_path,'r',encoding='utf_16')
    #token_file.close()
    bearer = get_CRPT_token()
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
    # import subprocess
    # import datetime
    # import os
    config = configparser.ConfigParser()
    config.read(global_var())
    url2 = config["API_CRPT"]["url_check_doc"]
    # token_path = config["API_CRPT"]["token_path"]
    # script_path = config["API_CRPT"]["script_path"]
    # file_time = datetime.datetime.fromtimestamp(os.stat(token_path).st_mtime)
    # delta_time = datetime.timedelta(hours=10)
    # if file_time + delta_time <= datetime.datetime.now():
    #     subprocess.check_call('powershell -file "' + script_path + '"')
    # token_file = open(token_path, 'r', encoding='utf_16')
    bearer = get_CRPT_token()
    #token_file.close()
    headers = {'Authorization': 'Bearer ' + bearer, 'content-type': 'application/json', 'charset': 'utf-8'}
    req = requests.get(url2 + doc_id + '/body', headers=headers)
    doc_status = json.dumps(req.json()['downloadStatus'])
    return doc_status

def create_upload_task(status,start_date,end_date):
    config = configparser.ConfigParser()
    config.read(global_var())
    url = config["API_CRPT"]["url_create_upload_task"]
    bearer = get_CRPT_token()
    headers = {'Authorization': 'Bearer ' + bearer, 'content-type': 'application/json'}
    body = {"format": "CSV", "name": "FILTERED_CIS_REPORT", "periodicity": "SINGLE", "productGroupCode": "5","params": "{\"participantInn\":\"7816162305\",\"packageType\":[\"UNIT\",\"LEVEL1\"],\"status\":\"" + status + "\",\"emissionPeriod\":{\"start\":\"" + start_date + "T08:02:30.577395Z\",\"end\":\"" + end_date + "T08:02:30.577395Z\"}}"}
    request = requests.post(url, headers=headers, json=body)
    task_id = json.dumps(request.json()['id'])
    return task_id

def get_upload_task_status(task_id):
    config = configparser.ConfigParser()
    config.read(global_var())
    url = config["API_CRPT"]["url_get_upload_task_status"] + task_id
    bearer = get_CRPT_token()
    headers = {'Authorization': 'Bearer ' + bearer, 'content-type': 'application/json'}
    params = {"pg":"5"}
    request = requests.get(url, headers=headers, params=params)
    task_status = json.dumps(request.json()['currentStatus'])
    return task_status

def get_result_id(task_id):
    config = configparser.ConfigParser()
    config.read(global_var())
    url = config["API_CRPT"]["url_get_result_id"]
    bearer = get_CRPT_token()
    headers = {'Authorization': 'Bearer ' + bearer, 'content-type': 'application/json'}
    params = {'page':'0','size':'10','pg':'5','task_ids':[''+task_id+'']}
    request = requests.get(url, headers=headers, params=params )
    result_id = json.dumps(request.json()['list'][0]['id']).replace('"','')
    return result_id

def get_result_file(result_id):
    config = configparser.ConfigParser()
    config.read(global_var())
    url = config["API_CRPT"]["url_download_result_file"]+result_id+'/file'
    bearer = get_CRPT_token()
    headers = {'Authorization': 'Bearer ' + bearer}
    downloaded_file_path = str(config["TELEGRAM_BOT"]["file_path"]+"result_"+result_id+".zip")
    file = open (downloaded_file_path, 'wb')
    request = requests.get(url, headers=headers)
    file.write(request.content)
    file.close()
    return downloaded_file_path