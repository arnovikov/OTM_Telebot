from GLOBAL_VAR import global_var
def IC_STATISTIC (date_from, date_to):
    import cx_Oracle
    import configparser
    import requests
    import json
    import subprocess
    import datetime
    import os
    import openpyxl
    config = configparser.ConfigParser()
    config.read(global_var())
    conn_str = config["ORACLE_DB"]["conn_str"]
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
    date_from = date_from.strftime ('%d-%b-%y')
    date_to = date_to.strftime ('%d-%b-%y')
    file_path = str(config["CREATE_EXCEL"]["file_path"]) + date_from + '-' + date_to + '_ic_statistic_result.xlsx'

    str1 = """
            SELECT FILE_NAME, DOCUMENT_NUMBER, DOCUMENT_DATE, CREATION_DATE as document_creation_date FROM XXFIN230_EDOC_OUTBOUND_INT1 
            where legal_entity_id = 'NT'
            and DOC_TYPE in ('УПД') 
            and file_name like '%MARK%'
            and trunc(document_date) between '"""

    str2 = """' AND '"""
    str3 = """' order by DOCUMENT_NUMBER, CREATION_DATE desc"""

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(('FILE_NAME', 'DOCUMENT_NUMBER', 'DOCUMENT_DATE', 'DOCUMENT_CREATION_DATE', 'DOCUMENT_DATE_GISMT','DOC_STATUS_GISMT'))
    dtime = datetime.timedelta(hours=3)
    conn = cx_Oracle.connect(conn_str)
    c = conn.cursor()
    c.execute(str1+str(date_from)+str2+str(date_to)+str3)
    for row in c:
        row = list(row)
        req = requests.get(url2 + row[0] + '/body', headers=headers)
        if str(req) == '<Response [200]>':
            doc_status = json.dumps(req.json()['downloadStatus'])
            receipt_at = datetime.datetime.strptime(json.dumps(req.json()['receivedAt'])[1:20], '%Y-%m-%dT%H:%M:%S')
        else:
            doc_status = '-'
            receipt_at = '-'
        if receipt_at != '-':
            receipt_at = receipt_at + dtime
        row.append(receipt_at)
        row.append(doc_status)
        ws.append((row))
    conn.close()
    ws.auto_filter.ref = ws.dimensions
    wb.save(file_path)
    wb.close()
    return file_path

