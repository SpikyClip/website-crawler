# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

from urllib.parse import urlparse
from scrapy.pipelines.files import FilesPipeline


class MyFilesPipeline(FilesPipeline):
    """
    Custom file pipeline class that overrides default file naming system
    (checksum names only) to implement a custom system that is organised
    in a similar structure to the website.
    """

    def file_path(self, request, response=None, info=None, *, item=None):
        """
        saves files in a url + title + ext format based on Item
        information
        """

        url = urlparse(item["req_url"]).path
        title = item["title"]
        ext = "." + item["extension"]

        path = url + title + ext

        return path
