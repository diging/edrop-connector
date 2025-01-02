# eDROP Connector

## Running the App
To run this Django app, the easiest is to run it via Docker. 

- Make sure Docker is installed.
- Make sure there is a folder `data/db` in this folder (if it's the first time you run this project, you will need to create `db` inside `data`).
- Then from this directory, run `docker compose up`
- The app will be available at http://localhost:8000/.

## Developing the App

When developing this app, please keep the following in mind:

- If you add new packages, add them to `requirements.txt` and specify what version should be used.
- We follow the [GitFlow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow) Workflow, which basically means, a branch should be created for each issue off of the `develop` branch. When the code is done for that issue, a pull request to develop should be made. Once we are ready for a new version, `develop` will be merged into `main` and a new release will be created.
- Commits should be previxed with `[issue-number]`, e.g. `[GH-1] added code to accept incoming connections`.
- Branches should be named after the issue they are for prefixed with `feature`, `bug`, or `chore`, e.g. `feature/GH-1`.
- If you need to run migrations or run other Django commands, you will need to log in to the Docker container running the Django app and run the commands from there. The following steps will likely work for this:
   ```
   > docker ps
   CONTAINER ID   IMAGE  COMMAND  CREATED  STATUS  PORTS  NAMES
   575f0aa89a6e   edrop-connector-web "./startup.sh tail -…"  About an hour ago  Up 3 seconds  0.0.0.0:8000->8000/tcp   edrop-connector-web-1
   1a7478580d3e   postgres "docker-entrypoint.s…"  About an hour ago  Up 3 seconds 0.0.0.0:5432->5432/tcp   edrop-connector-db-1
   ```
   Then pick the container id or name and run:
   ```
   docker exec -it edrop-connector-web-1 bash
   ```
   If your container is not called `edrop-connector-web-1`, specify the correct name instead.

   Now you're inside the container and you can run any Django coammend you need.


## Copyright 
By committing code to this repository, you agree to transfer or license your copyright to the project under its the terms that will be selected at a later point.