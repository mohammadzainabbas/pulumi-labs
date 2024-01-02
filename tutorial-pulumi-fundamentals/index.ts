import * as pulumi from "@pulumi/pulumi";
import * as docker from "@pulumi/docker";

const projectName = pulumi.getProject();
const stack = pulumi.getStack();

pulumi.log.info(`Running ${projectName} the ${stack} stack!`);

/* Pull the backend image from Docker Hub */
const backendImageName = "backend-image";
const backend = new docker.RemoteImage(`${projectName}-${backendImageName}`, {
    name: "pulumi/tutorial-pulumi-fundamentals-backend:latest",
});

/* Pull the frontend image from Docker Hub */
const frontendImageName = "frontend-image";
const frontend = new docker.RemoteImage(`${projectName}-${frontendImageName}`, {
    name: "pulumi/tutorial-pulumi-fundamentals-frontend:latest",
});


