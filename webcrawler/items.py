# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class PageItem(scrapy.Item):
    req_url = scrapy.Field()

    title = scrapy.Field()
    extension = scrapy.Field()

    file_urls = scrapy.Field()
    files = scrapy.Field()


class FileItem(scrapy.Item):
    req_url = scrapy.Field()

    title = scrapy.Field()
    extension = scrapy.Field()

    file_urls = scrapy.Field()
    files = scrapy.Field()


class VideoItem(scrapy.Item):
    req_url = scrapy.Field()
    iframe_url = scrapy.Field()

    title = scrapy.Field()
    extension = scrapy.Field()
    quality = scrapy.Field()

    file_urls = scrapy.Field()
    files = scrapy.Field()
