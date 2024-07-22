# How to setup the docker container

After this you can build the two container (backend and db) by executing 'docker-compose up --build'
First you need to create a folder with the 'Dockerfile' and the 'docker-compose.yml' and the code for your application app.py as well as the requirmenets.txt .

Run the following command in terminal so that a new network is created so that both the backend and db container can communicate to each other.

'docker network create myNetwork'


