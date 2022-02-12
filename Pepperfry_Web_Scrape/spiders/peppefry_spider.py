import json
import scrapy
import os
import requests


class PepperfrySpider(scrapy.Spider):

    name = "pepperfry_spider"
    BASE_DIR = "./Pepperfry Data/"
    MAX_CNT = 10

    def start_requests(self):

        BASE_URL = 'https://www.pepperfry.com/site_product/search?q='

        items = ["two seater sofa", "bench", "book cases", "coffee table", "dining set",
                 "queen beds", "arm chairs", "chest drawers", "garden seating", "bean bags", "king beds"]

        urls = []
        dir_names = []

        summary = {}

        for item in items:
            qs = "+".join(item.split())
            dir_name = item.capitalize()

            urls.append(BASE_URL + qs)
            dir_names.append(dir_name)

            dir_path = self.BASE_DIR + dir_name

            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

        for url, dir_name in zip(urls, dir_names):

            d = {
                "dir_name": dir_name
            }

            resp = scrapy.Request(
                url, callback=self.parseItemsPage, dont_filter=True)

            resp.meta["dir_name"] = dir_name

            summary[dir_name] = yield resp

        yield summary

    def parseItemsPage(self, response, **meta):

        productUrls = response.css("div.clipCard__hd a::attr(href)").getall()

        productUrls = list(filter(lambda x: not x.startswith(
            "javascript"), productUrls))[:self.MAX_CNT]

        self.log(productUrls)

        for url in productUrls:

            resp = scrapy.Request(
                url, callback=self.parseItemDetails, dont_filter=True)
            resp.meta["dir_name"] = response.meta['dir_name']
            yield resp

    def parseItemDetails(self, response, **meta):

        img_urls = response.css(
            "li.vipImage__thumb-each a::attr(data-img)").getall()

        item_name = response.css("h1.vip-pro-hd::text").get()
        brand_name = response.css(
            "a.vip-pro-by-brand-link::text").get().split()[-1]
        effective_price = response.css(
            "span.vip-eff-price-amt::text").get().split()[-1]
        discount = response.css(
            "span.vip-eff-price-disc::text").get()[1:-1].split()[0]
        mrp = response.css("span.vip-save-price-mrp::attr(data-price)").get()

        metadata = {
            "item_name": item_name,
            "brand_name": brand_name,
            "effective_price": effective_price,
            "discount": discount,
            "mrp": mrp,
        }

        category_name = response.meta["dir_name"]

        item_dir_path = os.path.join(self.BASE_DIR, category_name, item_name)

        if not os.path.exists(item_dir_path):
            os.makedirs(item_dir_path)

        with open(os.path.join(item_dir_path, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=4)

        for i, url in enumerate(img_urls, 1):
            res = requests.get(url)

            with open(os.path.join(item_dir_path, f"image_{i}.jpg"), "wb") as f:
                f.write(res.content)

        yield metadata
