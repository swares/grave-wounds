# Pictures for the books

Each picture the books use is listed in `data/pictures/*.yaml` with its caption, credit, licence and the
source page where its licence was checked. Save the image file here under the name its entry gives:

- `images/books/medieval/` for *The Medieval Wars* (`data/pictures/<battlefield>.yaml`,
  `data/pictures/medieval-intro.yaml`)
- `images/books/rules/` for the Rules (`data/pictures/rules.yaml`)

Until a file is here, the book shows a captioned slot with the credit and source in its place. The build
copies this folder to `dist/images/`. Keep files reasonably small (about 1,600 px on the long side, JPEG).
