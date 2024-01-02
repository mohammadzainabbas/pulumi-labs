import * as pulumi from "@pulumi/pulumi";
import * as docker from "@pulumi/docker";

const stack = pulumi.getStack();

pulumi.log.info(`Hello, world! You are running the ${stack} stack!`);

/* Pull the backend image from Docker Hub */
const backendImageName = "backend";
const backend = new docker.RemoteImage(`${backendImageName}Image`, {
    name: "pulumi/tutorial-pulumi-fundamentals-backend:latest",
});