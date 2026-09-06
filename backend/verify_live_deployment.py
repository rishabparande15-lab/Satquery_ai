"""Production Live Backend Verification Script.

Usage:
    python backend/verify_live_deployment.py https://<your-actual-render-url>

Verifies:
1. GET /health
2. GET /api/health
3. POST /api/search with {"query": "Amazon", "limit": 3}
4. GET /api/scenes/{scene_id}
5. POST /api/analyze with real scene ID
6. CORS headers for Netlify domain
"""

import sys
import json
import httpx

def main():
    if len(sys.argv) < 2:
        print("Usage: python backend/verify_live_deployment.py <BACKEND_HTTPS_URL>")
        print("Example: python backend/verify_live_deployment.py https://satquery-backend-xyz.onrender.com")
        sys.exit(1)

    base_url = sys.argv[1].rstrip("/")
    netlify_domain = "https://satquery-ai.netlify.app"

    print("=" * 60)
    print(f"  VERIFYING LIVE BACKEND: {base_url}")
    print("=" * 60)

    # 1. Test /health
    print("\n[1/6] Testing GET /health ...")
    try:
        r = httpx.get(f"{base_url}/health", timeout=30.0)
        print(f"Status: {r.status_code}")
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        data = r.json()
        print("Response:", json.dumps(data, indent=2))
        assert data.get("status") == "ok"
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)

    # 2. Test /api/health
    print("\n[2/6] Testing GET /api/health ...")
    try:
        r = httpx.get(f"{base_url}/api/health", timeout=30.0)
        print(f"Status: {r.status_code}")
        assert r.status_code == 200
        data = r.json()
        print("Response:", json.dumps(data, indent=2))
        assert data.get("status") == "ok"
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)

    # 3. Test CORS preflight & headers
    print("\n[3/6] Testing CORS for Netlify ...")
    try:
        opt_resp = httpx.request(
            "OPTIONS",
            f"{base_url}/api/search",
            headers={
                "Origin": netlify_domain,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
            timeout=15.0,
        )
        print(f"OPTIONS status: {opt_resp.status_code}")
        acao = opt_resp.headers.get("access-control-allow-origin")
        print(f"Access-Control-Allow-Origin: {acao}")
        assert acao == netlify_domain, f"CORS origin mismatch: {acao}"
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)

    # 4. Test /api/search with query 'Amazon'
    print("\n[4/6] Testing POST /api/search with query: 'Amazon' ...")
    try:
        search_resp = httpx.post(
            f"{base_url}/api/search",
            json={"query": "Amazon", "limit": 3},
            headers={"Origin": netlify_domain, "Content-Type": "application/json"},
            timeout=30.0,
        )
        print(f"Search status: {search_resp.status_code}")
        assert search_resp.status_code == 200, f"Search failed: {search_resp.text}"
        scenes = search_resp.json()
        print(f"Scenes returned: {len(scenes)}")
        assert len(scenes) > 0, "Zero scenes returned"
        scene = scenes[0]
        scene_id = scene["id"]
        print(f"Target Scene ID: {scene_id}")
        print(f"Location Name: {scene.get('locationName')}")
        print(f"Bounding Box: {scene.get('boundingBox')}")
        print(f"Is Real Data: {scene.get('isRealData')}")
        assert "Amazon" in scene.get("locationName", "")
        assert scene.get("isRealData") is True
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)

    # 5. Test /api/scenes/{scene_id}
    print(f"\n[5/6] Testing GET /api/scenes/{scene_id} ...")
    try:
        meta_resp = httpx.get(
            f"{base_url}/api/scenes/{scene_id}",
            headers={"Origin": netlify_domain},
            timeout=30.0,
        )
        print(f"Scene detail status: {meta_resp.status_code}")
        assert meta_resp.status_code == 200
        meta = meta_resp.json()
        print(f"Total STAC Assets: {len(meta.get('assets', {}))}")
        print(f"Red Asset (B04): {meta.get('assets', {}).get('red', {}).get('href')}")
        print(f"NIR Asset (B08): {meta.get('assets', {}).get('nir', {}).get('href')}")
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)

    # 6. Test /api/analyze with real scene ID
    print(f"\n[6/6] Testing POST /api/analyze for scene: {scene_id} ...")
    try:
        analyze_resp = httpx.post(
            f"{base_url}/api/analyze",
            json={
                "scene_id": scene_id,
                "query": "Assess Amazon rainforest canopy health",
                "window_pixels": 256,
            },
            headers={"Origin": netlify_domain, "Content-Type": "application/json"},
            timeout=60.0,
        )
        print(f"Analyze status: {analyze_resp.status_code}")
        assert analyze_resp.status_code == 200, f"Analyze failed: {analyze_resp.text}"
        analysis = analyze_resp.json()
        print(f"Job ID: {analysis.get('job_id')}")
        print(f"Mean NDVI: {analysis.get('mean_ndvi')}")
        print(f"Valid Pixels: {analysis.get('valid_pixels')}/{analysis.get('total_pixels')}")
        print(f"Vegetation Density: {analysis.get('vegetation_density')}")
        print(f"Is Real Analysis: {analysis.get('is_real_analysis')}")
        assert analysis.get("is_real_analysis") is True
        assert analysis.get("mean_ndvi") is not None
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  ALL LIVE ENDPOINTS AND REAL NDVI ANALYSES VERIFIED!")
    print("=" * 60)
    print(f"\nConfigure your Netlify site with:")
    print(f"  NEXT_PUBLIC_API_BASE_URL={base_url}")

if __name__ == "__main__":
    main()
