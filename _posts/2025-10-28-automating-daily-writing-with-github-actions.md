---
layout: post
title: Automating Daily Writing with GitHub Actions
subtitle: From idea capture to published post
date: '2025-10-28 20:52:54'
tags:
- automation
- GitHub
- Python
categories:
- Automation
canonical_url: https://example.github.io/2025/10/28/automating-daily-writing-with-github-actions/
lang: en
timezone: Asia/Seoul
description: From idea capture to published post
keywords:
- GitHub Actions blog automation
- automation
- GitHub
- Python
---

Automating daily writing isn’t about forcing words out; it’s about removing friction. With GitHub Actions blog automation, you can capture ideas fast, schedule posts with file naming, and ship to GitHub Pages on autopilot—without leaving your repo.

# Automating Daily Writing with GitHub Actions
From idea capture to published post

## What we’ll automate
- Capture ideas as GitHub Issues, turn them into Markdown drafts with one label.
- Promote drafts to posts on a daily schedule based on the filename date.
- Build and deploy the site to GitHub Pages on every push to main.

This setup is static-site-generator agnostic and keeps everything in Git.

## Repo layout and naming convention
We’ll use a simple content structure and a predictable filename format to drive scheduling.

- content/drafts: drafts named YYYY-MM-DD-title.md
- content/posts: published posts

Example draft:

```md
content/drafts/2025-11-01-automating-daily-writing.md
---
title: "Automating Daily Writing"
date: 2025-11-01
draft: true
---

Opening paragraph here...
```

This lets automation compare the date in the filename against “today” and decide when to publish.

## Idea capture: label an issue to create a draft
When you add the label blog-draft to an issue, this workflow scaffolds a Markdown file in content/drafts using the issue’s title and body.

Create .github/workflows/issue-to-draft.yml:

```yaml
name: Issue to Draft
on:
  issues:
    types: [labeled]

permissions:
  contents: write

jobs:
  seed-draft:
    if: github.event.label.name == 'blog-draft'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Create draft from issue
        env:
          GIT_AUTHOR_NAME: github-actions
          GIT_AUTHOR_EMAIL: actions@github.com
          GIT_COMMITTER_NAME: github-actions
          GIT_COMMITTER_EMAIL: actions@github.com
        run: |
          # Read fields directly from the event payload
          title=$(jq -r '.issue.title' "$GITHUB_EVENT_PATH")
          body=$(jq -r '.issue.body // ""' "$GITHUB_EVENT_PATH")
          num=$(jq -r '.issue.number' "$GITHUB_EVENT_PATH")

          # Slugify the title
          slug=$(echo "$title" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g' | sed -E 's/^-+|-+$//g')

          # Use today as the draft date; adjust if you want a future date
          date=$(date -u +%F)
          file="content/drafts/${date}-${slug}.md"

          mkdir -p content/drafts
          printf -- '---\ntitle: "%s"\ndate: %s\ndraft: true\n---\n\n%s\n' "$title" "$date" "$body" > "$file"

          git add "$file"
          git commit -m "chore(blog): draft from issue #$num"
          git push
```

Why this helps: you can brain-dump into Issues on mobile or desktop and turn them into drafts with a single label—no local tooling needed.

## Scheduled publishing with GitHub Actions blog automation
This daily workflow promotes any draft whose filename date is today or earlier. It copies the file to content/posts (flipping draft: false) and commits the change.

Create .github/workflows/publish-scheduled.yml:

```yaml
name: Publish Scheduled Posts
on:
  schedule:
    - cron: "0 6 * * *"   # 06:00 UTC daily
  workflow_dispatch:

permissions:
  contents: write

jobs:
  publish-ready:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Move ready drafts to posts
        run: |
          set -euo pipefail
          today=$(date -u +%F)
          shopt -s nullglob
          mkdir -p content/posts
          moved=0

          for f in content/drafts/*.md; do
            base=$(basename "$f")
            datepart=${base%%-*}
            if [[ "$datepart" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ && "$datepart" <= "$today" ]]; then
              # Flip draft flag if present
              sed 's/^draft: true/draft: false/' "$f" > "content/posts/$base"
              git rm -f "$f" >/dev/null 2>&1 || true
              git add "content/posts/$base"
              moved=$((moved+1))
            fi
          done

          if [ "$moved" -gt 0 ]; then
            git -c user.name=github-actions -c user.email=actions@github.com commit -m "publish: $moved post(s) on $today"
            git push
          else
            echo "No drafts to publish today."
          fi
```

Tip: Want stricter scheduling? Put the intended publish date in the filename even for drafts created from issues (you can manually edit the filename in a quick PR).

## Build and deploy to GitHub Pages
Use the official Pages actions to build and deploy on push to main. Set your repository’s Pages “Build and deployment” source to GitHub Actions in Settings.

Create .github/workflows/deploy-pages.yml:

```yaml
name: Deploy to GitHub Pages
on:
  push:
    branches: [main]

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/configure-pages@v5
      - name: Build site
        run: |
          # Replace with your SSG build; output to _site
          # Examples:
          #   Jekyll: bundle install && bundle exec jekyll build -d _site
          #   Hugo:   sudo apt-get update && sudo apt-get install -y hugo && hugo -D -d _site
          # For demo purposes, publish raw posts:
          mkdir -p _site
          cp -r content/posts/* _site/ || true
      - uses: actions/upload-pages-artifact@v3
        with:
          path: _site

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

This decouples content operations (drafts and scheduling) from deployment. Your own build step can be as simple or advanced as you like.

## Tips and gotchas
- Permissions: These workflows need contents: write for commits made by the bot, and pages/id-token for deployment.
- Branch protection: If main is protected, target a staging branch in the automation and open PRs instead of pushing directly.
- Time zones: The cron and date compare use UTC. Adjust cron or add an offset if you want local-time publishing.
- Idempotency: The publish job skips if no drafts match; it’s safe to run manually via workflow_dispatch.
- Previews: Add a PR workflow to build and post a preview URL as a comment if you want review before publish.

## Takeaways
- GitHub Actions blog automation turns Issues into drafts and dates into schedules—no extra services required.
- Use filename dates to drive “publish on or before” logic with a simple daily cron.
- Keep deployment clean with official Pages actions and your SSG of choice.
- Start small: label-to-draft, daily publish, push to Pages. Iterate from there.