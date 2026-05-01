# tethysext-atcore documentation site

This directory contains the [Docusaurus 3.x](https://docusaurus.io/) site that
publishes the `tethysext-atcore` documentation to GitHub Pages.

## Local development

```bash
cd website
npm install
npm start
```

`npm start` launches a local dev server with hot reload at
http://localhost:3000/tethysext-atcore/.

## Production build

```bash
npm run build
npm run serve   # optional: preview the static build
```

The static site is emitted to `website/build/`.

## Deployment

Deployment is automated. On every push to `master` that touches
`website/**` or `tethysext/**`, the `.github/workflows/docs.yml` workflow
builds the site and publishes it to GitHub Pages via
`actions/deploy-pages`.

## Authoring

- **Narrative content** lives directly under `website/docs/`. The
  `docs-narrative-writer` agent is responsible for these pages.
- **API reference** lives under `website/docs/api/` and is generated as
  MDX by the `docs-api-writer` agent. Do not hand-edit that directory.
