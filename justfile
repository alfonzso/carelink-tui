git_branch := `git rev-parse --abbrev-ref HEAD`
git_count := shell('git rev-list --count ' + git_branch)

default:
    just --list

build:
    docker build -t alfonzso/carelink-server:{{ git_branch }}-{{ git_count }} .

push: build
    docker push alfonzso/carelink-server:{{ git_branch }}-{{ git_count }}
