import json
import os
import urllib3

http = urllib3.PoolManager()
WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL', 'https://httpbin.org/post')

def lambda_handler(event, context):
    """
    AWS Lambda Serverless Alert Handler (Section 10.2 DEVOPSPRESUB Specification)
    Triggered by DynamoDB stream, SQS, or webhook event when budget limits are updated or breached.
    """
    alerts_dispatched = 0
    for record in event.get('Records', []):
        if record.get('eventName') in ['INSERT', 'MODIFY']:
            new_img = record.get('dynamodb', {}).get('NewImage', {})
            category = new_img.get('category', {}).get('S', 'General')
            spent = float(new_img.get('spent', {}).get('N', 0.0))
            limit = float(new_img.get('limit', {}).get('N', 0.0))
            
            if spent > limit and limit > 0:
                overrun = spent - limit
                msg = {
                    "text": f"🚨 BUDGET ALERT: Category '{category}' exceeded limit by ${overrun:.2f}! Spent: ${spent:.2f}, Limit: ${limit:.2f}."
                }
                try:
                    http.request(
                        'POST',
                        WEBHOOK_URL,
                        body=json.dumps(msg),
                        headers={'Content-Type': 'application/json'},
                        timeout=5.0
                    )
                    alerts_dispatched += 1
                except Exception as e:
                    print(f"Error dispatching webhook alert: {e}")

    # Fallback for direct HTTP invocations
    if 'category' in event and 'spent' in event and 'limit' in event:
        spent = float(event['spent'])
        limit = float(event['limit'])
        if spent > limit and limit > 0:
            msg = {
                "text": f"🚨 BUDGET ALERT: Category '{event['category']}' exceeded limit by ${spent - limit:.2f}!"
            }
            try:
                http.request(
                    'POST',
                    WEBHOOK_URL,
                    body=json.dumps(msg),
                    headers={'Content-Type': 'application/json'},
                    timeout=5.0
                )
                alerts_dispatched += 1
            except Exception as e:
                print(f"Direct alert dispatch error: {e}")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Alert processing complete',
            'alerts_dispatched': alerts_dispatched
        })
    }
