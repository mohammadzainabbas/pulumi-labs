import * as pulumi from "@pulumi/pulumi";
import * as docker from "@pulumi/docker";

const projectName = pulumi.getProject();
const stack = pulumi.getStack();
pulumi.log.info(`Program: ${projectName}`);
pulumi.log.info(`Stack: ${stack}`);

/* Get configuration values */
const config = new pulumi.Config();
const frontendPort = config.requireNumber("frontendPort");
const backendPort = config.requireNumber("backendPort");
const databasePort = config.requireNumber("databasePort");

pulumi.log.info(`Frontend port: ${frontendPort}`);
pulumi.log.info(`Backend port: ${backendPort}`);
pulumi.log.info(`Database port: ${databasePort}`);

/* Pull the backend (ExpressJS & NodeJS) image from Docker Hub */
const backendImageName = "backend-image";
const backend = new docker.RemoteImage(`${projectName}-${backendImageName}`, {
    name: "pulumi/tutorial-pulumi-fundamentals-backend:latest",
});

/* Pull the frontend (ReactJS) image from Docker Hub */
const frontendImageName = "frontend-image";
const frontend = new docker.RemoteImage(`${projectName}-${frontendImageName}`, {
    name: "pulumi/tutorial-pulumi-fundamentals-frontend:latest",
});

/* Pull the database (MongoDB) image from Docker Hub */
const databaseImageName = "database-image";
const database = new docker.RemoteImage(`${projectName}-${databaseImageName}`, {
    name: "pulumi/tutorial-pulumi-fundamentals-database-local:latest",
});

/* Create a network for the containers to communicate */
const networkName = `network`;
const network = new docker.Network(`${projectName}-${networkName}`, {
    name: `${networkName}-${stack}`,
    
});
