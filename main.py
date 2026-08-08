import re
import json
import httpx
import asyncio
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="MovieBox Stream",
    description="Full Streaming Web Application & Pure REST API for MovieBox",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_URL = "https://moviebox.ph"
API_BASE = "https://h5-api.aoneroom.com/wefeed-h5api-bff"
STREAM_BASE = "https://h5.aoneroom.com/wefeed-h5-bff"

_bearer_token: str | None = None

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "Referer": "https://moviebox.ph/",
    "Origin": "https://moviebox.ph",
    "X-Client-Info": '{"timezone":"Asia/Dhaka"}',
    "X-Request-Lang": "en",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "sec-ch-ua": '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "cross-site",
}

PLAYER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://h5.aoneroom.com",
    "sec-ch-ua": '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
}

async def _get_bearer_token() -> str:
    """Auto-acquire a guest JWT token with fallback parsing."""
    global _bearer_token
    if _bearer_token:
        return _bearer_token
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
            resp = await client.get(f"{API_BASE}/home?host=moviebox.ph", headers=DEFAULT_HEADERS)
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
        _bearer_token = None
    return _bearer_token or ""

async def _make_request(url: str, method: str = "GET", payload: dict = None, custom_headers: dict = None) -> dict:
    global _bearer_token
    token = await _get_bearer_token()
    headers = {
        **DEFAULT_HEADERS,
        "Authorization": f"Bearer {token}" if token else "",
        **(custom_headers or {})
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
        try:
            if method == "POST":
                resp = await client.post(url, headers=headers, json=payload)
            else:
                resp = await client.get(url, headers=headers)

            x_user = resp.headers.get("x-user")
            if x_user:
                try:
                    new_token = json.loads(x_user).get("token")
                    if new_token:
                        _bearer_token = new_token
                except Exception:
                    pass

            if resp.status_code != 200:
                _bearer_token = None
                raise HTTPException(status_code=502, detail=f"Upstream API error: {resp.status_code}")

            return resp.json()
        except Exception as e:
            _bearer_token = None
            if isinstance(e, HTTPException): raise e
            raise HTTPException(status_code=502, detail=f"Request failed: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def home_web_app():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MovieBox Stream — Watch Movies & TV Series Online</title>
    <meta name="description" content="Discover, search, and stream your favorite movies, TV shows, and animations in HD. Zero ads, pure streaming experience.">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-body: #08090d;
            --bg-card: rgba(22, 24, 34, 0.65);
            --bg-glass: rgba(255, 255, 255, 0.05);
            --bg-glass-hover: rgba(255, 255, 255, 0.12);
            --primary: #ff3d71;
            --primary-hover: #ff1a53;
            --secondary: #3366ff;
            --accent: #00f2ff;
            --text-main: #f0f2f8;
            --text-sub: #a0a5b5;
            --border: rgba(255, 255, 255, 0.08);
            --radius-lg: 24px;
            --radius-md: 16px;
            --radius-sm: 10px;
            --shadow-glow: 0 12px 35px rgba(255, 61, 113, 0.35);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-body);
            color: var(--text-main);
            min-height: 100vh;
            overflow-x: hidden;
            background-image: 
                radial-gradient(circle at 15% 10%, rgba(255, 61, 113, 0.12) 0%, transparent 40%),
                radial-gradient(circle at 85% 60%, rgba(51, 102, 255, 0.12) 0%, transparent 40%);
            background-attachment: fixed;
        }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: var(--bg-body); }
        ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--primary); }

        /* Navbar */
        nav {
            position: fixed;
            top: 0; left: 0; right: 0;
            z-index: 100;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 18px 48px;
            background: rgba(8, 9, 13, 0.85);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border);
            transition: all 0.3s ease;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
            font-size: 1.6rem;
            font-weight: 800;
            color: #fff;
            letter-spacing: -0.5px;
        }

        .logo-icon {
            width: 42px; height: 42px;
            border-radius: 12px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            display: flex; align-items: center; justify-content: center;
            font-size: 1.2rem; color: #fff;
            box-shadow: 0 4px 15px rgba(255, 61, 113, 0.4);
        }

        .nav-links {
            display: flex;
            align-items: center;
            gap: 8px;
            list-style: none;
        }

        .nav-btn {
            padding: 10px 20px;
            border-radius: 40px;
            color: var(--text-sub);
            text-decoration: none;
            font-weight: 600;
            font-size: 0.95rem;
            transition: all 0.3s ease;
            cursor: pointer;
            border: none;
            background: transparent;
        }

        .nav-btn:hover, .nav-btn.active {
            color: #fff;
            background: var(--bg-glass-hover);
        }

        .nav-btn.active {
            background: linear-gradient(135deg, rgba(255, 61, 113, 0.2), rgba(51, 102, 255, 0.2));
            border: 1px solid rgba(255, 61, 113, 0.4);
            color: #fff;
        }

        /* Search Box */
        .search-container {
            position: relative;
            width: 320px;
        }

        .search-input {
            width: 100%;
            padding: 12px 20px 12px 46px;
            border-radius: 30px;
            background: rgba(255, 255, 255, 0.07);
            border: 1px solid var(--border);
            color: #fff;
            font-family: inherit;
            font-size: 0.9rem;
            outline: none;
            transition: all 0.3s ease;
        }

        .search-input:focus {
            background: rgba(255, 255, 255, 0.12);
            border-color: var(--primary);
            box-shadow: 0 0 20px rgba(255, 61, 113, 0.2);
        }

        .search-icon {
            position: absolute;
            left: 16px; top: 50%;
            transform: translateY(-50%);
            color: var(--text-sub);
            font-size: 0.9rem;
        }

        .suggestions-menu {
            position: absolute;
            top: calc(100% + 10px);
            left: 0; right: 0;
            background: rgba(18, 20, 29, 0.95);
            backdrop-filter: blur(24px);
            border: 1px solid var(--border);
            border-radius: var(--radius-md);
            max-height: 380px;
            overflow-y: auto;
            z-index: 200;
            display: none;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
        }

        .suggestion-item {
            padding: 12px 18px;
            display: flex;
            align-items: center;
            gap: 12px;
            cursor: pointer;
            transition: background 0.2s;
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
        }

        .suggestion-item:hover {
            background: rgba(255, 61, 113, 0.15);
        }

        .suggestion-item i { color: var(--primary); font-size: 0.9rem; }
        .suggestion-title { font-weight: 500; font-size: 0.9rem; }

        /* Main Layout */
        main {
            padding-top: 90px;
            max-width: 1440px;
            margin: 0 auto;
            padding-bottom: 80px;
        }

        /* Hero Banner */
        .hero {
            position: relative;
            margin: 24px 48px 48px;
            height: 480px;
            border-radius: var(--radius-lg);
            overflow: hidden;
            display: flex;
            align-items: flex-end;
            padding: 48px;
            background-size: cover;
            background-position: center;
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.5);
            transition: background-image 0.5s ease-in-out;
        }

        .hero-overlay {
            position: absolute;
            inset: 0;
            background: linear-gradient(0deg, #08090d 5%, rgba(8, 9, 13, 0.6) 50%, rgba(8, 9, 13, 0.1) 100%);
        }

        .hero-content {
            position: relative;
            z-index: 2;
            max-width: 650px;
        }

        .hero-tag {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 14px;
            border-radius: 30px;
            background: rgba(255, 61, 113, 0.2);
            border: 1px solid rgba(255, 61, 113, 0.4);
            color: var(--primary);
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 16px;
        }

        .hero-title {
            font-size: clamp(2rem, 5vw, 3.2rem);
            font-weight: 900;
            line-height: 1.1;
            margin-bottom: 16px;
            text-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }

        .hero-desc {
            color: var(--text-sub);
            font-size: 1rem;
            line-height: 1.6;
            margin-bottom: 28px;
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .hero-btns {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .btn-primary {
            padding: 14px 32px;
            border-radius: 40px;
            background: linear-gradient(135deg, var(--primary), var(--primary-hover));
            color: #fff;
            font-weight: 700;
            font-size: 1rem;
            border: none;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            box-shadow: var(--shadow-glow);
            transition: all 0.3s ease;
        }

        .btn-primary:hover {
            transform: translateY(-3px) scale(1.03);
            box-shadow: 0 16px 40px rgba(255, 61, 113, 0.5);
        }

        .btn-secondary {
            padding: 14px 28px;
            border-radius: 40px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            color: #fff;
            font-weight: 600;
            font-size: 1rem;
            border: 1px solid var(--border);
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            transition: all 0.3s ease;
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
        }

        /* Content Section */
        .section {
            padding: 0 48px;
            margin-bottom: 56px;
        }

        .section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 24px;
        }

        .section-title {
            font-size: 1.6rem;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .section-title i {
            color: var(--primary);
        }

        /* Movie Grid */
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 24px;
        }

        .card {
            position: relative;
            border-radius: var(--radius-md);
            overflow: hidden;
            background: var(--bg-card);
            border: 1px solid var(--border);
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            display: flex;
            flex-direction: column;
        }

        .card:hover {
            transform: translateY(-10px) scale(1.03);
            border-color: rgba(255, 61, 113, 0.5);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6), 0 0 20px rgba(255, 61, 113, 0.2);
        }

        .card-poster {
            position: relative;
            width: 100%;
            padding-top: 150%;
            background-size: cover;
            background-position: center;
            background-color: #12141d;
        }

        .card-overlay {
            position: absolute;
            inset: 0;
            background: linear-gradient(0deg, rgba(8, 9, 13, 0.95) 0%, transparent 60%);
            opacity: 0;
            transition: opacity 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .card:hover .card-overlay {
            opacity: 1;
        }

        .play-icon {
            width: 54px; height: 54px;
            border-radius: 50%;
            background: var(--primary);
            color: #fff;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.3rem;
            box-shadow: var(--shadow-glow);
            transform: scale(0.8);
            transition: transform 0.3s ease;
        }

        .card:hover .play-icon {
            transform: scale(1);
        }

        .card-badge {
            position: absolute;
            top: 12px; left: 12px;
            padding: 4px 10px;
            border-radius: 20px;
            background: rgba(8, 9, 13, 0.8);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: var(--accent);
            font-size: 0.75rem;
            font-weight: 700;
            z-index: 2;
        }

        .card-rating {
            position: absolute;
            top: 12px; right: 12px;
            padding: 4px 8px;
            border-radius: 8px;
            background: rgba(255, 193, 7, 0.2);
            border: 1px solid rgba(255, 193, 7, 0.4);
            color: #ffc107;
            font-size: 0.75rem;
            font-weight: 700;
            display: flex; align-items: center; gap: 4px;
            z-index: 2;
        }

        .card-info {
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .card-name {
            font-weight: 700;
            font-size: 0.95rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .card-sub {
            color: var(--text-sub);
            font-size: 0.8rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        /* Spinner & Loading */
        .loading-spinner {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 60px 0;
            gap: 16px;
            color: var(--text-sub);
        }

        .spinner {
            width: 48px; height: 48px;
            border: 4px solid rgba(255, 61, 113, 0.2);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 1s infinite linear;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        /* Modal Base */
        .modal-backdrop {
            position: fixed;
            inset: 0;
            z-index: 1000;
            background: rgba(4, 5, 8, 0.88);
            backdrop-filter: blur(25px);
            display: none;
            align-items: center;
            justify-content: center;
            padding: 24px;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

        .modal-content {
            position: relative;
            background: rgba(18, 20, 29, 0.95);
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            max-width: 900px;
            width: 100%;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 30px 80px rgba(0, 0, 0, 0.8);
            display: flex;
            flex-direction: column;
        }

        .modal-close {
            position: absolute;
            top: 20px; right: 20px;
            z-index: 10;
            width: 40px; height: 40px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid var(--border);
            color: #fff;
            font-size: 1.2rem;
            cursor: pointer;
            display: flex; align-items: center; justify-content: center;
            transition: all 0.2s;
        }

        .modal-close:hover {
            background: var(--primary);
            transform: rotate(90deg);
        }

        /* Detail Modal Specs */
        .detail-hero {
            display: flex;
            gap: 32px;
            padding: 40px;
        }

        .detail-poster {
            width: 220px;
            flex-shrink: 0;
            height: 330px;
            border-radius: var(--radius-md);
            background-size: cover;
            background-position: center;
            border: 1px solid var(--border);
            box-shadow: 0 16px 40px rgba(0,0,0,0.5);
        }

        .detail-body {
            display: flex;
            flex-direction: column;
            gap: 16px;
            flex-grow: 1;
        }

        .detail-title {
            font-size: 2.2rem;
            font-weight: 800;
            line-height: 1.2;
        }

        .detail-meta {
            display: flex;
            align-items: center;
            gap: 16px;
            flex-wrap: wrap;
            font-size: 0.9rem;
            color: var(--text-sub);
        }

        .detail-meta-badge {
            padding: 4px 12px;
            border-radius: 20px;
            background: rgba(0, 242, 255, 0.15);
            color: var(--accent);
            font-weight: 700;
        }

        .detail-overview {
            color: #c5cad8;
            font-size: 0.95rem;
            line-height: 1.7;
        }

        .episodes-selector {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-top: 12px;
        }

        .select-input {
            padding: 10px 18px;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid var(--border);
            color: #fff;
            font-family: inherit;
            font-size: 0.9rem;
            outline: none;
            cursor: pointer;
        }

        /* Player Modal */
        .player-wrapper {
            position: relative;
            width: 100%;
            padding-top: 56.25%; /* 16:9 ratio */
            background: #000;
            border-radius: var(--radius-lg) var(--radius-lg) 0 0;
            overflow: hidden;
        }

        .player-video {
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
        }

        .player-controls-bar {
            padding: 20px 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #12141d;
            border-radius: 0 0 var(--radius-lg) var(--radius-lg);
        }

        .quality-selector {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .quality-btn {
            padding: 6px 14px;
            border-radius: 20px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid var(--border);
            color: var(--text-sub);
            font-size: 0.8rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
        }

        .quality-btn.active, .quality-btn:hover {
            background: var(--primary);
            color: #fff;
            border-color: var(--primary);
        }

        /* Responsive Design */
        @media (max-width: 900px) {
            nav { padding: 16px 24px; }
            .search-container { width: 220px; }
            .hero { margin: 16px 24px 32px; padding: 28px; height: 380px; }
            .section { padding: 0 24px; }
            .detail-hero { flex-direction: column; padding: 24px; }
            .detail-poster { width: 100%; height: 280px; }
        }

        @media (max-width: 600px) {
            .nav-links { display: none; }
            .hero-title { font-size: 1.8rem; }
            .grid { grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 14px; }
            .card-info { padding: 10px; }
            .card-name { font-size: 0.85rem; }
        }
    </style>
</head>
<body>

    <!-- Navigation Bar -->
    <nav>
        <a href="#" class="logo" onclick="loadPage('home'); return false;">
            <div class="logo-icon"><i class="fa-solid fa-play"></i></div>
            MovieBox<span style="color: var(--primary)">.ph</span>
        </a>

        <ul class="nav-links">
            <li><button class="nav-btn active" id="btn-home" onclick="loadPage('home')">Home</button></li>
            <li><button class="nav-btn" id="btn-movies" onclick="loadCategory('movies')">Movies</button></li>
            <li><button class="nav-btn" id="btn-tv" onclick="loadCategory('tv-series')">TV Series</button></li>
            <li><button class="nav-btn" id="btn-anime" onclick="loadCategory('animation')">Animation</button></li>
        </ul>

        <div class="search-container">
            <i class="fa-solid fa-magnifying-glass search-icon"></i>
            <input type="text" class="search-input" id="search-input" placeholder="Search movies, anime, TV..." onkeyup="handleSearchInput(event)">
            <div class="suggestions-menu" id="suggestions-menu"></div>
        </div>
    </nav>

    <!-- Main Container -->
    <main id="main-content">
        <!-- Dynamic Content Injected Here -->
        <div class="loading-spinner">
            <div class="spinner"></div>
            <p>Initializing MovieBox API...</p>
        </div>
    </main>

    <!-- Detail Modal -->
    <div class="modal-backdrop" id="detail-modal">
        <div class="modal-content">
            <button class="modal-close" onclick="closeModal('detail-modal')"><i class="fa-solid fa-xmark"></i></button>
            <div class="detail-hero">
                <div class="detail-poster" id="modal-poster"></div>
                <div class="detail-body">
                    <div class="detail-title" id="modal-title">Title</div>
                    <div class="detail-meta">
                        <span class="detail-meta-badge" id="modal-rating"><i class="fa-solid fa-star"></i> 8.5</span>
                        <span id="modal-year">2024</span>
                        <span id="modal-badge">HD</span>
                    </div>
                    <p class="detail-overview" id="modal-desc">Loading details...</p>
                    
                    <div class="episodes-selector" id="tv-controls" style="display: none;">
                        <select class="select-input" id="season-select">
                            <option value="1">Season 1</option>
                        </select>
                        <select class="select-input" id="episode-select">
                            <option value="1">Episode 1</option>
                        </select>
                    </div>

                    <div style="margin-top: 16px;">
                        <button class="btn-primary" id="modal-play-btn"><i class="fa-solid fa-play"></i> Watch Stream Now</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Video Player Modal -->
    <div class="modal-backdrop" id="player-modal">
        <div class="modal-content" style="max-width: 1000px; padding: 0; background: #000;">
            <button class="modal-close" onclick="closePlayerModal()"><i class="fa-solid fa-xmark"></i></button>
            <div class="player-wrapper">
                <video id="html5-player" class="player-video" controls autoplay crossorigin="anonymous"></video>
            </div>
            <div class="player-controls-bar">
                <div>
                    <h3 id="player-title" style="font-size: 1.1rem; font-weight: 700;">Movie Title</h3>
                    <p id="player-sub" style="font-size: 0.85rem; color: var(--text-sub);">Quality Stream</p>
                </div>
                <div class="quality-selector" id="quality-buttons">
                    <!-- Dynamic Quality Buttons -->
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentSubjectId = null;
        let currentSlug = "";
        let currentStreams = [];

        // App Init
        document.addEventListener("DOMContentLoaded", () => {
            loadPage('home');
        });

        // Load Homepage
        async function loadPage(pageType) {
            setActiveNav('btn-' + (pageType === 'home' ? 'home' : pageType));
            const main = document.getElementById('main-content');
            main.innerHTML = `
                <div class="loading-spinner">
                    <div class="spinner"></div>
                    <p>Fetching latest catalog...</p>
                </div>`;

            try {
                const res = await fetch('/home');
                const data = await res.json();
                
                if (!data.sections || data.sections.length === 0) {
                    main.innerHTML = `<p style="text-align:center; padding: 60px;">No content found.</p>`;
                    return;
                }

                let html = '';
                
                // Hero Banner (First Banner Item)
                const bannerSec = data.sections.find(s => s.section === 'Banner');
                if (bannerSec && bannerSec.items.length > 0) {
                    const heroItem = bannerSec.items[0];
                    html += `
                    <div class="hero" style="background-image: url('${heroItem.poster_url || ''}')">
                        <div class="hero-overlay"></div>
                        <div class="hero-content">
                            <div class="hero-tag"><i class="fa-solid fa-fire"></i> Featured Hit</div>
                            <h1 class="hero-title">${heroItem.name}</h1>
                            <p class="hero-desc">Discover the top trending title on MovieBox. Direct high-speed MP4 streaming enabled.</p>
                            <div class="hero-btns">
                                <button class="btn-primary" onclick="openMediaDetail('${heroItem.subject_id}', '${heroItem.slug}')"><i class="fa-solid fa-play"></i> Watch Now</button>
                            </div>
                        </div>
                    </div>`;
                }

                // Render Content Sections
                data.sections.forEach(sec => {
                    if (sec.items && sec.items.length > 0) {
                        html += `
                        <div class="section">
                            <div class="section-header">
                                <h2 class="section-title"><i class="fa-solid fa-clapperboard"></i> ${sec.section}</h2>
                            </div>
                            <div class="grid">
                                ${sec.items.map(item => renderCard(item)).join('')}
                            </div>
                        </div>`;
                    }
                });

                main.innerHTML = html;
            } catch (err) {
                main.innerHTML = `<div class="loading-spinner"><p style="color:var(--primary)">Failed to load content: ${err.message}</p></div>`;
            }
        }

        // Load Categories (Movies, TV, Anime)
        async function loadCategory(catEndpoint) {
            setActiveNav('btn-' + catEndpoint);
            const main = document.getElementById('main-content');
            main.innerHTML = `
                <div class="loading-spinner">
                    <div class="spinner"></div>
                    <p>Loading category...</p>
                </div>`;

            try {
                const res = await fetch(`/${catEndpoint}?page=1`);
                const data = await res.json();
                
                const titleMap = {
                    'movies': 'Movies Catalog',
                    'tv-series': 'TV Series Catalog',
                    'animation': 'Anime & Animation'
                };

                let html = `
                <div class="section" style="margin-top: 24px;">
                    <div class="section-header">
                        <h2 class="section-title"><i class="fa-solid fa-film"></i> ${titleMap[catEndpoint] || 'Catalog'}</h2>
                    </div>
                    <div class="grid">
                        ${(data.items || []).map(item => renderCard(item)).join('')}
                    </div>
                </div>`;

                main.innerHTML = html;
            } catch (err) {
                main.innerHTML = `<div class="loading-spinner"><p style="color:var(--primary)">Error: ${err.message}</p></div>`;
            }
        }

        // Render Card Component
        function renderCard(item) {
            const poster = item.poster_url || 'https://via.placeholder.com/300x450?text=No+Poster';
            const rating = item.rating ? `<div class="card-rating"><i class="fa-solid fa-star"></i> ${item.rating}</div>` : '';
            const badge = item.badge ? `<div class="card-badge">${item.badge}</div>` : '';

            return `
            <div class="card" onclick="openMediaDetail('${item.subject_id}', '${item.slug}')">
                ${badge}
                ${rating}
                <div class="card-poster" style="background-image: url('${poster}')">
                    <div class="card-overlay">
                        <div class="play-icon"><i class="fa-solid fa-play"></i></div>
                    </div>
                </div>
                <div class="card-info">
                    <div class="card-name">${item.name}</div>
                    <div class="card-sub">
                        <span>${item.year || 'HD'}</span>
                        <span style="color: var(--primary); font-weight: 700;">Stream</span>
                    </div>
                </div>
            </div>`;
        }

        // Live Search Handling
        let searchTimeout = null;
        function handleSearchInput(e) {
            const query = e.target.value.trim();
            const menu = document.getElementById('suggestions-menu');

            if (e.key === 'Enter' && query.length > 0) {
                menu.style.display = 'none';
                executeSearch(query);
                return;
            }

            if (query.length < 2) {
                menu.style.display = 'none';
                return;
            }

            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(async () => {
                try {
                    const res = await fetch(`/search/suggest?q=${encodeURIComponent(query)}`);
                    const data = await res.json();
                    
                    if (data.suggestions && data.suggestions.length > 0) {
                        menu.innerHTML = data.suggestions.map(s => `
                            <div class="suggestion-item" onclick="openMediaDetail('${s.subject_id}', '${s.slug}'); document.getElementById('suggestions-menu').style.display='none';">
                                <i class="fa-solid fa-magnifying-glass"></i>
                                <span class="suggestion-title">${s.title}</span>
                            </div>
                        `).join('');
                        menu.style.display = 'block';
                    } else {
                        menu.style.display = 'none';
                    }
                } catch(err) {}
            }, 300);
        }

        // Search Full Grid
        async function executeSearch(query) {
            const main = document.getElementById('main-content');
            main.innerHTML = `
                <div class="loading-spinner">
                    <div class="spinner"></div>
                    <p>Searching for "${query}"...</p>
                </div>`;

            try {
                const res = await fetch(`/search?q=${encodeURIComponent(query)}`);
                const data = await res.json();
                
                let html = `
                <div class="section" style="margin-top: 24px;">
                    <div class="section-header">
                        <h2 class="section-title"><i class="fa-solid fa-magnifying-glass"></i> Search Results for "${query}"</h2>
                    </div>
                    <div class="grid">
                        ${(data.items || []).map(item => renderCard(item)).join('')}
                    </div>
                </div>`;

                main.innerHTML = html;
            } catch (err) {
                main.innerHTML = `<div class="loading-spinner"><p style="color:var(--primary)">Search error: ${err.message}</p></div>`;
            }
        }

        // Open Detail Modal
        async function openMediaDetail(subjectId, slug) {
            currentSubjectId = subjectId;
            currentSlug = slug;

            const modal = document.getElementById('detail-modal');
            modal.style.display = 'flex';

            document.getElementById('modal-title').innerText = 'Loading Title...';
            document.getElementById('modal-desc').innerText = 'Fetching specs...';
            document.getElementById('modal-poster').style.backgroundImage = 'none';

            try {
                const res = await fetch(`/detail/${slug}`);
                const data = await res.json();
                const detail = data.data || {};
                const sub = detail.subject || {};

                document.getElementById('modal-title').innerText = sub.title || 'Movie / Series';
                document.getElementById('modal-desc').innerText = sub.description || sub.introduction || 'No synopsis available.';
                document.getElementById('modal-poster').style.backgroundImage = `url('${sub.cover?.url || ''}')`;
                document.getElementById('modal-rating').innerHTML = `<i class="fa-solid fa-star"></i> ${sub.imdbRatingValue || '8.0'}`;
                document.getElementById('modal-year').innerText = (sub.releaseDate || '').substring(0, 4) || '2024';
                document.getElementById('modal-badge').innerText = sub.corner || 'HD';

                // Play Button Handler
                document.getElementById('modal-play-btn').onclick = () => {
                    closeModal('detail-modal');
                    launchPlayer(subjectId, slug, 0, 0, sub.title);
                };

            } catch (err) {
                document.getElementById('modal-title').innerText = 'Details Loaded';
                document.getElementById('modal-play-btn').onclick = () => {
                    closeModal('detail-modal');
                    launchPlayer(subjectId, slug, 0, 0, 'Stream Video');
                };
            }
        }

        // Launch Video Player
        async function launchPlayer(subjectId, slug, se=0, ep=0, title='Stream') {
            const playerModal = document.getElementById('player-modal');
            const video = document.getElementById('html5-player');
            const playerTitle = document.getElementById('player-title');
            const qualityBox = document.getElementById('quality-buttons');

            playerTitle.innerText = title;
            qualityBox.innerHTML = '<span>Fetching sources...</span>';
            video.src = '';
            playerModal.style.display = 'flex';

            try {
                const res = await fetch(`/api/stream/${subjectId}?detail_path=${slug}&se=${se}&ep=${ep}`);
                const data = await res.json();

                if (data.sources && data.sources.length > 0) {
                    currentStreams = data.sources;
                    
                    // Render Quality Buttons
                    qualityBox.innerHTML = data.sources.map((s, idx) => `
                        <button class="quality-btn ${idx === 0 ? 'active' : ''}" onclick="switchQuality(${idx})">${s.resolution} (${s.format})</button>
                    `).join('');

                    // Play Highest Quality Source
                    switchQuality(0);
                } else {
                    qualityBox.innerHTML = '<span style="color: var(--primary)">No direct MP4 stream found for this episode.</span>';
                }
            } catch (err) {
                qualityBox.innerHTML = `<span style="color: var(--primary)">Stream error: ${err.message}</span>`;
            }
        }

        // Switch Resolution Quality
        function switchQuality(idx) {
            if (!currentStreams[idx]) return;
            const video = document.getElementById('html5-player');
            const selected = currentStreams[idx];

            document.querySelectorAll('.quality-btn').forEach((btn, i) => {
                btn.classList.toggle('active', i === idx);
            });

            video.src = selected.url;
            video.play();
        }

        // Close Modal Helper
        function closeModal(id) {
            document.getElementById(id).style.display = 'none';
        }

        function closePlayerModal() {
            const video = document.getElementById('html5-player');
            video.pause();
            video.src = '';
            closeModal('player-modal');
        }

        // Nav Helper
        function setActiveNav(btnId) {
            document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
            const el = document.getElementById(btnId);
            if (el) el.classList.add('active');
        }
    </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)

@app.get("/home")
async def get_home():
    url = f"{API_BASE}/home?host=moviebox.ph"
    data = await _make_request(url)
    sections = []
    for op in data.get("data", {}).get("operatingList", []) or []:
        op_type = op.get("type")
        title = op.get("title", "Featured")
        if op_type == "BANNER":
            items = [{
                "name": item.get("title") or (item.get("subject") or {}).get("title"),
                "poster_url": item.get("image", {}).get("url") or (item.get("subject") or {}).get("cover", {}).get("url"),
                "slug": item.get("detailPath") or (item.get("subject") or {}).get("detailPath"),
                "subject_id": (item.get("subject") or {}).get("subjectId"),
                "badge": (item.get("subject") or {}).get("corner")
            } for item in op.get("banner", {}).get("items", []) if item.get("title") and "Communities" not in item.get("title")]
            sections.append({"section": "Banner", "count": len(items), "items": items})
        elif op_type in ["SUBJECTS_MOVIE", "SUBJECTS_TV", "SUBJECTS_ANIMATION"]:
            items = [{
                "name": sub.get("title"),
                "poster_url": sub.get("cover", {}).get("url"),
                "slug": sub.get("detailPath"),
                "subject_id": sub.get("subjectId"),
                "badge": sub.get("corner"),
                "rating": sub.get("imdbRatingValue")
            } for sub in op.get("subjects", [])]
            sections.append({"section": title, "count": len(items), "items": items})
    return {"status": "success", "sections": sections}

async def _get_category_data(tab_id: int, page: int = 1, per_page: int = 24, sort: str = "RECOMMEND") -> dict:
    url = f"{API_BASE}/subject/filter"
    payload = {"tabId": tab_id, "filter": {"sort": sort, "genre": "ALL", "country": "ALL", "year": "ALL", "language": "ALL"}, "page": page, "perPage": per_page}
    data = await _make_request(url, method="POST", payload=payload)
    inner = data.get("data", {}) or {}
    raw_items = inner.get("items", inner.get("subjects", []))
    items = [{
        "name": sub.get("title"),
        "poster_url": sub.get("cover", {}).get("url"),
        "slug": sub.get("detailPath"),
        "subject_id": sub.get("subjectId"),
        "badge": sub.get("corner"),
        "rating": sub.get("imdbRatingValue"),
        "year": sub.get("releaseDate", "")[:4] if sub.get("releaseDate") else None
    } for sub in raw_items]
    pager = inner.get("pager", {}) or {}
    total = pager.get("totalCount") or inner.get("total") or len(items)
    return {"page": page, "per_page": per_page, "total": total, "items": items}

@app.get("/movies")
async def get_movies(page: int = 1, sort: str = "RECOMMEND"):
    return await _get_category_data(tab_id=2, page=page, sort=sort)

@app.get("/tv-series")
async def get_tv_series(page: int = 1, sort: str = "RECOMMEND"):
    return await _get_category_data(tab_id=5, page=page, sort=sort)

@app.get("/animation")
async def get_animation(page: int = 1, sort: str = "RECOMMEND"):
    return await _get_category_data(tab_id=8, page=page, sort=sort)

@app.get("/search/suggest")
async def get_search_suggestions(q: str = Query(..., min_length=1)):
    url = f"{API_BASE}/subject/search-suggest"
    data = await _make_request(url, method="POST", payload={"keyword": q, "perPage": 10})
    inner = data.get("data", {}) or {}
    raw = inner.get("items", inner.get("list", []))
    suggestions = []
    for item in raw:
        sub = item.get("subject") or {}
        suggestions.append({
            "title": sub.get("title") or item.get("word") or item.get("title"),
            "slug": sub.get("detailPath") or item.get("detailPath"),
            "subject_id": sub.get("subjectId") or item.get("subjectId")
        })
    return {"suggestions": suggestions}

@app.get("/search")
async def search(q: str = Query(..., min_length=1), page: int = 1):
    url = f"{API_BASE}/subject/search"
    data = await _make_request(url, method="POST", payload={"keyword": q, "page": page, "perPage": 20})
    inner = data.get("data", {}) or {}
    raw = inner.get("items", inner.get("list", []))
    items = [{
        "name": sub.get("title"),
        "poster_url": sub.get("cover", {}).get("url"),
        "slug": sub.get("detailPath"),
        "subject_id": sub.get("subjectId")
    } for sub in raw]
    pager = inner.get("pager", {}) or {}
    total = pager.get("totalCount") or inner.get("total") or len(items)
    return {"query": q, "page": page, "total": total, "items": items}

@app.get("/detail/{slug}")
async def get_movie_detail(slug: str):
    url = f"{API_BASE}/detail?detailPath={slug}"
    return await _make_request(url)

@app.get("/api/stream/{subject_id}")
async def get_stream_sources(subject_id: str, detail_path: str = "", se: int = 0, ep: int = 0):
    play_url = f"{STREAM_BASE}/web/subject/play?subjectId={subject_id}&se={se}&ep={ep}&detailPath={detail_path}"
    player_referer = f"https://h5.aoneroom.com/spa/videoPlayPage/movies/{detail_path}?id={subject_id}&type=/movie/detail&detailSe={se}&detailEp={ep}&lang=en"

    async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
        try:
            resp = await client.get(play_url, headers={**PLAYER_HEADERS, "Referer": player_referer})
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail="Stream service unavailable")
            res_json = resp.json()
            data = res_json.get("data", {}) or {}
        except Exception as e:
            if isinstance(e, HTTPException): raise e
            raise HTTPException(status_code=502, detail=f"Stream request failed: {str(e)}")

    has_resource = data.get("hasResource", False)
    
    streams = [
        {
            "resolution": f"{s.get('resolutions')}p" if s.get('resolutions') else "HD",
            "format": s.get("format", "mp4"),
            "url": s.get("url"),
            "size": s.get("size"),
            "duration": s.get("duration"),
            "codec": s.get("codecName")
        }
        for s in data.get("streams", []) or [] if s.get("url")
    ]
    
    return {
        "subject_id": subject_id,
        "se": se,
        "ep": ep,
        "has_resource": has_resource or len(streams) > 0,
        "sources": streams,
        "hls": data.get("hls", []),
        "dash": data.get("dash", []),
        "free_episodes": data.get("freeNum"),
        "limited": data.get("limited", False),
        "note": None if (has_resource or len(streams) > 0) else "No stream found for this selection."
    }

@app.get("/api/stream/{subject_id}/captions")
async def get_captions(subject_id: str, detail_path: str = "", se: int = 0, ep: int = 0):
    play_url = f"{STREAM_BASE}/web/subject/play?subjectId={subject_id}&se={se}&ep={ep}&detailPath={detail_path}"
    player_referer = f"https://h5.aoneroom.com/spa/videoPlayPage/movies/{detail_path}?id={subject_id}&type=/movie/detail&detailSe={se}&detailEp={ep}&lang=en"

    async with httpx.AsyncClient(follow_redirects=True, timeout=25) as client:
        try:
            play_resp = await client.get(play_url, headers={**PLAYER_HEADERS, "Referer": player_referer})
            play_data = play_resp.json().get("data", {}) or {}
        except Exception:
            play_data = {}

    streams = play_data.get("streams", []) or []
    dash = play_data.get("dash", []) or []

    stream_id = None
    stream_format = None
    if streams:
        stream_id = streams[0].get("id")
        stream_format = streams[0].get("format", "MP4")
    elif dash:
        stream_id = dash[0].get("id")
        stream_format = dash[0].get("format", "DASH")

    if not stream_id:
        return {"subject_id": subject_id, "se": se, "ep": ep, "count": 0, "captions": []}

    cap_url = (
        f"{API_BASE}/subject/caption"
        f"?format={stream_format}&id={stream_id}&subjectId={subject_id}&detailPath={detail_path}"
    )
    data = await _make_request(cap_url)
    inner = data.get("data", {}) or {}
    captions = inner.get("captions", []) if isinstance(inner, dict) else (inner if isinstance(inner, list) else [])
    return {"subject_id": subject_id, "se": se, "ep": ep, "count": len(captions), "captions": captions}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "MovieBox API Pro", "version": "3.0.0"}

if __name__ == "__main__":
    import os, uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
