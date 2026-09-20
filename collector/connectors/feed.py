import json
import os
from typing import Iterable
from urllib.parse import urlencode
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
    """Generic adapter for an approved JSON product feed/API."""

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


class FlipkartAffiliateConnector(StoreConnector):
    """Official Flipkart Affiliate API search connector.

    Requires an approved Flipkart Affiliate account, tracking ID and API token.
    No product-page scraping is performed.
    """

    API_URL = "https://affiliate-api.flipkart.net/affiliate/1.0/search/json"

    def __init__(self, tracking_id: str, token: str, queries: list[str]):
        self.slug = "flipkart"
        self.name = "Flipkart"
        self.tracking_id = tracking_id
        self.token = token
        self.queries = queries

    def fetch(self) -> Iterable[NormalizedOffer]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "ZenGhuntCollector/1.0",
            "Fk-Affiliate-Id": self.tracking_id,
            "Fk-Affiliate-Token": self.token,
        }
        for query in self.queries:
            params = urlencode({"query": query, "resultCount": 10})
            request = Request(f"{self.API_URL}?{params}", headers=headers)
            with urlopen(request, timeout=30) as response:
                payload = json.load(response)

            rows = payload.get("productInfoList", []) if isinstance(payload, dict) else []
            for row in rows:
                base = row.get("productBaseInfoV1", {}) if isinstance(row, dict) else {}
                shipping = row.get("productShippingInfoV1", {}) if isinstance(row, dict) else {}
                product_id = base.get("productId")
                title = base.get("title")
                product_url = base.get("productUrl")
                if not product_id or not title or not product_url:
                    continue

                mrp_obj = base.get("maximumRetailPrice") or base.get("mrp") or {}
                selling_obj = base.get("flipkartSellingPrice") or base.get("price") or {}
                special_obj = base.get("flipkartSpecialPrice") or base.get("specialPrice") or {}
                mrp = mrp_obj.get("amount") if isinstance(mrp_obj, dict) else mrp_obj
                price = special_obj.get("amount") if isinstance(special_obj, dict) else special_obj
                if price in (None, ""):
                    price = selling_obj.get("amount") if isinstance(selling_obj, dict) else selling_obj
                if price in (None, ""):
                    continue

                images = base.get("imageUrls") or {}
                image_url = None
                if isinstance(images, dict):
                    image_url = images.get("400x400") or images.get("200x200") or images.get("800x800")
                    if not image_url and images:
                        image_url = next(iter(images.values()))

                category = base.get("categoryPath") or base.get("categoryPaths")
                brand = base.get("productBrand")
                availability = base.get("inStock", True) and base.get("isAvailable", True)
                offer_text = base.get("offers")

                try:
                    yield NormalizedOffer(
                        store=self.slug,
                        store_product_id=str(product_id),
                        product_url=str(product_url),
                        title=str(title),
                        price=float(price),
                        mrp=float(mrp) if mrp not in (None, "") else None,
                        image_url=image_url,
                        brand=str(brand) if brand else None,
                        category=str(category) if category else None,
                        currency="INR",
                        availability=bool(availability),
                        offer_description=str(offer_text) if offer_text else None,
                        metadata={"query": query, "shipping": shipping, "raw": row},
                    )
                except (TypeError, ValueError):
                    continue


def configured_connectors() -> list[StoreConnector]:
    """Build connectors from GitHub Actions environment variables."""
    connectors: list[StoreConnector] = []

    flipkart_id = os.getenv("FLIPKART_AFFILIATE_ID")
    flipkart_token = os.getenv("FLIPKART_AFFILIATE_TOKEN")
    if flipkart_id and flipkart_token:
        queries = [q.strip() for q in os.getenv(
            "FLIPKART_AFFILIATE_QUERIES",
            "wireless headphones,smartphone,smartwatch,laptop"
        ).split(",") if q.strip()]
        connectors.append(FlipkartAffiliateConnector(flipkart_id, flipkart_token, queries))

    stores = {
        "amazon": "Amazon",
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
