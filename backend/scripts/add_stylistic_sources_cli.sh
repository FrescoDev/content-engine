#!/bin/bash
# Quick script to add stylistic sources via CLI

echo "Adding stylistic sources..."

# Add Reddit sources
poetry run python -m src.cli.main add-style-source \
  --type reddit \
  --url "https://www.reddit.com/r/hiphopheads/" \
  --name "r/hiphopheads" \
  --description "Hip-hop culture subreddit" \
  --tags "hip-hop,culture,music,rap"

poetry run python -m src.cli.main add-style-source \
  --type reddit \
  --url "https://www.reddit.com/r/theJoeBuddenPodcast/" \
  --name "r/theJoeBuddenPodcast" \
  --description "Joe Budden Podcast discussion subreddit" \
  --tags "podcast,hip-hop,culture,discussion"

# Add podcast sources
poetry run python -m src.cli.main add-style-source \
  --type podcast \
  --url "https://podcasts.musixmatch.com/podcast/the-joe-budden-podcast-01gv03qx00bhdgccn8k448zhy3" \
  --name "The Joe Budden Podcast (Musixmatch)" \
  --description "Joe Budden Podcast transcripts" \
  --tags "podcast,hip-hop,transcript"

poetry run python -m src.cli.main add-style-source \
  --type podcast \
  --url "https://podcasts.happyscribe.com/the-joe-rogan-experience" \
  --name "The Joe Rogan Experience (HappyScribe)" \
  --description "Joe Rogan Experience podcast transcripts" \
  --tags "podcast,transcript,conversation"

echo "Done! Sources added."





