build flags="":
    docker build -t bot . {{flags}}

run: build
    docker run -it --rm --env-file .env bot

bash: build
    docker run -it --rm --env-file .env bot bash

lockdeps:
    pip-compile requirements.in -o requirements.txt --resolver=backtracking

deploy:
    git push dokku master:master

ssh:
    ssh root@137.184.158.113

linkremote:
    git remote add dokku dokku@137.184.158.113:reminders

unlinkremote:
    git remote remove dokku

setsecrets:
    # on dokku host
    dokku config:set reminders DATABASE_URL=1 BOT_KEY=2
