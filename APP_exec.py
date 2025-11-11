# API_execution.py — Azure API Management checks (307 & 389)
import logging
import boto3    
import requests
from API_policy import *  # p307, p389, p307_send, p389_send
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from DatabaseLayer import (
    get_azure_parameters,
    insert_noncompliance_results_to_db,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

NON_STATUS = "ACTIVE"
COM_STATUS = "INACTIVE"

def list_apim_services(subscription_id, headers):
    url = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.ApiManagement/service?api-version=2019-12-01"
    r = requests.get(url, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json().get('value', [])

def get_diagnostic_settings(resource_id, headers):
    url = f"https://management.azure.com/{resource_id}/providers/microsoft.insights/diagnosticSettings?api-version=2021-05-01-preview"
    r = requests.get(url, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json().get('value', [])

def get_resource_locks(resource_id, headers):
    # Ensure resource_id starts with '/' for correct URL formation
    if not resource_id.startswith('/'):
        resource_id = '/' + resource_id
    url = f"https://management.azure.com{resource_id}/providers/Microsoft.Authorization/locks?api-version=2016-09-01"
    r = requests.get(url, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json().get('value', [])

def main():
    try:
        #create_dynamo_table_if_not_exists()
        accounts = get_azure_parameters()

        for (subscription_id, headers, _credential) in accounts:
            logging.info(f"Processing subscription: {subscription_id}")

            non_307, com_307 = [], []
            non_389, com_389 = [], []
            non_467, com_467 = [], []

            services = list_apim_services(subscription_id, headers)
            for svc in services:
                resource_id = svc.get('id')
                name        = svc.get('name')
                location    = svc.get('location')
                vnet_type   = (svc.get('properties') or {}).get('virtualNetworkType', 'None')

                # Policy 307
                if vnet_type == "None":
                    non_307.append(p307(name, location, NON_STATUS, subscription_id))
                else:
                    com_307.append(p307(name, location, COM_STATUS, subscription_id))

                # Policy 389
                try:
                    diag = get_diagnostic_settings(resource_id, headers)
                    if len(diag) > 0:
                        com_389.append(p389(name, location, COM_STATUS, subscription_id))
                    else:
                        non_389.append(p389(name, location, NON_STATUS, subscription_id))
                except requests.HTTPError as e:
                    logging.warning(f"Diagnostics fetch failed for {name} ({resource_id}): {e}")
                    non_389.append(p389(name, location, NON_STATUS, subscription_id))

                # Policy 467
                try:
                    locks = get_resource_locks(resource_id, headers)
                    if len(locks) > 0:
                        com_467.append(p467(name, location, COM_STATUS, subscription_id))
                    else:
                        non_467.append(p467(name, location, NON_STATUS, subscription_id))
                except requests.HTTPError as e:
                    logging.warning(f"Resource locks fetch failed for {name} ({resource_id}): {e}")
                    non_467.append(p467(name, location, NON_STATUS, subscription_id))


            p307_send(non_307, com_307)
            p389_send(non_389, com_389)
            p467_send(non_467, com_467)  # Placeholder for policy 467

            results_to_insert = non_307 + non_389 + non_467
            if results_to_insert:
                logging.info(f"Inserting non-compliance results into DB for sub {subscription_id} (count={len(results_to_insert)})")
                insert_noncompliance_results_to_db(results_to_insert, subscription_id)
            else:
                logging.info(f"All API Management checks compliant for subscription: {subscription_id}")

    except Exception as e:
        logging.error(f"Execution error: {e}")

if __name__ == '__main__':
    main()
