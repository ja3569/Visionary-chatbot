import json
import math
import datetime
import logging
import boto3
import os
import time
import dateutil.parser
sqs = boto3.client('sqs')
queue_url = 'https://sqs.us-east-1.amazonaws.com/445215740396/visionarysqs'

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


""" --- Helper functions --- """
def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


""" --- Helper Functions --- """


def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')


def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }
    
def pullMessage(sqs, queue_url):
    response = sqs.receive_message(
        QueueUrl=queue_url,
        AttributeNames=['SentTimestamp'],
        MaxNumberOfMessages=1,
        MessageAttributeNames=['All'],
        VisibilityTimeout=0,
        WaitTimeSeconds=0
        )
    return response

def getMessage(response1):
    message = response1['Messages'][0]
    rh = message['ReceiptHandle']
    location = message['MessageAttributes']['Location']['StringValue']
    zip_code = message['MessageAttributes']['ZipCode']['StringValue']
    cuisine = message['MessageAttributes']['Cuisine']['StringValue']
    dining_date = message['MessageAttributes']['DiningDate']['StringValue']
    message = ["Below are the top three {} restaurant suggestions on {}. Enjoy your meal!\n\n".format(cuisine, dining_date), str(cuisine), str(zip_code), rh]
    return message
    
def deleteMsg(message, sqs, queue_url):
    receipt_handle = message
    response = sqs.delete_message(queue_url, ReceiptHandle=receipt_handle)
    return response
    
def deleteM():
    while True:
        response = sqs.receive_message(
            QueueUrl= queue_url,
            AttributeNames=['ALL'],
            MaxNumberOfMessages=1)
        if len(response.get('Messages', [])) == 0:
            break
        for msg in response['Messages']:
            message=json.loads(response['Messages'][0]['Body'])
            delete_message= sqs.delete_message(QueueUrl=QueueUrl, ReceiptHandle=msg["ReceiptHandle"])

def pullDB(i, db_id):
    db = boto3.resource('dynamodb')
    table = db.Table('yelp-restaurants')
    response = table.get_item(Key={'id': db_id})["Item"]
    res = "{}. {}, located at {}\n".format(i, response['name'], response['address'])
    return res
    
def searchZipCode(zip_code):
    db = boto3.resource('dynamodb')
    table = db.Table('yelp-restaurants')
    response = table.scan()
    idList = []
    for item in response['Items']:
        if item['zip_code'] == zip_code:
            idList.append(item['id'])
    return idList

def printMsg():
    response1 = pullMessage(sqs, queue_url)
    msg = getMessage(response1)
    #deleteMsg(response1['Messages'][0]['ReceiptHandle'], sqs, queue_url)
    
    idList = searchZipCode(msg[2])
    messag = msg[0] + "\n"

    for i in range(3):
        messag = messag + pullDB(str(i+1), idList[i]) + "\n"
    return messag

def validate_dining_suggestion(intent_request):
    location = intent_request["Location"]
    zip_code = get_slots(intent_request)["ZipCode"]
    cuisine = intent_request["Cuisine"]
    dining_date = intent_request["DiningDate"]
    
    if location is not None:
        if location.lower() not in ['manhattan', 'uptown', 'downtown', 'midtown', 'bronx', 'brooklyn', 'queens', 'nyc', 'new york']:
            return build_validation_result(False,
                                           'Location',
                                           '{} is out of service, please enter another location, such as Manhattan'.format(location))

    if cuisine is not None:
        if cuisine.lower() not in ["chinese", "indian"]:
            return build_validation_result(False,
                                           'Cuisine',
                                           '{} is not available, please enter another cuisine, such as Indian'.format(cuisine))
    
    if dining_date is not None:
        if datetime.datetime.strptime(dining_date, '%Y-%m-%d').date() < datetime.date.today():
            return build_validation_result(False, 'DiningDate', 'Your chosen date is in the past or not valid! Try 2022-4-26')
     
    return build_validation_result(True, None, None)

""" --- Functions that control the bot's behavior --- """

def greetings(intent_request):
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Hi there, how can I help? (Try "hungry")'})
                  
                  
def thank_you(intent_request):
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'You are welcome!'})
    

def dining_suggestion(intent_request):
    location = get_slots(intent_request)["Location"]
    zip_code = get_slots(intent_request)["ZipCode"]
    cuisine = get_slots(intent_request)["Cuisine"]
    dining_date = get_slots(intent_request)["DiningDate"]
    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':
        slots = get_slots(intent_request)

        validation_result = validate_dining_suggestion(intent_request['currentIntent']['slots'])
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])
        return delegate(intent_request['sessionAttributes'], get_slots(intent_request))
    
    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageAttributes={
           'Location': {
                'DataType': 'String',
                'StringValue': location
            },
            'ZipCode' : {
                'DataType': 'String',
                'StringValue': zip_code
            },
            'Cuisine': {
                'DataType': 'String',
                'StringValue': cuisine
            },
            'DiningDate': {
                'DataType': 'String',
                'StringValue': dining_date
            }
        },
        MessageBody=('visionarysqs')
    )
    msg = printMsg()
    return close(intent_request['sessionAttributes'], 'Fulfilled',
                     {'contentType': 'PlainText',
                      'content': str(msg)})


""" --- Intents --- """


def dispatch(intent_request):
    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    if intent_name == 'GreetingIntent':
        return greetings(intent_request)
    elif intent_name == 'ThankYouIntent':
        return thank_you(intent_request)
    elif intent_name == 'DiningSuggestionIntent':
        return dining_suggestion(intent_request)
    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):

    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)

