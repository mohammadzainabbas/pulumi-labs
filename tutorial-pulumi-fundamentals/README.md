# Pulumi Fundamentals - Tutorial

[![Deploy](https://get.pulumi.com/new/button.svg)](https://app.pulumi.com/new?template=https://github.com/mohammadzainabbas/pulumi-labs/tree/main/tutorial-pulumi-fundamentals)

## Overview

A tutorial-style typescript based Pulumi program with sample progressive web application (PWA) **the Pulumipus Boba Tea Shop**; built with `MongoDB`, `ExpressJS`, `ReactJS`, and `NodeJS` (the *MERN* stack).

> [!NOTE]
> This tutorial is part of official Pulumi tutorials. You can follow along [here](https://www.pulumi.com/learn/pulumi-fundamentals/).


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

3. Create a new Pulumi stack, which is an isolated deployment target for this example:

```bash
pulumi stack init
```
