def handler(event, context):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
        "body": "",
    }
