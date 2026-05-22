import json
import logging
import os

import boto3

logger = logging.getLogger(__name__)


def handler(event, context):
    connections_table_name = os.environ["CONNECTIONS_TABLE"]
    api_gw_endpoint = os.environ["API_GW_ENDPOINT"]

    sns_msg = json.loads(event["Records"][0]["Sns"]["Message"])

    ddb = boto3.resource("dynamodb")
    table = ddb.Table(connections_table_name)

    resp = table.scan()
    connections = resp.get("Items", [])

    client = boto3.client("apigatewaymanagementapi", endpoint_url=api_gw_endpoint)

    data = json.dumps({"type": "update", "data": sns_msg})
    sent = 0

    for item in connections:
        try:
            client.post_to_connection(
                ConnectionId=item["connection_id"],
                Data=data,
            )
            sent += 1
        except client.exceptions.GoneException:
            table.delete_item(Key={"connection_id": item["connection_id"]})
        except Exception as e:
            logger.warning("Failed to send to connection %s: %s", item["connection_id"], e)

    logger.info("Sent notifications to %d/%d connections", sent, len(connections))

    return {"sent": sent}
