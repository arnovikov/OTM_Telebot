from GLOBAL_VAR import global_var
def create_excel (mc_list,mc_data,file_name):
    import openpyxl
    import configparser
    config = configparser.ConfigParser()
    config.read(global_var())
    file_path = str(config["CREATE_EXCEL"]["file_path"])+file_name
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(('cis','cis_status','gtin','owner_INN','owner_name','producer_INN','producer_name','emissionDate','emissionType','introducedDate','lastDocId','statusEx'))
    for cell in mc_list:
        if cell in mc_data.keys():
            ws.append((cell, mc_data.get(cell).get('status'), mc_data.get(cell).get('gtin'), mc_data.get(cell).get('ownerInn'), mc_data.get(cell).get('ownerName'), mc_data.get(cell).get('producerInn'), mc_data.get(cell).get('producerName'), mc_data.get(cell).get('emissionDate'), mc_data.get(cell).get('emissionType'), mc_data.get(cell).get('introducedDate'), mc_data.get(cell).get('lastDocId'), mc_data.get(cell).get('statusEx')))
        else:
            ws.append((cell,'-','-','-','-','-','-','-','-','-','-','-'))
    ws.auto_filter.ref = ws.dimensions
    wb.save(file_path)
    wb.close()
    return file_path

