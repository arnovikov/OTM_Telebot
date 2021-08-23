from GLOBAL_VAR import global_var
def select_MC_by_UPD(UPD_number):
    import cx_Oracle
    import configparser
    config = configparser.ConfigParser()
    config.read(global_var())
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
    config = configparser.ConfigParser()
    config.read(global_var())
    conn_str = config["ORACLE_DB"]["conn_str"]
    conn = cx_Oracle.connect(conn_str)
    str1 = """
            select t.trx_number as TRX_Number, decode(t.attribute4,'C','УКД','A','УПДи','УПД') as TRX_Type, trunc(t.trx_date) as UPD_DATE, p.party_name as CUSTOMER_NAME, sum(tl.quantity_invoiced) as TYRES_QTY
            from ra_customer_trx_all t , ra_customer_trx_lines_all tl, hz_cust_accounts ca, hz_parties p
            where 1=1 
            and t.org_id = 82
            and t.CUSTOMER_TRX_ID = tl.CUSTOMER_TRX_ID
            and t.SOLD_TO_CUSTOMER_ID = ca.CUST_ACCOUNT_ID
            and ca.PARTY_ID = p.PARTY_ID
            and t.TRX_NUMBER = '"""
    str2 = """' group by t.trx_number, t.trx_date, p.party_name"""
    c = conn.cursor()
    c.execute(str1 + UPD_number + str2)
    columns = [col[0] for col in c.description]
    c.rowfactory = lambda *args: dict(zip(columns, args))
    data = c.fetchall()
    conn.close()
    return data

def UIT_data (uit):
    import cx_Oracle
    import configparser
    config = configparser.ConfigParser()
    config.read(global_var())
    conn_str = config["ORACLE_DB"]["conn_str"]
    conn = cx_Oracle.connect(conn_str)
    str1 = """
            select t.trx_number as UPD_Number, trunc(t.trx_date) as UPD_DATE, p.party_name as CUSTOMER_NAME, i.segment1 as ITEM_CODE, mc.SOURCE_REFERENCE, mc.SOURCE_TYPE 
            from xxnt.xxinv060_customer_trx_mc mc, ra_customer_trx_all t , hz_cust_accounts ca, hz_parties p, mtl_system_items i
            where mc.customer_trx_id = t.customer_trx_id and mc.org_id = t.org_id 
            and mc.org_id in (82)
            and i.ORGANIZATION_ID = 110
            and mc.INVENTORY_ITEM_ID = i.INVENTORY_ITEM_ID
            and t.SOLD_TO_CUSTOMER_ID = ca.CUST_ACCOUNT_ID
            and ca.PARTY_ID = p.PARTY_ID
            and mc.MC = q'{"""
    str2 = """}' order by mc.MC, mc.creation_date asc"""
    c = conn.cursor()
    c.execute(str1 + uit + str2)
    columns = [col[0] for col in c.description]
    c.rowfactory = lambda *args: dict(zip(columns, args))
    data = c.fetchall()
    conn.close()
    return data

def EDO_file_name(doc_num):
    import cx_Oracle
    import configparser
    config = configparser.ConfigParser()
    config.read(global_var())
    conn_str = config["ORACLE_DB"]["conn_str"]
    conn = cx_Oracle.connect(conn_str)
    str1 = """
                SELECT max(file_name) keep (dense_rank last order by creation_date)
                FROM XXFIN230_EDOC_OUTBOUND_INT1  
                WHERE substr(ext_doc_group_id,3,11) in  ('"""
    str2 = """') and DOC_TYPE  in ('УПД','УКД')"""
    c = conn.cursor()
    c.execute(str1 + doc_num + str2)
    file_name = c.fetchone()
    conn.close()
    return file_name[0]