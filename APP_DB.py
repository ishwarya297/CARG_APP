# import json
# import boto3
# from botocore.exceptions import ClientError
# from datetime import datetime
# import logging
# import psycopg2
# import os

# from dotenv import load_dotenv

# load_dotenv()

# REGION_NAME = os.environ.get('REGION_NAME')
# SECRET_NAME = os.environ.get('SECRET_NAME')

# def get_secret():
#     region_name = REGION_NAME
#     secret_name = SECRET_NAME
#     session = boto3.session.Session()
#     client = session.client(service_name='secretsmanager', region_name=region_name)
#     try:
#         get_secret_value_response = client.get_secret_value(SecretId=secret_name)
#         print("Successfully retrieved the secret from AWS Secrets Manager.")
#     except ClientError as e:
#         raise e
#     return json.loads(get_secret_value_response['SecretString'])

# def connect_db():
#     try:
#         db_credentials = get_secret()
#         conn = psycopg2.connect(
#             dbname=db_credentials["dbname"],
#             user=db_credentials["username"],
#             password=db_credentials["password"],
#             host=db_credentials["proxy"],
#             port=db_credentials["port"]
#         )
#         logging.info("Database connection established.")
#         return conn
#     except psycopg2.Error as e:
#         logging.error(f"Database connection error: {e}")
#         return None
        
# # Prevent duplicate alerts per asset+control+ACTIVE status
# def alert_db_insert(asset_id, controlcheck_id, configname, resourcetype, assetname, accountid, compliancetype="NON_COMPLIANT"):
#     remedystatus = "ACTIVE"
#     createdby = "ccs"
#     createdon = datetime.datetime.now()
#     resultrecordedtime = datetime.datetime.now()
#     connection = get_db_connection()
#     cursor = connection.cursor()
#     # Check for existing alert (all unique params)
#     cursor.execute("""
#         SELECT id FROM ccsadminnew.ccsazurealerts
#         WHERE assetname_id = %s AND controlcheck_id = %s AND resourcetype = %s AND accountid = %s AND compliancetype = %s AND remedystatus = %s
#     """, (asset_id, controlcheck_id, resourcetype, accountid, compliancetype, remedystatus))

#     if cursor.fetchone():
#         print(f"[SKIP] Duplicate alert for {assetname} - {controlcheck_id}")
#     else:
#         cursor.execute("""
#             INSERT INTO ccsadminnew.ccsazurealerts (
#                 assetname_id, controlcheck_id, configrulename, resourcetype, assetname, accountid,
#                 compliancetype, remedystatus, createdby, createdon,resultrecordedtime
#             ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#         """, (asset_id, controlcheck_id, configname, resourcetype, assetname, accountid,
#               compliancetype, remedystatus, createdby, createdon,resultrecordedtime))
#         connection.commit()
#         print(f"[INSERTED] Alert for {assetname} - {controlcheck_id}")
#     cursor.close()
#     connection.close()

# def insert_noncompliance_results_to_db(results, project_id):
#     try:
#         print('Inserting compliance results into database')
#         conn = connect_db()
#         print("Successfully connected to the PostgreSQL database.")
#         cursor = conn.cursor()

#         data = []
#         for result in results:
#             status = result['Status'].lower()
#             if status not in ['active', 'inactive']:
#                 print("Status must be either 'active' or 'inactive'")
#                 continue

#             opened = result.get('OpenedAt', None)
#             if isinstance(opened, int):
#                 opened_at_dt = datetime.utcfromtimestamp(opened)
#                 opened_at = opened_at_dt.strftime('%Y-%m-%d %H:%M:%S')
#             else:
#                 opened_at = None

#             if status == 'active' and (opened_at is None or opened_at == 0):
#                 print("Skipping alert as it is open and OpenedAt is 0 or missing")
#                 continue

#             data.append({
#                 "p_assetname": result.get('AssetId', ''),
#                 "p_configrulename": result.get('PolicyName', ''),
#                 "p_resourcetype": result.get('Resource', ''),
#                 "p_compliancetype": "NON_COMPLIANT",
#                 "p_resultrecordedtime": opened_at or '',
#                 "p_accountid": project_id,
#                 "p_remedystatus": result.get('Status', ''),
#                 "p_region": result.get('ResourceRegion', '').lower()
#             })

#         if data:
#             print("JSON Data being passed to the stored procedure:")
#             print(json.dumps(data, indent=2))
#             try:
#                 cursor.execute("CALL ccsadminnew.sp_insert_ccsazurealerts(%s)", (json.dumps(data),))
#                 conn.commit()
#             except Exception as db_e:
#                 print(f"DB Error: {db_e}")
#                 import traceback
#                 traceback.print_exc()

#         cursor.close()
#         conn.close()
#     except Exception as e:
#         print(f"An error occurred: {e}")
#         import traceback
#         traceback.print_exc()

import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

REGION_NAME = os.environ.get('REGION_NAME')
SECRET_NAME = os.environ.get('SECRET_NAME')

def get_secret():
    region_name = REGION_NAME
    secret_name = SECRET_NAME
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        print("Successfully retrieved the secret from AWS Secrets Manager.")
    except ClientError as e:
        raise e
    return json.loads(get_secret_value_response['SecretString'])

def get_db_connection():
    db_credentials = get_secret()
    conn = psycopg2.connect(
        dbname=db_credentials["dbname"],
        user=db_credentials["username"],
        password=db_credentials["password"],
        host=db_credentials["proxy"],
        port=db_credentials["port"]
    )
    return conn

# Prevent duplicate alerts per asset+control+ACTIVE status
def alert_db_insert(asset_id, controlcheck_id, configname, resourcetype, assetname, accountid, compliancetype="NON_COMPLIANT"):
    remedystatus = "ACTIVE"
    createdby = "ccs"
    createdon = datetime.now()
    resultrecordedtime = datetime.now()
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id FROM ccsadminnew.ccsazurealerts
        WHERE assetname_id = %s AND controlcheck_id = %s AND resourcetype = %s AND accountid = %s AND compliancetype = %s AND remedystatus = %s
    """, (asset_id, controlcheck_id, resourcetype, accountid, compliancetype, remedystatus))
    if cursor.fetchone():
        print(f"[SKIP] Duplicate alert for {assetname} - {controlcheck_id}")
    else:
        cursor.execute("""
            INSERT INTO ccsadminnew.ccsazurealerts (
                assetname_id, controlcheck_id, configrulename, resourcetype, assetname, accountid,
                compliancetype, remedystatus, createdby, createdon, resultrecordedtime
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (asset_id, controlcheck_id, configname, resourcetype, assetname, accountid,
              compliancetype, remedystatus, createdby, createdon, resultrecordedtime))
        connection.commit()
        print(f"[INSERTED] Alert for {assetname} - {controlcheck_id}")
    cursor.close()
    connection.close()

def get_asset_id_by_assetname(assetname):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT assetname_id FROM ccsadminnew.ccsazureassets WHERE assetname = %s", (assetname,))
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    if result:
        return result[0]
    else:
        return None

def get_controlcheck_id_by_name(configrulename):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT controlcheck_id
        FROM ccsadminnew.ccscontrolcheckmaster
        WHERE LOWER(TRIM(rulename)) = LOWER(TRIM(%s))
        """,
        (configrulename,)
    )
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    if result:
        return result[0]
    else:
        print(f"[WARN] controlcheck_id not found for rule: {configrulename}")
        return None

def insert_noncompliance_results_to_db(results, project_id):
    try:
        print('Inserting compliance results into database')
        conn = get_db_connection()
        print("Successfully connected to the PostgreSQL database.")
        cursor = conn.cursor()

        data = []
        for result in results:
            status = result['Status'].lower()
            if status not in ['active', 'inactive']:
                print("Status must be either 'active' or 'inactive'")
                continue

            opened = result.get('OpenedAt', None)
            if isinstance(opened, int):
                opened_at_dt = datetime.utcfromtimestamp(opened)
                opened_at = opened_at_dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                opened_at = None

            if status == 'active' and (opened_at is None or opened_at == 0):
                print("Skipping alert as it is open and OpenedAt is 0 or missing")
                continue

            data.append({
                "p_assetname": result.get('AssetId', ''),
                "p_configrulename": result.get('PolicyName', ''),
                "p_resourcetype": result.get('Resource', ''),
                "p_compliancetype": "NON_COMPLIANT",
                "p_resultrecordedtime": opened_at or '',
                "p_accountid": project_id,
                "p_remedystatus": result.get('Status', ''),
                "p_region": result.get('ResourceRegion', '').lower()
            })

        if data:
            print("JSON Data being passed to the stored procedure:")
            print(json.dumps(data, indent=2))
            try:
                cursor.execute("CALL ccsadminnew.sp_insert_ccsazurealerts(%s)", (json.dumps(data),)
                )
                conn.commit()
            except Exception as db_e:
                print(f"DB Error: {db_e}")
                import traceback
                traceback.print_exc()

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
