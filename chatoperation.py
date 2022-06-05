import json
import boto3

def lambda_handler(event, context):
    client = boto3.client('lex-runtime')
    msg_from_user = event['messages'][0]['unstructured']['text']

    response = client.post_text(botName='chat_operation',
                                botAlias='test',
                                userId='200',
                                sessionAttributes={},
                                requestAttributes={},
                                inputText=msg_from_user)
    
    
    msg_from_lex = response['message']
    if msg_from_lex:
        print("Message from Chatbot: {msg_from_lex}")
        resp = {
            'statusCode': 200,
            'messages': [
                {
                    "type": "unstructured",
                    "unstructured": {
                        "text": response['message']
                    }
                }
            ]
                
        }

    return resp
        


