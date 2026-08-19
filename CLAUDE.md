# landing-page-extract

One-file Gemini extractor: pass landing-page URLs, get marketing fields as JSON on stdout. Gemini fetches the page (URL-context tool). Auth: `GEMINI_API_KEY`.

## Stack
Python 3, `google-genai`. Usage: `python extract.py URL [URL ...]`

## Do not
- Expect a typed `response_schema` while the URL tool is on (API 400). Prompt-shape the JSON instead.
