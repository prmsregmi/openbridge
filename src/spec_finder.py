import httpx
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class SpecResult:
    name: str
    description: str
    spec_url: str
    api_base_url: str
    source: str


async def search_apis_guru(query: str) -> list[SpecResult]:
    """Search APIs.guru directory for OpenAPI specs matching the query."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get("https://api.apis.guru/v2/list.json")
        resp.raise_for_status()
        catalog = resp.json()

    query_lower = query.lower()
    scored: list[tuple[float, str, dict]] = []

    for api_id, api_data in catalog.items():
        provider = api_id.split(":")[0] if ":" in api_id else api_id
        versions = api_data.get("versions", {})
        preferred = api_data.get("preferred", "")
        if not preferred and versions:
            preferred = list(versions.keys())[-1]
        version_data = versions.get(preferred, {})
        info = version_data.get("info", {})
        title = info.get("title", "")

        # Score by matching against provider name and API title
        match_targets = [provider.lower(), title.lower()]
        best_score = max(
            SequenceMatcher(None, query_lower, t).ratio() for t in match_targets
        )

        # Boost exact substring matches (full query found in target)
        if query_lower in provider.lower() or query_lower in title.lower():
            best_score = max(best_score, 0.85)

        # Check individual words — require majority of query words present
        query_words = query_lower.split()
        if len(query_words) > 1:
            combined = f"{provider.lower()} {title.lower()}"
            matched_words = sum(1 for w in query_words if w in combined)
            word_ratio = matched_words / len(query_words)
            if word_ratio < 0.5:
                best_score *= 0.3  # Heavy penalty for low word overlap

        if best_score > 0.45:
            scored.append((best_score, api_id, version_data))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []

    for _, api_id, version_data in scored[:5]:
        info = version_data.get("info", {})
        spec_url = version_data.get("swaggerUrl", "") or version_data.get(
            "openapiVer", ""
        )
        # APIs.guru provides the spec URL directly
        if not spec_url:
            link = version_data.get("link", "")
            if link:
                spec_url = f"https://api.apis.guru/v2/{link}"

        api_base_url = ""
        servers = version_data.get("servers", [])
        if servers:
            api_base_url = servers[0].get("url", "")
        elif "host" in version_data:
            scheme = (version_data.get("schemes") or ["https"])[0]
            api_base_url = f"{scheme}://{version_data['host']}"

        # Infer base URL from provider domain if still empty
        if not api_base_url:
            provider = api_id.split(":")[0] if ":" in api_id else api_id
            if "." in provider:
                api_base_url = f"https://api.{provider}"

        results.append(
            SpecResult(
                name=info.get("title", api_id),
                description=info.get("description", "")[:200],
                spec_url=spec_url,
                api_base_url=api_base_url,
                source="apis.guru",
            )
        )

    return results


async def search_github_specs(query: str, token: str | None = None) -> list[SpecResult]:
    """Search GitHub for OpenAPI spec files matching the query."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    results = []
    filenames = ["openapi.yaml", "openapi.json", "swagger.json", "swagger.yaml"]

    async with httpx.AsyncClient(timeout=30) as client:
        for filename in filenames[:2]:  # Limit to avoid rate limits
            search_query = f"filename:{filename} {query}"
            resp = await client.get(
                "https://api.github.com/search/code",
                params={"q": search_query, "per_page": 3},
                headers=headers,
            )
            if resp.status_code == 403:
                break  # Rate limited
            if resp.status_code != 200:
                continue

            data = resp.json()
            for item in data.get("items", []):
                repo = item.get("repository", {})
                raw_url = (
                    f"https://raw.githubusercontent.com/"
                    f"{repo.get('full_name', '')}/{repo.get('default_branch', 'main')}/"
                    f"{item.get('path', '')}"
                )
                results.append(
                    SpecResult(
                        name=f"{repo.get('full_name', '')} - {item.get('name', '')}",
                        description=repo.get("description", "") or "",
                        spec_url=raw_url,
                        api_base_url="",  # Would need to parse the spec
                        source="github",
                    )
                )

    return results


async def find_spec(query: str, github_token: str | None = None) -> list[SpecResult]:
    """Multi-strategy spec search. Tries APIs.guru first, then GitHub."""
    results = await search_apis_guru(query)
    if results:
        return results

    results = await search_github_specs(query, github_token)
    return results
