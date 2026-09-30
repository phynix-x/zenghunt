import json
import os
import csv
import io
import xml.etree.ElementTree as ET
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



class RemoteProductFeedConnector(StoreConnector):
    """Approved remote product feed adapter for JSON, CSV, XML/TXT exports."""

    def __init__(self, slug: str, name: str, url: str, token: str | None = None, fmt: str = "auto"):
        self.slug, self.name, self.url, self.token, self.fmt = slug, name, url, token, fmt.lower()

    def _download(self):
        headers = {"Accept": "application/json,application/xml,text/csv,text/plain,*/*", "User-Agent": "ZenGhuntCollector/1.0"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        with urlopen(Request(self.url, headers=headers), timeout=60) as response:
            return response.read(), response.headers.get("Content-Type", "")

    @staticmethod
    def _strip(tag: str) -> str:
        return tag.rsplit("}", 1)[-1].lower()

    def _rows(self, body: bytes, content_type: str):
        fmt = self.fmt
        if fmt == "auto":
            lower = (self.url + " " + content_type).lower()
            fmt = "json" if "json" in lower or lower.endswith(".json") else ("csv" if "csv" in lower or lower.endswith((".csv", ".txt")) else "xml")

        if fmt == "json":
            payload = json.loads(body.decode("utf-8-sig"))
            rows = payload.get("products", payload.get("items", payload)) if isinstance(payload, dict) else payload
            return rows if isinstance(rows, list) else []

        if fmt == "csv":
            return list(csv.DictReader(io.StringIO(body.decode("utf-8-sig", errors="replace"))))

        root = ET.fromstring(body)
        rows = []
        for node in root.iter():
            children = list(node)
            if not children:
                continue
            tags = {self._strip(c.tag) for c in children}
            if tags & {"title", "name", "product_name"} and tags & {"price", "saleprice", "currentprice", "url", "link"}:
                rows.append({self._strip(c.tag): (c.text or "").strip() for c in children})
        return rows

    def fetch(self) -> Iterable[NormalizedOffer]:
        body, content_type = self._download()
        for item in self._rows(body, content_type):
            if not isinstance(item, dict):
                continue
            merchant = _first(item, "store", "merchant", "advertiser", "campaign_name")
            slug = str(merchant).strip().lower().replace(" ", "-") if merchant else self.slug
            name = str(merchant).strip() if merchant else self.name
            price = _first(item, "price", "sale_price", "saleprice", "current_price")
            product_id = _first(item, "store_product_id", "product_id", "id", "sku", "offer_id")
            url = _first(item, "affiliate_url", "product_url", "url", "link")
            title = _first(item, "title", "name", "product_name")
            if price in (None, "") or not product_id or not url or not title:
                continue
            try:
                yield NormalizedOffer(
                    store=slug,
                    store_product_id=str(product_id),
                    product_url=str(url),
                    title=str(title),
                    price=float(price),
                    mrp=float(_first(item, "mrp", "list_price", "old_price")) if _first(item, "mrp", "list_price", "old_price") not in (None, "") else None,
                    image_url=_first(item, "image_url", "image", "image_link"),
                    brand=_first(item, "brand", "brand_name"),
                    category=_first(item, "category", "category_name"),
                    model_number=_first(item, "model_number", "model"),
                    global_product_id=_first(item, "global_product_id", "gtin", "ean", "upc"),
                    currency=str(_first(item, "currency") or "INR"),
                    availability=str(_first(item, "availability", "in_stock") or "in stock").lower() not in {"0", "false", "out of stock", "unavailable"},
                    offer_title=_first(item, "offer_title"),
                    offer_description=_first(item, "offer_description", "description"),
                    coupon_code=_first(item, "coupon_code"),
                    discount_text=_first(item, "discount_text"),
                    valid_until=_first(item, "valid_until"),
                    metadata=item,
                )
            except (TypeError, ValueError):
                continue


def _configured_remote_feeds() -> list[RemoteProductFeedConnector]:
    connectors = []
    raw = os.getenv("ZENGHUNT_FEEDS_JSON")
    if not raw:
        return connectors
    configs = json.loads(raw)
    if not isinstance(configs, list):
        raise ValueError("ZENGHUNT_FEEDS_JSON must be a JSON array")
    for cfg in configs:
        if not isinstance(cfg, dict) or not cfg.get("url"):
            continue
        connectors.append(RemoteProductFeedConnector(
            str(cfg.get("slug") or "affiliate-feed"),
            str(cfg.get("name") or cfg.get("slug") or "Affiliate Feed"),
            str(cfg["url"]),
            str(cfg["token"]) if cfg.get("token") else None,
            str(cfg.get("format") or "auto"),
        ))
    return connectors


def configured_connectors() -> list[StoreConnector]:
    """Build connectors from GitHub Actions environment variables."""
    connectors: list[StoreConnector] = _configured_remote_feeds()

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
