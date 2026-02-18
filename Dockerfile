FROM ruby:3.3-slim

RUN apt-get update && \
    apt-get install -y build-essential git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /srv/jekyll

EXPOSE 4000 35729

CMD ["bash", "-c", "rm -f Gemfile.lock && bundle install && bundle exec jekyll serve --host 0.0.0.0 --livereload"]
