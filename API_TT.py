from GLOBAL_VAR import global_var
def check_outs_doc_status(doc_number):
    import requests
    import configparser
    config = configparser.ConfigParser()
    config.read(global_var())
    url = config["API_TT"]["url_check_out_doc"]
    token_path = config["API_TT"]["ns_token_path"]
    token_file = open(token_path, 'r', encoding='utf_16')
    bearer = token_file.read()
    token_file.close()
    headers = {'X-Auth-Token': 'Bearer ' + bearer, 'Content-Type': 'application/json', 'x-warehouse-name': 'NS_VSEVO'}
    params = {'documentNumber': doc_number}
    request = requests.get(url, headers=headers, params=params)
    guid = request.json()['content'][0]['guid']
    checkStatus = request.json()['content'][0]['checkStatus']
    action = request.json()['content'][0]['action']
    outDocType = request.json()['content'][0]['outDocType']
    data_for_user = {'guid': guid, 'checkStatus': checkStatus, 'action': action, 'outDocType': outDocType}
    return data_for_user

def get_CRPT_token(business_unit='NS'):
    import requests
    import configparser
    config = configparser.ConfigParser()
    config.read(global_var())
    url = config["API_TT"]["url_get_CRPT_token"]
    if business_unit == 'NT':
        token_path = config["API_TT"]["nt_token_path"]
    else:
        token_path = config["API_TT"]["ns_token_path"]
    token_file = open(token_path, 'r', encoding='utf_16')
    bearer = token_file.read()
    token_file.close()
    headers = {'X-Auth-Token': 'Bearer ' + bearer, 'Content-Type': 'application/json'}
    request = requests.get(url, headers=headers)
    token = request.json()['token']
    return token

def nt_mc_status_update (mc_list):
    import requests
    import configparser
    import time
    import json
    config = configparser.ConfigParser()
    config.read(global_var())
    url = config["API_TT"]["url_mc_status_update"]
    token_path = config["API_TT"]["nt_token_path"]
    mc_amount_to_update = int(config["API_TT"]["mc_amount_to_update"])
    status = config["API_TT"]["mrkSystemStatus"]
    warehouse = config["API_TT"]["warehouse"]
    token_file = open(token_path, 'r', encoding='utf_16')
    bearer = token_file.read()
    token_file.close()
    data = {}
    count = 1
    num_of_runs = len(mc_list) // mc_amount_to_update + 1
    for run in range(num_of_runs):
        headers = {'X-Auth-Token': 'Bearer ' + bearer, 'Content-Type': 'application/json', 'x-warehouse-name': warehouse}
        body = {"mrkSystemStatus":status, "searchRequest": {"uits": mc_list[(count - 1) * mc_amount_to_update:count * mc_amount_to_update]}}
        req = requests.post(url, headers=headers, data=json.dumps(body))
        data_run = json.loads(req.text)
        data = {**data, **data_run}
        count = count + 1
        time.sleep(5)
    return data