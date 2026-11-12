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

---

## 2026-11-11 · httpbin as a real server for testing

**Tags:** `http` `testing` `base64` `httpbin`

**What I learned:** httpbin.org is a free service for HTTP testing. It has a route that decodes base64 straight from the URL, so it works as a real server for that kind of test.

**How to use it:**

```
https://httpbin.org/base64/SGVsbG8gV29ybGQh
```

It returns the decoded content (here, `Hello World!`).

**Notes / watch out for:**

- Not verified: I could not open it to confirm the response.
- As far as I know, it returns text/HTML rather than generic binary, so it is useful for text tests more than for real files.

**Links:** <https://httpbin.org/>

---

## 2026-11-11 · httpbingo: base64 route with a content type

**Tags:** `http` `testing` `base64` `httpbingo` `go`

**What I learned:** httpbingo.org is a Go reimplementation of httpbin. Its `/base64/:value` route accepts an optional `content-type` parameter, which tells the browser how to treat the decoded data (for example, as an image).

**How to use it:** this URL is a 1×1 pixel PNG:

```
https://httpbingo.org/base64/iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk-M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==?content-type=image/png
```

**Notes / watch out for:**

- Not tested, and it may not work as is. Controlling the `Content-Type` from the URL appears in a security advisory against go-httpbin (it allowed XSS), so current versions may limit which types they accept.
- URL-safe base64: `+` and `/` have their own meaning in a URL, so they must be replaced with `-` and `_` (in the example above, one `+` was already replaced). This is the problem my Base67 avoids by design.
- Size: servers usually cut URLs off after a few kilobytes. Fine for an icon, not for a photo.
- No guarantees: these are third-party test services that can go down, change or limit usage. Don't rely on them for anything that must keep working.

**Links:**

- <https://hbin.apps-isd.sd.gov.bc.ca/>
- <https://advisories.gitlab.com/pkg/golang/github.com/mccutchen/go-httpbin/v2/>
