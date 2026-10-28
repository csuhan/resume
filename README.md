# csuhan.com

Source of [csuhan.com](https://csuhan.com), served by GitHub Pages.

## Editing

Edit these, never `index.html` directly (it is generated):

| What | File |
| --- | --- |
| Page content | `src/index.html` |
| Styles | `css/*.css` |
| Scripts | `js/main.js` |
| Images, PDFs | `img/`, `attaches/` |
| 3D version | `3D/` (built from a separate project) |

Then publish:

```bash
scripts/publish.sh "what changed"
```

## How loading works

GitHub Pages is slow from mainland China, so the published `index.html` keeps
the number of requests to csuhan.com low:

- **CSS** is inlined into `index.html` at build time. It arrives with the page
  in one request and can never be stale.
- **JS** loads from jsDelivr at a URL pinned to the commit that last changed
  it (`cdn.jsdelivr.net/gh/csuhan/resume@<commit>/js/main.min.js`), with
  csuhan.com as fallback. A changed file always gets a new URL, so neither the
  CDN nor the browser can serve an old copy.
- **Images** still come from csuhan.com.

`scripts/publish.sh` commits the JS first, then builds `index.html` against
that commit. That ordering is what guarantees visitors get the latest code.
