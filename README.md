ArtemPodcast.com
================

This repo contains files and scripts for [artempodcast.com](https://artempodcast.com)

Deployment
----------
- GitHub Pages deploy runs from `.github/workflows/hugo.yml` on pushes to `main`.
- The site is built with Hugo and published with the GitHub Pages Actions flow.
- `static/CNAME` is set to `artempodcast.com` for custom domain publishing.
- In GitHub: Settings -> Pages -> Build and deployment -> Source should be **GitHub Actions**.

Recording
---------
use ./record script
