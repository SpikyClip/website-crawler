# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class PageItem(scrapy.Item):
    """
    Item template for html pages
    """

    title = scrapy.Field()
    extension = scrapy.Field()

    # the url of the page that contained file_urls
    req_url = scrapy.Field()
    # The urls from which files should be downloaded from
    file_urls = scrapy.Field()

    # Field where scrapy keeps track of the file download status
    files = scrapy.Field()


class FileItem(scrapy.Item):
    """
    Item template for files (non-video)
    """

    title = scrapy.Field()
    extension = scrapy.Field()

    # the url of the page that contained file_urls
    req_url = scrapy.Field()
    # The urls from which files should be downloaded from
    file_urls = scrapy.Field()

    # Field where scrapy keeps track of the file download status
    files = scrapy.Field()


class VideoItem(scrapy.Item):
    """
    Item template for video files
    """

    title = scrapy.Field()
    extension = scrapy.Field()

    iframe_url = scrapy.Field()
    quality = scrapy.Field()

    # the url of the page that contained file_urls
    req_url = scrapy.Field()
    # The urls from which files should be downloaded from
    file_urls = scrapy.Field()

    # Field where scrapy keeps track of the file download status
    files = scrapy.Field()
