build flags="":
    docker build -t bot . {{flags}}

run: build
    docker run -it --rm --env-file .env bot

bash: build
    docker run -it --rm --env-file .env bot bash

lockdeps:
    pip-compile requirements.in -o requirements.txt --resolver=backtracking

deploy:
    fly deploy

setsecrets:
    echo "Remember to export the variables before running this!"
    fly secrets set DATABASE_URL=$DATABASE_URL BOT_KEY=$BOT_KEY