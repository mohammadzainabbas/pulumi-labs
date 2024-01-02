import * as pulumi from "@pulumi/pulumi";
import * as docker from "@pulumi/docker";

const stack = pulumi.getStack();

pulumi.log.info(`Hello, world! You are running the ${stack} stack!`);