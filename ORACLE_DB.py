def select_MC_by_UPD(UPD_number):
    import cx_Oracle
    import configparser
    config = configparser.ConfigParser()  # создаём объекта парсера
    config.read("C:/Users/arnovikov/OneDrive - Nokian Tyres/Documents/_Работа/OTM Project/MC_Check/settings.ini")
    conn_str = config["ORACLE_DB"]["conn_str"]
    conn = cx_Oracle.connect(conn_str)
    mc_list = []
    #print(conn.version)
    str1 = """SELECT MC from xxnt.xxinv060_customer_trx_mc WHERE CUSTOMER_TRX_ID in (select CUSTOMER_TRX_ID from ra_customer_trx_all where TRX_NUMBER in ('"""
    str2 = """')) and org_id = 82"""
    c = conn.cursor()
    c.execute(str1+UPD_number+str2)
    for row in c:
        mc_list.append(row[-1])
    conn.close()
    return mc_list

def UPD_data(UPD_number):
    import cx_Oracle
    import configparser
    config = configparser.ConfigParser()  # создаём объекта парсера
    config.read("C:/Users/arnovikov/OneDrive - Nokian Tyres/Documents/_Работа/OTM Project/MC_Check/settings.ini")
    conn_str = config["ORACLE_DB"]["conn_str"]
    conn = cx_Oracle.connect(conn_str)
    str1 = """
            select t.trx_number, t.trx_date, p.party_name, sum(tl.quantity_invoiced) as TYRES_QTY
            from ra_customer_trx_all t , ra_customer_trx_lines_all tl, hz_cust_accounts ca, hz_parties p
            where 1=1 
            and t.org_id = 82
            and t.CUSTOMER_TRX_ID = tl.CUSTOMER_TRX_ID
            and t.SOLD_TO_CUSTOMER_ID = ca.CUST_ACCOUNT_ID
            and ca.PARTY_ID = p.PARTY_ID
            and t.TRX_NUMBER = '
            """
    str2 = """' group by t.trx_number, t.trx_date, p.party_name"""
    c = conn.cursor()
    c.execute(str1 + UPD_number + str2)
    columns = [col[0] for col in c.description]
    c.rowfactory = lambda *args: dict(zip(columns, args))
    data = c.fetchall()
    conn.close()
    return data