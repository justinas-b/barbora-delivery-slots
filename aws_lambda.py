import os

barbora = Barbora(username=os.getenv("username"), password=os.getenv("password"), msteams_webhook=os.getenv("webhook"))


def lambda_handler(event, context):
    barbora.run_once()
    return {'statusCode': 200, 'body': json.dumps('Barbora query completed!')}
