#!/usr/bin/env python3
"""Extract structured marketing fields from landing page URLs via Gemini.

Gemini fetches each page itself (the URL-context tool), so no scraping here.
One API call per URL; results print as a JSON array to stdout.

Design note: Gemini rejects a strict `response_schema` whenever a tool is
enabled -- the API returns 400 "Tool use with a response mime type:
'application/json' is unsupported". So we can't get typed output *and* let the
model fetch the page in one call. The workaround (verified 2026-07-21) is to
enable the URL-context tool, instruct the JSON shape in the prompt, and parse
the reply -- stripping any ```json markdown fence the model wraps it in.

Reads GEMINI_API_KEY from the environment (google-genai picks it up).

Usage:
    python extract.py URL [URL ...]
    python extract.py --model gemini-2.5-pro URL ...
"""

from __future__ import annotations

import argparse
import json
import sys

from google import genai
from google.genai import types

PROMPT = """Read the landing page at {url} and extract its marketing content.
Return ONLY a JSON object with exactly these keys:
- headline: the main hero headline (string)
- subheadline: the supporting subheadline, or null (string or null)
- primary_offer: the core offer, price, or value proposition (string)
- primary_cta: the main call-to-action button text (string)
- secondary_cta: a secondary CTA if present, else null (string or null)
- target_audience: who the page is aimed at, inferred (string)
- key_benefits: 3-5 key benefits as short strings (array of strings)
Use null for anything genuinely absent. Do not invent. Output JSON only, no prose."""


def _parse_json(text: str) -> dict:
    """Load JSON from the model reply, tolerating a ```json ... ``` fence."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t[3:]
        t = t.rsplit("```", 1)[0]
    return json.loads(t.strip())


def extract(client: genai.Client, model: str, url: str) -> dict:
    resp = client.models.generate_content(
        model=model,
        contents=PROMPT.format(url=url),
        config=types.GenerateContentConfig(
            tools=[types.Tool(url_context=types.UrlContext())],
        ),
    )
    data = _parse_json(resp.text)
    data["url"] = url
    return data


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("urls", nargs="+", help="landing page URLs")
    ap.add_argument(
        "--model",
        default="gemini-2.5-flash",
        help="Gemini model (default: gemini-2.5-flash)",
    )
    args = ap.parse_args()

    try:
        client = genai.Client()
    except Exception as e:  # missing/invalid key surfaces here
        sys.exit(f"error: could not init Gemini client (is GEMINI_API_KEY set?): {e}")

    out = []
    for url in args.urls:
        try:
            out.append(extract(client, args.model, url))
        except Exception as e:
            out.append({"url": url, "error": f"{type(e).__name__}: {e}"})
            print(f"warn: {url}: {e}", file=sys.stderr)

    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
