build flags="":
    docker build -t bot . {{flags}}

run: build
    docker run -it --rm --env-file .env bot

bash: build
    docker run -it --rm --env-file .env bot bash

lockdeps:
    pip-compile requirements.in -o requirements.txt

deploy:
    git push dokku master:master

