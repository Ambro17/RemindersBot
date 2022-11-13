build flags="":
    docker build -t bot . {{flags}}

run: build
    docker run -it --rm --env-file .env bot

lockdeps:
    pip-tools