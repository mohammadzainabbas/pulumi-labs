# Amazon SageMaker + Hugging Face LLM Deployment

[![Deploy](https://get.pulumi.com/new/button.svg)](https://app.pulumi.com/new?template=https://github.com/pulumi/examples/tree/master/aws-py-apigatewayv2-eventbridge)

## Overview

A Pulumi IaC program written in Python to deploy a Hugging Face Language Model (LLM) on Amazon SageMaker.

## Included:

- IAM roles
- SageMaker model endpoint
- CloudWatch alarms

## Prerequisites

* `Python 3.9+`
* `Pulumi`
* `AWS CLI v2` _(with valid credentials configured)_

## Quick Start

### Setup

1. Create a new directory & initialize a new project:

```bash
mkdir newProject && cd newProject
pulumi new sagemaker-aws-python
```

2. Deploy the stack:

```bash
pulumi up
```

> Note that Pulumi will provide the SageMaker endpoint name as an output.

### Test the SageMaker Endpoint

Use this rudimentary Python snippet to test the deployed SageMaker endpoint.

1. Activate the Python `venv` locally

```bash
# On Linux & MacOS
source venv/bin/activate
```

2. Save the following as test.py:

> NOTE: change your `region_name` if using a different region than `us-east-1`

```python
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
```

2. Run the test:

> Notice: using the `pulumi stack output` command to return EndpointName from Pulumi state

```bash
python3 test.py $(pulumi stack output EndpointName)
```

or 

```bash
python3 test.py $(pulumi stack output EndpointName) --text "What's the most beautiful thing in life ? Provide a short essay on this."
```

### Cleanup

To destroy the Pulumi stack and all of its resources:

```bash
pulumi destroy
```
