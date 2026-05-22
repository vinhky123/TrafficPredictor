import os

import boto3


def handler(event, context):
    table_name = os.environ["CONNECTIONS_TABLE"]
    connection_id = event["requestContext"]["connectionId"]

    ddb = boto3.resource("dynamodb")
    table = ddb.Table(table_name)

    try:
        table.delete_item(Key={"connection_id": connection_id})
    except Exception:
        pass

    return {"statusCode": 200}
