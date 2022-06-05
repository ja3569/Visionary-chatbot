import json
import boto3
import datetime
import requests
from decimal import *
from botocore.exceptions import ClientError

center_ids ={}
template = {'objectid': None, 'service_type': None, 'walk_in': None, 'insurance': None, 'facility_name': None, 'address': None, 'zip_code': None, 'zip_code': None, 'phone': None}
dynamodb= boto3.resource(service_name='dynamodb', region_name="us-east-1")
table = dynamodb.Table('VaccinationCenter')
    
def insert(json_response, json_template):
    for item in json_response:
        if item in template.keys():
            if item == "address": 
                json_template["address"] = str(json_response["address"]) + "," + str(json_response["borough"]) + "," + str(json_response["city"])
            else:
                json_template[item] = str(json_response[item])
    response = table.put_item(Item=json_template)
    return response

def lambda_handler(event=None, context=None):
    req = requests.get("https://data.cityofnewyork.us/resource/w9ei-idxz.json")
    json_req = req.json()
    for i in range(0, len(json_req)):
        center = json_req[i]
        if center['objectid'] not in center_ids:
            insert(center, template)
            center_ids[center['objectid']] = 0
    
    

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
