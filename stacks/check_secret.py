import boto3

client = boto3.client('secretsmanager', region_name='eu-west-2')

try:
    response = client.get_secret_value(SecretId='github-token-adel')
    print("✅ Secret value retrieved successfully:\n")
    print(response['SecretString'])
except Exception as e:
    print("❌ Error retrieving the secret:")
    print(e)
