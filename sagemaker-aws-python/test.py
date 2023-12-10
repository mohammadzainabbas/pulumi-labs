import json, boto3, argparse

def main(endpoint_name, text):
    client = boto3.client('sagemaker-runtime', region_name='us-east-1')
    payload = json.dumps({"inputs": text})
    response = client.invoke_endpoint(EndpointName=endpoint_name, ContentType="application/json", Body=payload)
    print("Response:", json.loads(response['Body'].read().decode()))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("endpoint_name")
    parser.add_argument("--text", default="In 3 words, name the biggest mountain on earth?")
    main(parser.parse_args().endpoint_name, parser.parse_args().text)