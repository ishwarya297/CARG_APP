from datetime import date
from datetime import datetime
 
t=datetime.now()
x = t.replace(microsecond=0)
Time = int(datetime.timestamp(x))
 
Resource="microsoft.apimanagement"
Assets = "Service"

def output(Policyname,location,asset_id,Status,Description,Recommendation,subscription_id):
    account_id=subscription_id
    if Status=="ACTIVE":  
        json_obj={
                    "Source" : "Native service - Azure",
                    "PolicyName": Policyname,
                    "CloudType": "Azure",
                    "CloudAccountId": subscription_id,
                    "ResourceRegion": location,
                    "Resource": Resource,
                    "Assets": Assets,
                    "AssetId": asset_id,
                    "Status": Status,
                    "OpenedAt" : Time,
                    "ClosedAt": "Nil",
                    "Description": Description,
                    "Recommendation": Recommendation
                }
    else:
        json_obj={
                    "Source" : "Native service - Azure",
                    "PolicyName": Policyname,
                    "CloudType": "Azure",
                    "CloudAccountId": subscription_id,
                    "ResourceRegion": location,
                    "Resource": Resource,
                    "Assets": Assets,
                    "AssetId": asset_id,
                    "Status": Status,
                    "OpenedAt" : "Nil",
                    "ClosedAt": Time,
                    "Description": Description,
                    "Recommendation": Recommendation
                }
    return json_obj
 
def p307(asset_id,location,Status,subscription_id):
    Policyname = "API Management services should use a virtual network"
    Description = "Deploying your API management service inside a virtual network allows more security and control over the network access"  
    Recommendation  = "1) Ensure that your API management service is upgraded to premium tier 2) Navigate to the virtual network section and update your virtual network"   
    return output(Policyname,location,asset_id,Status,Description,Recommendation,subscription_id)
 
def p389(asset_id,location,Status,subscription_id):
    Policyname = "Ensure that a 'Diagnostics Setting' exists for API Management Service"
    Description = "Enable Diagnostic settings for exporting activity logs. Diagnostic setting are available for each individual resources within a subscription. Settings should be configured for all appropriate resources for your environment."  
    Recommendation  = "From Azure Console 1. Click on the resource that has a diagnostic status of disabled 2. Select Add Diagnostic Settings 3. Enter a Diagnostic setting name 4. Select the appropriate log, metric, and destination. (This may be Log Analytics/Storage account or Event Hub) 5. Click save Repeat these step for all resources as needed. Default Value: By default, diagnostic setting is not set."   
    return output(Policyname,location,asset_id,Status,Description,Recommendation,subscription_id)

def p307_send(non_compliant,compliant):
    print("Sending non-compliant data for Policy 307:")
    for item in non_compliant,compliant:
        print(item)

def p389_send(non_compliant,compliant):
    print("Sending non-compliant data for Policy 389:")
    for item in non_compliant,compliant:
        print(item)

def p467(asset_id, location, Status, subscription_id):
    Policyname = "Ensure that Resource Locks are set for API Management Services"
    Description = ("Resource locks prevent accidental deletion or modification of critical Azure resources. "
                   "Setting locks on API Management Services ensures that these resources are protected from unintended changes.")
    Recommendation = ("1) Go to the Azure portal\n"
                      "2) Navigate to your API Management Service resource\n"
                      "3) In the left menu, select 'Locks'\n"
                      "4) Add a lock (Read-only or Delete) to protect the resource\n"
                      "5) Repeat for all critical API Management Services.")
    return output(Policyname, location, asset_id, Status, Description, Recommendation, subscription_id)

def p467_send(non_compliant, compliant):
    print("Sending non-compliant data for Policy 467:")
    for item in non_compliant:
        print(item)
