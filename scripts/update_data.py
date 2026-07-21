#!/usr/bin/env python3
"""
Daily data updater for abdulhaseeb2k.github.io
Runs via GitHub Actions (cron) and writes data.json which the site reads.
Stdlib only — no pip installs needed.
"""
import json
import os
import ssl
import urllib.request
from datetime import datetime, timezone, timedelta

CTX = ssl.create_default_context()
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# ------------------------------------------------------------------
# ⭐ FAMOUS REPOS — edit this list any time to add/remove repos.
# Live stats (stars, description, last push) are fetched automatically.
# ------------------------------------------------------------------
FAMOUS_REPOS = [
    "DeusData/codebase-memory-mcp",
    "tirth8205/code-review-graph",
    "diegosouzapw/OmniRoute",
    "WorldFlowAI/everything-claude-code",
    "thedotmack/claude-mem",
    "anthropics/claude-code",
    "open-webui/open-webui",
    "ollama/ollama",
    "BerriAI/litellm",
    "langchain-ai/langchain",
    "ggml-org/llama.cpp",
    "microsoft/generative-ai-for-beginners",
    "punkpeye/awesome-mcp-servers",
    "hesreallyhim/awesome-claude-code",
    # "REPLACE/grify",  # <- add the exact "grify" repo name here once found
]

# ------------------------------------------------------------------
# 💡 CONCEPT OF THE DAY — rotates daily (AI / Data Science / Dev / Security)
# ------------------------------------------------------------------
CONCEPTS = [
    {"cat": "AI", "title": "Mixture of Experts (MoE)", "desc": "The model contains many small 'expert' networks; a router sends each token to only 1-2 of them. This is why models like DeepSeek and Mixtral stay fast despite being huge.", "link": "https://huggingface.co/blog/moe"},
    {"cat": "Data Science", "title": "Feature Engineering", "desc": "Turning raw data into meaningful model inputs — extracting day-of-week from dates, encoding categories, building ratios. It often matters more than the choice of model.", "link": "https://developers.google.com/machine-learning/crash-course"},
    {"cat": "Dev", "title": "Idempotency", "desc": "An operation that gives the same result no matter how many times you run it. Critical for APIs and retry logic — a non-idempotent payment endpoint can double-charge.", "link": "https://en.wikipedia.org/wiki/Idempotence"},
    {"cat": "Security", "title": "Prompt Injection", "desc": "The #1 attack on LLM apps: instructions hidden in untrusted content (a web page, an email) hijack the model. Fix: treat tool output as data, never as commands.", "link": "https://owasp.org/www-project-top-10-for-large-language-model-applications/"},
    {"cat": "AI", "title": "RAG (Retrieval-Augmented Generation)", "desc": "Retrieve relevant chunks from your own documents and feed them to the model as context before it answers. Less hallucination, and it works on private data.", "link": "https://huggingface.co/learn"},
    {"cat": "Data Science", "title": "Data Leakage", "desc": "When training data contains information that won't exist at prediction time — the model aces the test set and fails in production. Keep your train/test split time-aware.", "link": "https://scikit-learn.org/stable/common_pitfalls.html"},
    {"cat": "Dev", "title": "CAP Theorem", "desc": "In a distributed system you can't have Consistency, Availability, and Partition-tolerance all at once. During a network partition you must choose between C and A.", "link": "https://en.wikipedia.org/wiki/CAP_theorem"},
    {"cat": "Security", "title": "Supply Chain Attack", "desc": "The attacker doesn't hack you — they hack your dependency (an npm/pip package). Use lockfiles, run `npm audit`, and vet unknown packages before installing.", "link": "https://owasp.org/www-project-dependency-check/"},
    {"cat": "AI", "title": "Quantization", "desc": "Compressing model weights from 16-bit to 4/8-bit — 4x smaller, faster, with a small quality cost. It's how 70B models run on consumer GPUs (GGUF, AWQ).", "link": "https://huggingface.co/docs/optimum/concept_guides/quantization"},
    {"cat": "Data Science", "title": "A/B Testing", "desc": "Randomly split users between two versions and compare them statistically. Never call a winner without understanding p-values and sample size.", "link": "https://en.wikipedia.org/wiki/A/B_testing"},
    {"cat": "Dev", "title": "Event-Driven Architecture", "desc": "Services publish and subscribe to events (Kafka, RabbitMQ) instead of calling each other directly. You gain loose coupling; debugging and ordering get harder.", "link": "https://martinfowler.com/articles/201701-event-driven.html"},
    {"cat": "Security", "title": "Zero Trust", "desc": "The 'inside the network means trusted' model is dead — every request is verified, even internal ones. Identity-based access instead of a VPN perimeter.", "link": "https://www.nist.gov/publications/zero-trust-architecture"},
    {"cat": "AI", "title": "Context Window", "desc": "How much text a model can 'see' at once. A large window fits a whole codebase or document set — but content in the middle of long contexts tends to get missed ('lost in the middle').", "link": "https://huggingface.co/blog"},
    {"cat": "Data Science", "title": "Overfitting vs Underfitting", "desc": "Overfit: the model memorized the training data and fails on new data. Underfit: it never learned the pattern. Fixes: regularization, more data, cross-validation.", "link": "https://scikit-learn.org/stable/auto_examples/model_selection/plot_underfitting_overfitting.html"},
    {"cat": "Dev", "title": "SOLID Principles", "desc": "Five OOP design rules (Single responsibility, Open/closed, Liskov, Interface segregation, Dependency inversion) that keep code maintainable as it grows.", "link": "https://en.wikipedia.org/wiki/SOLID"},
    {"cat": "Security", "title": "OWASP Top 10", "desc": "The official list of the 10 most common web app vulnerabilities — injection, broken auth, SSRF, and more. Every web developer should know it by heart.", "link": "https://owasp.org/www-project-top-ten/"},
    {"cat": "AI", "title": "Fine-tuning vs RAG", "desc": "Fine-tuning changes a model's behavior and style; RAG gives it new knowledge. Use RAG for facts, fine-tuning for tone/format — combining both is common.", "link": "https://huggingface.co/docs/transformers/training"},
    {"cat": "Data Science", "title": "Embeddings", "desc": "Converting text or images into vectors of numbers where similar things end up close together. Semantic search, RAG, and recommendations all run on this.", "link": "https://huggingface.co/blog/getting-started-with-embeddings"},
    {"cat": "Dev", "title": "CI/CD", "desc": "Automatic tests on every commit (CI) and automatic deployment (CD). GitHub Actions is exactly this — this very site now updates daily through it!", "link": "https://docs.github.com/en/actions"},
    {"cat": "Security", "title": "SSRF (Server-Side Request Forgery)", "desc": "An attacker makes your server hit internal URLs (cloud metadata, internal APIs). Validate URL inputs and block internal IP ranges.", "link": "https://owasp.org/www-community/attacks/Server_Side_Request_Forgery"},
    {"cat": "AI", "title": "Agents & Tool Use", "desc": "An LLM doesn't just write text — it calls tools (search, code execution, APIs) and reacts to the results. MCP is becoming the open standard for this.", "link": "https://modelcontextprotocol.io"},
    {"cat": "Dev", "title": "Database Indexing", "desc": "Without an index, a query scans the whole table. The right index means milliseconds; the wrong one means minutes. Run EXPLAIN to see what your query is really doing.", "link": "https://use-the-index-luke.com/"},
]


def http_get(url, timeout=25):
    req = urllib.request.Request(url, headers={
        "User-Agent": "abdulhaseeb2k-site-updater",
        "Accept": "application/vnd.github+json" if "api.github.com" in url else "*/*",
    })
    if GITHUB_TOKEN and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def safe(fn, fallback):
    try:
        return fn()
    except Exception as e:
        print(f"  ⚠ {fn.__name__ if hasattr(fn,'__name__') else 'task'} failed: {e}")
        return fallback


def hn_search(query, pages=1, hits=8, min_points=20, tags="story"):
    url = (f"https://hn.algolia.com/api/v1/search_by_date?query={query}"
           f"&tags={tags}&numericFilters=points>{min_points}&hitsPerPage={hits}")
    d = http_get(url)
    out = []
    for h in d.get("hits", []):
        out.append({
            "title": h.get("title") or "",
            "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
            "points": h.get("points") or 0,
            "comments": h.get("num_comments") or 0,
            "time": h.get("created_at") or "",
        })
    return out


def fetch_ai_news():
    return hn_search("AI%20OR%20LLM%20OR%20GPT%20OR%20Claude%20OR%20Gemini", hits=8, min_points=30)


def fetch_hacking_news():
    return hn_search("security%20OR%20vulnerability%20OR%20exploit%20OR%20CVE%20OR%20breach", hits=8, min_points=15)


def fetch_dev_news():
    return hn_search("programming%20OR%20framework%20OR%20database%20OR%20typescript%20OR%20rust%20OR%20python", hits=8, min_points=25)


def fetch_hn_front():
    d = http_get("https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=6")
    return [{
        "title": h.get("title") or "",
        "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
        "points": h.get("points") or 0,
        "time": h.get("created_at") or "",
    } for h in d.get("hits", [])]


def fetch_models():
    d = http_get("https://huggingface.co/api/models?sort=trendingScore&direction=-1&limit=10")
    return [{
        "id": m.get("id"),
        "pipeline": m.get("pipeline_tag") or "",
        "downloads": m.get("downloads") or 0,
        "likes": m.get("likes") or 0,
    } for m in d if isinstance(m, dict)]


def fetch_trending_repos():
    since = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
    d = http_get(f"https://api.github.com/search/repositories?q=created:>{since}&sort=stars&order=desc&per_page=8")
    return [{
        "name": r.get("full_name"),
        "url": r.get("html_url"),
        "stars": r.get("stargazers_count") or 0,
        "lang": r.get("language") or "",
        "desc": (r.get("description") or "")[:140],
    } for r in d.get("items", [])]


def fetch_famous_repos():
    import time
    out = []
    for full in FAMOUS_REPOS:
        time.sleep(0.4)  # be polite to the API
        try:
            r = http_get(f"https://api.github.com/repos/{full}")
            out.append({
                "name": r.get("full_name") or full,
                "url": r.get("html_url") or f"https://github.com/{full}",
                "stars": r.get("stargazers_count") or 0,
                "lang": r.get("language") or "",
                "desc": (r.get("description") or "")[:160],
                "pushed": r.get("pushed_at") or "",
            })
        except Exception as e:
            print(f"  ⚠ famous repo {full}: {e}")
    out.sort(key=lambda x: -x["stars"])
    return out


def pick_concept():
    day = datetime.now(timezone.utc).timetuple().tm_yday
    return CONCEPTS[day % len(CONCEPTS)]


def main():
    print("Fetching data...")
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ai_news":       safe(fetch_ai_news, []),
        "hacking_news":  safe(fetch_hacking_news, []),
        "dev_news":      safe(fetch_dev_news, []),
        "hn_front":      safe(fetch_hn_front, []),
        "models":        safe(fetch_models, []),
        "trending":      safe(fetch_trending_repos, []),
        "famous_repos":  safe(fetch_famous_repos, []),
        "concept":       pick_concept(),
    }
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "data.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    counts = {k: (len(v) if isinstance(v, list) else 1) for k, v in data.items() if k != "generated_at"}
    print(f"✅ data.json written: {counts}")


if __name__ == "__main__":
    main()
