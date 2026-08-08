#!/usr/bin/env python3
"""
MovieBox Stream Search & Direct Link Extractor
----------------------------------------------
A standalone Python tool to search any movie, TV series, or anime on MovieBox
and instantly extract direct MP4 stream URLs in 1080p, 720p, 480p, 360p.

Usage:
  python stream_search.py
  python stream_search.py --query "Naruto" --se 1 --ep 1
"""

import re
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error

API_BASE = "https://h5-api.aoneroom.com/wefeed-h5api-bff"
STREAM_BASE = "https://h5.aoneroom.com/wefeed-h5-bff"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "Referer": "https://moviebox.ph/",
    "Origin": "https://moviebox.ph",
    "X-Client-Info": '{"timezone":"Asia/Dhaka"}',
    "X-Request-Lang": "en",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

PLAYER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://h5.aoneroom.com",
}

_bearer_token = None

def get_bearer_token():
    global _bearer_token
    if _bearer_token:
        return _bearer_token
    try:
        req = urllib.request.Request(f"{API_BASE}/home?host=moviebox.ph", headers=DEFAULT_HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            x_user = resp.headers.get("x-user")
            if x_user:
                try:
                    _bearer_token = json.loads(x_user).get("token")
                except Exception:
                    pass
            if not _bearer_token:
                cookie = resp.headers.get("set-cookie", "")
                m = re.search(r"token=([^;]+)", cookie)
                if m:
                    _bearer_token = m.group(1)
    except Exception:
        pass
    return _bearer_token or ""

def api_request(url, method="GET", payload=None, custom_headers=None):
    token = get_bearer_token()
    headers = {
        **DEFAULT_HEADERS,
        "Authorization": f"Bearer {token}" if token else "",
        **(custom_headers or {})
    }
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    
    with urllib.request.urlopen(req, timeout=25) as resp:
        content = resp.read().decode("utf-8")
        return json.loads(content) if content else {}

def search_titles(query):
    url = f"{API_BASE}/subject/search"
    payload = {"keyword": query, "page": 1, "perPage": 10}
    res = api_request(url, method="POST", payload=payload)
    inner = res.get("data", {}) or {}
    raw = inner.get("items", inner.get("list", []))
    
    results = []
    for item in raw:
        results.append({
            "name": item.get("title") or (item.get("subject") or {}).get("title"),
            "slug": item.get("detailPath") or (item.get("subject") or {}).get("detailPath"),
            "subject_id": item.get("subjectId") or (item.get("subject") or {}).get("subjectId")
        })
    return [r for r in results if r["name"] and r["subject_id"]]

def get_detail(slug):
    url = f"{API_BASE}/detail?detailPath={slug}"
    res = api_request(url)
    return res.get("data", {}) or {}

def get_stream_urls(subject_id, detail_path, se=0, ep=0):
    def fetch_play(s, e):
        play_url = f"{STREAM_BASE}/web/subject/play?subjectId={subject_id}&se={s}&ep={e}&detailPath={detail_path}"
        referer = f"https://h5.aoneroom.com/spa/videoPlayPage/movies/{detail_path}?id={subject_id}&type=/movie/detail&detailSe={s}&detailEp={e}&lang=en"
        headers = {**PLAYER_HEADERS, "Referer": referer}
        req = urllib.request.Request(play_url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                content = resp.read().decode("utf-8")
                return json.loads(content).get("data", {}) or {}
        except Exception:
            return {}

    data = fetch_play(se, ep)
    raw_streams = data.get("streams", []) or []

    # Smart fallback for TV shows
    if not raw_streams and se == 0 and ep == 0:
        data = fetch_play(1, 1)
        raw_streams = data.get("streams", []) or []
        if raw_streams:
            se, ep = 1, 1

    streams = []
    for s in raw_streams:
        if s.get("url"):
            res = f"{s.get('resolutions')}p" if s.get('resolutions') and str(s.get('resolutions')) != "0" else "HD"
            size_mb = f"{round(int(s.get('size', 0)) / (1024*1024), 1)} MB" if s.get('size') else "N/A"
            duration_min = f"{int(s.get('duration', 0)) // 60}m {int(s.get('duration', 0)) % 60}s" if s.get('duration') else "N/A"
            streams.append({
                "resolution": res,
                "format": s.get("format", "MP4"),
                "size": size_mb,
                "duration": duration_min,
                "url": s.get("url")
            })
    return {"se": se, "ep": ep, "streams": streams}

def main():
    parser = argparse.ArgumentParser(description="MovieBox Search & Stream Extractor")
    parser.add_argument("--query", "-q", help="Search title (e.g. Naruto, Attack on Titan, Inception)")
    parser.add_argument("--se", type=int, default=0, help="Season number (default: 0 for movie / 1 for show)")
    parser.add_argument("--ep", type=int, default=0, help="Episode number (default: 0 for movie / 1 for show)")
    args = parser.parse_args()

    query = args.query
    if not query:
        print("\n🎬 ================= MovieBox Stream Extractor ================= 🎬")
        query = input("--> Enter Movie or TV Show name to search: ").strip()

    if not query:
        print("No search term entered.")
        return

    print(f"\n🔍 Searching for '{query}'...")
    results = search_titles(query)

    if not results:
        print("❌ No titles found.")
        return

    print(f"\nFound {len(results)} matches:")
    for idx, item in enumerate(results, 1):
        print(f"  [{idx}] {item['name']} (ID: {item['subject_id']})")

    if len(results) == 1 or args.query:
        choice = 1
    else:
        try:
            choice_str = input(f"\nSelect a title [1-{len(results)}]: ").strip()
            choice = int(choice_str) if choice_str else 1
        except ValueError:
            choice = 1

    selected = results[max(0, min(choice - 1, len(results) - 1))]
    print(f"\n📌 Selected: {selected['name']}")

    se, ep = args.se, args.ep
    if not args.query:
        # Check if TV Show details available
        detail = get_detail(selected['slug'])
        resource = detail.get("resource", {}) or {}
        seasons = resource.get("seasons", [])
        if seasons:
            print(f"📺 TV Series Detected! Available Seasons: {len(seasons)}")
            se_input = input(f"Enter Season number [1-{len(seasons)}] (default 1): ").strip()
            se = int(se_input) if se_input.isdigit() else 1

            season_obj = next((s for s in seasons if s.get("se") == se), seasons[0])
            max_ep = season_obj.get("maxEp", 1)
            ep_input = input(f"Enter Episode number [1-{max_ep}] (default 1): ").strip()
            ep = int(ep_input) if ep_input.isdigit() else 1
        else:
            se, ep = 0, 0

    print(f"\n⚡ Extracting stream URLs for Season {se}, Episode {ep}...")
    stream_data = get_stream_urls(selected['subject_id'], selected['slug'], se=se, ep=ep)
    streams = stream_data["streams"]

    if not streams:
        print("❌ No direct MP4 stream links found for this selection.")
        return

    print(f"\n✅ Direct Stream Links Extracted Successfully ({len(streams)} qualities available):\n")
    for s in streams:
        print(f"  • Quality: {s['resolution']} ({s['format']}) | Size: {s['size']} | Duration: {s['duration']}")
        print(f"    URL: {s['url']}\n")

if __name__ == "__main__":
    main()
