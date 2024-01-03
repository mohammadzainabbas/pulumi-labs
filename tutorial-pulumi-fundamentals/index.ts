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

const nodeEnvironment = config.require("nodeEnvironment")
const databaseName = config.require("databaseName")
const databaseHost = config.require("databaseHost")
const protocol = config.require("protocol")
// const dbHost = pulumi.interpolate`${databaseHost}:${databasePort}`

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

/* Create the backend container */
const backendContainerName = `backend-container`;
const backendContainer = new docker.Container(`${projectName}-${backendContainerName}`, {
    name: `${backendContainerName}-${stack}`,
    image: backend.repoDigest,
    ports: [{
        internal: backendPort,
        external: backendPort,
    }],
    envs: [
        `PORT=${backendPort}`,
        `DATABASE_NAME=${databaseName}`,
        `DATABASE_HOST=${pulumi.interpolate`${databaseHost}:${databasePort}`}`,
        `NODE_ENV=${nodeEnvironment}`,
    ],
    networksAdvanced: [{ name: network.name, aliases: [backendContainerName] }],
}, { dependsOn: [ databaseContainer ] });

/* Create the frontend container */
const frontendContainerName = `frontend-container`;
const frontendContainer = new docker.Container(`${projectName}-${frontendContainerName}`, {
    name: `${frontendContainerName}-${stack}`,
    image: frontend.repoDigest,
    ports: [{
        internal: frontendPort,
        external: frontendPort,
    }],
    envs: [
        `PORT=${frontendPort}`,
        `HTTP_PROXY=${backendContainerName}-${stack}:${backendPort}`,
        `PROXY_PROTOCOL=${frontendPort}`,
    ],
    networksAdvanced: [{ name: network.name, aliases: [frontendContainerName, `frontend`] }],
});

/* Create the database container */
const databaseContainerName = `database-container`;
const databaseContainer = new docker.Container(`${projectName}-${databaseContainerName}`, {
    name: `${databaseContainerName}-${stack}`,
    image: database.repoDigest,
    ports: [{
        internal: databasePort,
        external: databasePort,
    }],
    envs: [
        `MONGO_INITDB_DATABASE=${databaseName}`,
    ],
    networksAdvanced: [{ name: network.name, aliases: [databaseContainerName, `mongodb`] }],
});