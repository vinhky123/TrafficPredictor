import os
from datetime import datetime

import boto3


def handler(event, context):
    table_name = os.environ["CONNECTIONS_TABLE"]
    connection_id = event["requestContext"]["connectionId"]

    ddb = boto3.resource("dynamodb")
    table = ddb.Table(table_name)

    table.put_item(Item={
        "connection_id": connection_id,
        "connected_at": datetime.utcnow().isoformat(),
        "ttl": int(datetime.utcnow().timestamp()) + 86400,
    })

    return {"statusCode": 200}
