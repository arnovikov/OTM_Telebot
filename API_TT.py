from GLOBAL_VAR import global_var
def check_outs_doc_status(doc_number):
    import requests
    import configparser
    config = configparser.ConfigParser()
    config.read(global_var())
    url = config["API_TT"]["url_check_out_doc"]
    token_path = config["API_TT"]["token_path"]
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

def get_CRPT_token():
    import requests
    import configparser
    config = configparser.ConfigParser()
    config.read(global_var())
    url = config["API_TT"]["url_get_CRPT_token"]
    token_path = config["API_TT"]["token_path"]
    token_file = open(token_path, 'r', encoding='utf_16')
    bearer = token_file.read()
    token_file.close()
    headers = {'X-Auth-Token': 'Bearer ' + bearer, 'Content-Type': 'application/json'}
    request = requests.get(url, headers=headers)
    token = request.json()['token']
    return token
