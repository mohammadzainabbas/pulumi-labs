# Pulumi Fundamentals - Tutorial

[![Deploy](https://get.pulumi.com/new/button.svg)](https://app.pulumi.com/new?template=https://github.com/mohammadzainabbas/pulumi-labs/tree/main/tutorial-pulumi-fundamentals)

## Overview

A tutorial-style typescript based Pulumi program with sample progressive web application (PWA) **the Pulumipus Boba Tea Shop**; built with `MongoDB`, `ExpressJS`, `ReactJS`, and `NodeJS` (the *MERN* stack). 

> [!NOTE]
> This tutorial is part of official Pulumi tutorials. You can follow along [here](https://www.pulumi.com/learn/pulumi-fundamentals/).

## Key Concepts

- [x] Create a Pulumi Project
- [x] Pull Docker Images
- [x] Configure and Provision Containers

## Prerequisites

* `Pulumi` _(Account and CLI)_
* `Docker`
* `TypeScript` or `JavaScript` _(NodeJS v14+)_

## Quick Start

### Setup

1. Clone the repo:

```bash
git clone https://github.com/mohammadzainabbas/pulumi-labs.git
```

or if GitHub CLI is installed:

```bash
gh repo clone mohammadzainabbas/pulumi-labs
```

2. Change directory:

```bash
cd tutorial-pulumi-fundamentals
```

3. Install dependencies:

```bash
yarn
```

or if you prefer `npm`:

```bash
npm install
```

> [!CAUTION]
> If you are using `npm`, make sure to delete `yarn.lock` file first before running installing dependencies.

4. Deploy via Pulumi:

```bash
pulumi up
```

> [!NOTE]
> Source code of **Pulumipus Boba Tea Shop** application (_backend_, _frontend_ and _database_) is available [here](https://github.com/pulumi/tutorial-pulumi-fundamentals/).

5. Access the application by open the following URL in the browser:

```bash
pulumi stack output frontendUrl
```

> [!TIP]
> By default, the application is deployed to `http://localhost:3001`. You can change the port by setting the `frontendPort` pulumi config variable as follows:

```bash
pulumi config set frontendPort <port>
```

6. Cleanup:

```bash
pulumi destroy
```

> [!WARNING]  
> This will delete all the resources (_pulled images_, _containers_, _network_) created by this Pulumi program.

### Add new item

If you want to add a new item to your app, you can do so by making a `POST` request like the following:

```bash
curl --location --request POST 'http://localhost:3000/api/products' \
--header 'Content-Type: application/json' \
--data-raw '{
    "ratings": {
        "reviews": [],
        "total": 63,
        "avg": 5
    },
    "created": 1600979464567,
    "currency": {
        "id": "USD",
        "format": "$"
    },
    "sizes": [
        "M",
        "L"
    ],
    "category": "boba",
    "teaType": 2,
    "status": 1,
    "_id": "5f6d025008a1b6f0e5636bc7",
    "images": [
        {
            "src": "classic_boba.png"
        }
    ],
    "name": "My New Milk Tea",
    "price": 5,
    "description": "none",
    "productCode": "852542-107"
}'
```

> [!IMPORTANT]  
> The above request will add a new drink item called <kbd> <br> My New Milk Tea <br> </kbd> to the app. This is just an example. You can change the request body as per your needs.

