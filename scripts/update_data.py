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
    # "REPLACE/grify",  # <- "grify" ka exact naam mila to yahan add karein
]

# ------------------------------------------------------------------
# 💡 CONCEPT OF THE DAY — rotates daily (AI / Data Science / Dev / Security)
# ------------------------------------------------------------------
CONCEPTS = [
    {"cat": "AI", "title": "Mixture of Experts (MoE)", "desc": "Model ke andar kai chhote 'expert' networks hote hain; router har token ko sirf 1-2 experts ke paas bhejta hai. Isi liye DeepSeek/Mixtral jaise models bade ho kar bhi fast hain.", "link": "https://huggingface.co/blog/moe"},
    {"cat": "Data Science", "title": "Feature Engineering", "desc": "Raw data se model ke liye meaningful inputs banana — dates se day-of-week nikalna, categories encode karna, ratios banana. Aksar model choice se zyada farq isi se parta hai.", "link": "https://developers.google.com/machine-learning/crash-course"},
    {"cat": "Dev", "title": "Idempotency", "desc": "Ek operation jitni dafa bhi chalao, result same rahe. APIs aur retry logic ke liye critical — payment endpoint idempotent na ho to double-charge ho sakta hai.", "link": "https://en.wikipedia.org/wiki/Idempotence"},
    {"cat": "Security", "title": "Prompt Injection", "desc": "LLM apps ka #1 attack: untrusted content (web page, email) mein chhupi instructions model ko hijack kar leti hain. Fix: tool outputs ko data samjho, commands nahi.", "link": "https://owasp.org/www-project-top-10-for-large-language-model-applications/"},
    {"cat": "AI", "title": "RAG (Retrieval-Augmented Generation)", "desc": "Model ko jawab dene se pehle apne documents se relevant chunks retrieve kar ke context mein dena. Hallucination kam, private data pe kaam mumkin.", "link": "https://huggingface.co/learn"},
    {"cat": "Data Science", "title": "Data Leakage", "desc": "Jab training data mein aisi info aa jaye jo prediction time pe available nahi hogi — model test pe perfect, production mein fail. Train/test split hamesha time-aware rakho.", "link": "https://scikit-learn.org/stable/common_pitfalls.html"},
    {"cat": "Dev", "title": "CAP Theorem", "desc": "Distributed system mein Consistency, Availability, Partition-tolerance — teeno ek sath nahi mil sakte. Network partition pe C ya A mein se ek choose karna parta hai.", "link": "https://en.wikipedia.org/wiki/CAP_theorem"},
    {"cat": "Security", "title": "Supply Chain Attack", "desc": "Attacker aap ko nahi, aap ki dependency ko hack karta hai (npm/pip package). Lockfiles use karo, `npm audit` chalao, unknown packages install se pehle check karo.", "link": "https://owasp.org/www-project-dependency-check/"},
    {"cat": "AI", "title": "Quantization", "desc": "Model weights ko 16-bit se 4/8-bit mein compress karna — size 4x kam, speed zyada, quality thori si girti hai. Isi se 70B models consumer GPUs pe chalte hain (GGUF, AWQ).", "link": "https://huggingface.co/docs/optimum/concept_guides/quantization"},
    {"cat": "Data Science", "title": "A/B Testing", "desc": "Do versions ko randomly split users pe chala kar statistically compare karna. p-value aur sample size samjhe baghair results pe faisla mat karo.", "link": "https://en.wikipedia.org/wiki/A/B_testing"},
    {"cat": "Dev", "title": "Event-Driven Architecture", "desc": "Services direct calls ki bajaye events publish/subscribe karti hain (Kafka, RabbitMQ). Loose coupling milti hai, lekin debugging aur ordering mushkil ho jati hai.", "link": "https://martinfowler.com/articles/201701-event-driven.html"},
    {"cat": "Security", "title": "Zero Trust", "desc": "'Network ke andar ho to trusted' wala model khatam — har request verify hoti hai chahe andar se aaye. VPN ki jagah identity-based access.", "link": "https://www.nist.gov/publications/zero-trust-architecture"},
    {"cat": "AI", "title": "Context Window", "desc": "Model ek waqt mein kitna text 'dekh' sakta hai. Bara window = poori codebase/documents ek sath. Lekin lambe context mein beech ka content miss hone lagta hai ('lost in the middle').", "link": "https://huggingface.co/blog"},
    {"cat": "Data Science", "title": "Overfitting vs Underfitting", "desc": "Overfit: model ne training data ratta laga liya, naye data pe fail. Underfit: pattern seekha hi nahi. Fix: regularization, more data, cross-validation.", "link": "https://scikit-learn.org/stable/auto_examples/model_selection/plot_underfitting_overfitting.html"},
    {"cat": "Dev", "title": "SOLID Principles", "desc": "5 OOP design rules (Single responsibility, Open/closed, Liskov, Interface segregation, Dependency inversion) jo code ko maintainable banate hain.", "link": "https://en.wikipedia.org/wiki/SOLID"},
    {"cat": "Security", "title": "OWASP Top 10", "desc": "Web apps ki 10 sab se common vulnerabilities ki official list — injection, broken auth, SSRF waghera. Har web developer ko yaad honi chahiye.", "link": "https://owasp.org/www-project-top-ten/"},
    {"cat": "AI", "title": "Fine-tuning vs RAG", "desc": "Fine-tuning model ka behavior/style badalti hai; RAG usay naya knowledge deta hai. Facts ke liye RAG, tone/format ke liye fine-tuning — dono ka combo bhi common hai.", "link": "https://huggingface.co/docs/transformers/training"},
    {"cat": "Data Science", "title": "Embeddings", "desc": "Text/images ko numbers ke vectors mein convert karna jahan similar cheezein paas hoti hain. Semantic search, RAG, recommendations — sab isi pe chalte hain.", "link": "https://huggingface.co/blog/getting-started-with-embeddings"},
    {"cat": "Dev", "title": "CI/CD", "desc": "Har commit pe automatic tests (CI) aur automatic deployment (CD). GitHub Actions isi ka tool hai — ye site bhi ab isi se daily update hoti hai!", "link": "https://docs.github.com/en/actions"},
    {"cat": "Security", "title": "SSRF (Server-Side Request Forgery)", "desc": "Attacker server se andruni URLs (cloud metadata, internal APIs) hit karwata hai. URL inputs ko validate karo, internal ranges block karo.", "link": "https://owasp.org/www-community/attacks/Server_Side_Request_Forgery"},
    {"cat": "AI", "title": "Agents & Tool Use", "desc": "LLM sirf text nahi likhta — tools call karta hai (search, code run, APIs) aur results pe react karta hai. MCP is ka open standard ban raha hai.", "link": "https://modelcontextprotocol.io"},
    {"cat": "Dev", "title": "Database Indexing", "desc": "Index ke baghair query poori table scan karti hai. Sahi index se milliseconds, ghalat se minutes. EXPLAIN chala kar dekho query kya kar rahi hai.", "link": "https://use-the-index-luke.com/"},
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
