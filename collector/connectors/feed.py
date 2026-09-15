import json
import os
from typing import Iterable
from urllib.request import Request, urlopen

from .base import StoreConnector
from ..models import NormalizedOffer


def _first(item, *keys):
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return None


class JsonFeedConnector(StoreConnector):
    """Generic adapter for an approved JSON product feed/API.

    The feed must return a JSON array or {"products": [...]} and use the
    normalized field names documented in README. No synthetic records are made.
    """

    def __init__(self, slug: str, name: str, url: str, token: str | None = None):
        self.slug, self.name, self.url, self.token = slug, name, url, token

    def fetch(self) -> Iterable[NormalizedOffer]:
        headers = {"Accept": "application/json", "User-Agent": "ZenGhuntCollector/1.0"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = Request(self.url, headers=headers)
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
        rows = payload.get("products", payload) if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            raise ValueError(f"{self.slug}: feed must be a JSON array or contain products[]")

        for item in rows:
            if not isinstance(item, dict):
                continue
            price = _first(item, "price", "current_price")
            product_id = _first(item, "store_product_id", "product_id", "id")
            url = _first(item, "product_url", "url")
            title = _first(item, "title", "name")
            if price is None or not product_id or not url or not title:
                continue
            try:
                yield NormalizedOffer(
                    store=self.slug,
                    store_product_id=str(product_id),
                    product_url=str(url),
                    title=str(title),
                    price=float(price),
                    mrp=float(_first(item, "mrp", "list_price")) if _first(item, "mrp", "list_price") is not None else None,
                    image_url=_first(item, "image_url", "image"),
                    brand=_first(item, "brand"),
                    category=_first(item, "category"),
                    model_number=_first(item, "model_number", "model"),
                    global_product_id=_first(item, "global_product_id", "gtin", "ean", "upc"),
                    currency=str(_first(item, "currency") or "INR"),
                    availability=bool(_first(item, "availability", "in_stock") if _first(item, "availability", "in_stock") is not None else True),
                    offer_title=_first(item, "offer_title"),
                    offer_description=_first(item, "offer_description"),
                    coupon_code=_first(item, "coupon_code"),
                    discount_text=_first(item, "discount_text"),
                    valid_until=_first(item, "valid_until"),
                    metadata=item,
                )
            except (TypeError, ValueError):
                continue


def configured_connectors() -> list[JsonFeedConnector]:
    """Build connectors from GitHub Actions environment variables.

    Example: ZENGHUNT_FEED_AMAZON_URL + optional ZENGHUNT_FEED_AMAZON_TOKEN.
    Keeping URLs/secrets in Actions avoids exposing credentials in GitHub Pages.
    """
    connectors = []
    stores = {
        "amazon": "Amazon",
        "flipkart": "Flipkart",
        "myntra": "Myntra",
        "ajio": "AJIO",
        "meesho": "Meesho",
        "tatacliq": "Tata CLiQ",
        "croma": "Croma",
        "reliancedigital": "Reliance Digital",
    }
    for slug, name in stores.items():
        url = os.getenv(f"ZENGHUNT_FEED_{slug.upper()}_URL")
        if url:
            connectors.append(JsonFeedConnector(slug, name, url, os.getenv(f"ZENGHUNT_FEED_{slug.upper()}_TOKEN")))
    return connectors
