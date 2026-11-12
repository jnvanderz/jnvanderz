# Learning Log

A running log of things I learn. New entries are appended at the bottom, separated by `---`.

## Entry template

```md
---

## YYYY-MM-DD · Short title

**Tags:** `topic1` `topic2`

**What I learned:** one or two sentences.

**How to use it:** example or command.

**Notes / watch out for:** details, common mistakes.

**Links:** references.
```

---

## 2026-11-11 · CDNs for GitHub and NPM

**Tags:** `web` `cdn` `github` `npm` `javascript`

**What I learned:** I can load files from a GitHub repo or a package from NPM straight in the browser, without downloading them.

| I need... | CDN | Site |
|---|---|---|
| Files from GitHub | jsDelivr | <https://www.jsdelivr.com/> |
| NPM packages | unpkg | <https://unpkg.com/> |

### GitHub with jsDelivr

```
https://cdn.jsdelivr.net/gh/<user>/<repo>@<version>/<path/to/file>
```

`<version>` can be a branch (`main`), a tag (`v1.0.0`) or a commit hash.

Example:

```html
<script src="https://cdn.jsdelivr.net/gh/jnvanderz/base67@main/releases/js/100/pbase67_102.js"></script>
```

- In production, pin a tag or a commit. With `@main` the file can change, and branch caching delays updates.
- With no version, the latest release is served, which is unpredictable.
- Adding `.min` (`file.min.js`) makes jsDelivr minify the file on the fly.
- Several files in one request: `https://cdn.jsdelivr.net/combine/url1,url2`.
- Only works with public repos.

### NPM with unpkg

```
https://unpkg.com/<package>@<version>/<path/to/file>
```

Example:

```html
<script src="https://unpkg.com/mqtt@5.16.1/dist/mqtt.min.js"></script>
```

- Always pin the exact version. Without it, unpkg redirects to the latest one, which can break the project.
- To browse a package's files: `https://unpkg.com/browse/<package>@<version>/`.
- For ES modules, add `?module` to the URL.
- Alternative on jsDelivr: `https://cdn.jsdelivr.net/npm/<package>@<version>/<path>`.

### Quick summary

```text
GitHub → https://cdn.jsdelivr.net/gh/USER/REPO@VERSION/PATH
NPM    → https://unpkg.com/PACKAGE@VERSION/PATH
NPM    → https://cdn.jsdelivr.net/npm/PACKAGE@VERSION/PATH   (alternative)
```
