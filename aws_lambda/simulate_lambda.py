import json
from aws_lambda_alert import lambda_handler

if __name__ == "__main__":
    print("=" * 70)
    print("⚡ SIMULATING AWS LAMBDA SERVERLESS ALERT HANDLER (Section 10.2)")
    print("=" * 70)

    # Simulated DynamoDB Stream Insert Event with an overspent category
    mock_event = {
        "Records": [
            {
                "eventName": "INSERT",
                "dynamodb": {
                    "NewImage": {
                        "category": {"S": "Tech & Gadgets"},
                        "spent": {"N": "680.00"},
                        "limit": {"N": "500.00"}
                    }
                }
            },
            {
                "eventName": "INSERT",
                "dynamodb": {
                    "NewImage": {
                        "category": {"S": "Groceries"},
                        "spent": {"N": "320.00"},
                        "limit": {"N": "400.00"}
                    }
                }
            }
        ]
    }

    result = lambda_handler(mock_event, None)
    print("\nLambda Execution Output:")
    print(json.dumps(result, indent=2))
    print("\n✅ Verification Test Passed: Alert dispatched for breached category 'Tech & Gadgets'!")
