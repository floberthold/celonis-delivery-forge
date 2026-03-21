# Setup

## 1. Github Repo

The service template includes git initialization without pushing the repo.
Therefore, create a new repository under the [celonis org](https://github.com/celonis):
1. Go to `Settings` -> `General`
    - check `Automatically delete head branches`
2. Got to `Settings` -> `Branches`
    - Add rule
        - branch name pattern: `main`
        - check `Require a pull request before merging`
3. Push your local repo

## 2. ECR (Docker Registry)

In order to deploy your service you need to first register you Docker image repository.
Therefore, follow [these instructions](https://github.com/celonis/terraform/blob/master/ecr/README.md).

> ⚠️ the repository name should be the same as the deploy workflow image-id
> ```
> - name: Update cfg-ibc Repository
>   id: cfg-ibc-updater
>   uses: ./.github/actions/cfg-ibc-updater
>   with:
>     config-path: '["pig-compability-wrapper/overlays/realms/${{ inputs.env }}"]'
>     image-id: 'cloud/pig-compability-wrapper'
>     token: ${{ secrets.CELOBOT_GITHUB_TOKEN }}
> ```

## 3. Config IBC

Once your Docker repository is set up [cfg-ibc](https://github.com/celonis/cfg-ibc).
For reference see https://github.com/celonis/cfg-ibc/pull/11829

## 4. Persistence (Optional)
In order to enable persistence using Postgres databases follow the following steps:
### Create a database
Create the database [as shown here](https://celonis-confluence.atlassian.net/wiki/spaces/DKB/pages/17668688/Create+databases+with+Argo+CD+and+kustomize) for each realm.
This works the same for all staging and production clusters (openshift/azure/aws).

### Create the database migration directory in your service
Initialize the database migration directory for alembic by running the following which will create the folder `./migrations`:
```
poetry run python_core_alembic init
```
Once you have defined your initial database models (this can be zero models) in your service run the following to create the initial migration:
```
poetry run alembic revision -m "Initial table setup"
```
Make sure the migration folder and alembic configuration are added to your container files.
Locally, you can test the migrations by running `poetry run python_core_alembic upgrade`.
### Add database configuration to your cfg-ibc configuration
For the following step the database needs to be created and the migration directory needs to be added to your service.
- Set the environment variables in cfg-ibc to connect to your database [as shown here](https://github.com/celonis/cfg-ibc/blob/master/pc-sandbox/overlays/realms/develop/env.patch.yaml).
The details of the different database connections per realm can be adapted from [other services](https://github.com/celonis/cfg-ibc/blob/master/machine-learning/overlays/realms/eu-3/kustomization.yaml#L11).
The `@xy`-suffix in some realms for the username (e.g. eu-3) are also required for your pc-service.
- Migrations are executed using an init container before the python-core app is started.
  Take a look at our [sandbox service](https://github.com/celonis/cfg-ibc/tree/master/pc-sandbox) for an example how to configure the init container.
- Lastly, it requires the following [presets](https://github.com/celonis/cfg-ibc/blob/master/pc-sandbox/base/kustomization.yaml). For these the [init container](https://github.com/celonis/cfg-ibc/blob/master/pc-sandbox/base/deployment.yaml) needs to be added to the deployment!

### Enable Tenant Erasion
Enable tenant erasion by registering your service with [cloud-backend](https://github.com/celonis/cloud-backend/blob/develop/cloud-backend/src/main/resources/application-kubernetes.yml).
This will configure cloud-backend to call your service when a tenant is deleted.
This should be enabled before __any__ customer data can be stored in the database.
If tenant erasion is only enabled on a subset of all realms cloud-backend can be configured individually via an environment variable in cfg-ibc.
See [this thread](https://github.com/celonis/cloud-backend/commit/9b8c0ee9061735cbfb2dc16b09c8444121fd906d) for details.

## 5. RabbitMQ (Optional)
In order to enable RabbitMQ follow the following steps:
1. Create user following official [documentation](https://www.celonis.dev/catalog/default/component/rabbitmq-as-a-service-documentation/docs/onboarding/create-user/) in the base directory ([example](https://github.com/celonis/cfg-ibc/blob/master/rabbitmq-cluster-topology-config/overlays/components/pc-sandbox/users.yaml)).
2. Create Queues (preferably of type quorum), Exchanges, and Bindings on cfg-ibc following the official [documentation](https://www.celonis.dev/catalog/default/component/rabbitmq-as-a-service-documentation/docs/onboarding/queue-management/) in the base directory ([example](https://github.com/celonis/cfg-ibc/tree/master/rabbitmq-cluster-topology-config/overlays/components/pc-sandbox))
3. Set environment variables in your service configuration on cfg-ibc ([example](https://github.com/celonis/cfg-ibc/blob/549e6b69ceb6590e37ef09fef8a39ca6400a85df/pc-sandbox/overlays/realms/develop/env.patch.yaml#L35C29-L35C29))
4. Add configuration preset to your service configuration on cfg-ibc ([example](https://github.com/celonis/cfg-ibc/blob/13c69ec732097f7df04219abebf0d5edb464028c/pc-sandbox/base/kustomization.yaml#L13))

## 6. Vector Database (Optional)

In order to enable python core vector using Zilliz vector databases follow the following steps:

### Create a vector database

Contact the ML Infrastructure team to provision a Zilliz project with clusters per region.

### Add vector database configuration to your cfg-ibc configuration
For the following step the vector database needs to be created.
- Set the environment variables in cfg-ibc to connect to your vector database [as shown here](https://github.com/celonis/cfg-ibc/blob/master/pc-sandbox/overlays/realms/develop/env.patch.yaml).
  The details of the different database connections per realm can be requested from the ML Infra team.
- Migrations are executed using an init container before the python-core app is started.
  Take a look at our [sandbox service](https://github.com/celonis/cfg-ibc/tree/master/pc-sandbox) for an example how to configure the init container.
- Lastly, it requires the following [presets](https://github.com/celonis/cfg-ibc/blob/master/pc-sandbox/base/kustomization.yaml). For these the [init container](https://github.com/celonis/cfg-ibc/blob/master/pc-sandbox/base/deployment.yaml) needs to be added to the deployment!

### Enable Tenant Erasion
Enable tenant erasion by registering your service with [cloud-backend](https://github.com/celonis/cloud-backend/blob/develop/cloud-backend/src/main/resources/application-kubernetes.yml).
This will configure cloud-backend to call your service when a tenant is deleted.
This should be enabled before __any__ customer data can be stored in the database.
If tenant erasion is only enabled on a subset of all realms cloud-backend can be configured individually via an environment variable in cfg-ibc.
See [this thread](https://github.com/celonis/cloud-backend/commit/9b8c0ee9061735cbfb2dc16b09c8444121fd906d) for details.

## 7. Gateway
If needed, add your service to the cloud-gateway configuration as described [here](https://github.com/celonis/cfg-ibc/blob/907d398291a53d201beccbf33deb44f0689fb8cb/gateway/overlays/envs/prod/config.default.yaml).

## 8. Sonarcloud
The `build-branch` workflow includes sonarcloud analysis. Follow this steps to in order connect sonar cloud with your Github project:

1. Go on: https://sonarcloud.io/sessions/new?return_to=%2Forganizations%2Fcelonis%2Fprojects login with you GitHub credentials (log in with your GitHub account in case you don't see the celonis projects)
2. Find `+` button in the upper right corner and click `Analyze new project`
3. Find your project on the list of projects of Celonis organization
4. Click on it and click `Setup project`
5. Then go to `Administration` in the sidebar, `Analysis Method`, `GitHub Actions`, `Follow the Tutorial`
6. Go to your GitHub repository -> `Settings` -> `Secrets` -> `Actions`
   - add the Sonar Cloud `secret key` to your github secrets with name `SONAR_TOKEN `

## 9. Veracode

The `veracode` workflow runs the veracode security scan on a daily schedule or via workflow dispatch.
Follow the steps from

1. visit [confluence](https://confluence.celonis.com/display/DKB/How+to+integrate+a+service+on+Github+with+Veracode)
and follow the steps in order create new veracode token for your Github project.
2. Go to your GitHub repository -> `Settings` -> `Secrets` -> `Actions`
   - add the veracode token to your github secrets with name `SRCCLR_API_TOKEN`

## 10. Backstage
The service template contains a `catalog-info.yaml` file that registers your service on [Backstage](https://www.celonis.dev/catalog) (including the service API specification located in the `openapi.json` file).
After, creating the Github Repository, you can view your service in the backstage [catalog](https://www.celonis.dev/catalog).
