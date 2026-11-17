from __future__ import annotations

import argparse
import json
import os
from html.parser import HTMLParser
from urllib.request import urlopen


class CatalogParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items: list[dict[str, str | float | int]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        if tag != "article":
            return
        fields = {key: value for key, value in attrs if value is not None}
        self.items.append({
            "sku": fields["data-sku"],
            "title": fields["data-title"],
            "price": float(fields["data-price"]),
            "stock": int(fields["data-stock"]),
        })


def collect(url: str):
    parser = CatalogParser()
    with urlopen(url, timeout=15) as response:
        parser.feed(response.read().decode("utf-8"))
    if not parser.items:
        raise ValueError("商品目录没有 article 数据，检查采集地址和页面结构")
    return parser.items


def main():
    parser = argparse.ArgumentParser(description="采集项目自带的商品目录")
    parser.add_argument("--url", default="http://fixture/")
    parser.add_argument("--local", action="store_true", help="输出 JSON，不写入 Crawlab")
    args = parser.parse_args()
    items = collect(args.url)
    if args.local:
        print(json.dumps(items, ensure_ascii=False, indent=2))
        return
    if not os.environ.get("CRAWLAB_TASK_ID"):
        parser.error("请由 Crawlab 执行此任务；本地验证请添加 --local")
    from crawlab import save_items

    save_items(items)
    print(f"FLOWHARBOR_CATALOG_SAVED count={len(items)}", flush=True)


if __name__ == "__main__":
    main()
