import scrapy
import time

class FixPriceSpider(scrapy.Spider):
    name = 'fix_price_spider'
    # start_urls = [
    #     'https://fix-price.com/catalog/spets-tsena-po-karte/igrushki-i-kantstovary-spets-tsena',
    #     'https://fix-price.com/catalog/krasota-i-zdorove/dlya-tela',
    #     'https://fix-price.com/catalog/kosmetika-i-gigiena/gigienicheskie-sredstva'
    # ]

    start_urls = [
        'https://fix-price.com/catalog/kosmetika-i-gigiena/ukhod-za-telom'
    ]

    custom_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Accept-Language': 'ru-RU,ru;q=0.9',
        'Region': 'Екатеринбург'
    }

    def parse(self, response):
        # Cсылки на страницы товаров
        product_links = response.css('a.title::attr(href)').getall()
        for link in product_links:
            yield response.follow('https://fix-price.com' + link, self.parse_product)

        # Пагинация
        next_page = response.css('a.button.next::attr(href)').get()
        if next_page:
            yield response.follow('https://fix-price.com' + next_page, self.parse)

    def parse_product(self, response):
        # Парсинг информации о каждом товаре
        yield {
            "timestamp": int(time.time()),
            "RPC": response.css('span.value::text').get(),
            "url": response.url,
            "title": response.css('h1.title::text').get(),
            "marketing_tags": response.css('div.sticker.big.isSpecialPrice::text').getall(),
            "brand": response.css('h1.title::text').get().split(", ")[1],
            "section": response.css('span.text::text').getall()[2],
            "price_data": {
                "current": response.css('div.special-price::text').get(), 
                "original": response.css('div.regular-price::text').get(), 
                "sale_tag": 'Скидка: x',
            },
            "stock": {
                "in_stock": 'Нет в наличии' not in response.text,
                "count": 0 
            },
            "assets": {
                "main_image": response.css('div.main-image img::attr(src)').get(),
                "set_images": response.css('div.image-gallery img::attr(src)').getall(),
                "view360": [],
                "video": []
            },
            "metadata": self.parse_metadata(response),
            "variants": len(response.css('div.variants div::text').getall()),
        }

    def parse_title(self, response):
        title = response.css('h1.product-title::text').get()
        # Если есть цвет или объем, добавляем их в название
        additional_info = response.css('div.product-info span::text').getall()
        return f"{title}, {' '.join(additional_info)}"

    def get_price(self, response):
        return 2

    def get_original_price(self, response):
        return 10

    def get_sale_tag(self, response):
        discount_percentage = response.css('span.discount::text').re_first(r'\d+')
        if discount_percentage:
            return f"Скидка {discount_percentage}%"
        return ''

    def parse_metadata(self, response):
        # Извлечения характеристик товара
        metadata = {}
        characteristics = response.css('div.characteristics table tr')
        for char in characteristics:
            key = char.css('th::text').get().strip()
            value = char.css('td::text').get().strip()
            metadata[key] = value
        return 1