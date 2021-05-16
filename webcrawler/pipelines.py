# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

from urllib.parse import urlparse
from scrapy.pipelines.files import FilesPipeline


class MyFilesPipeline(FilesPipeline):
    def file_path(self, request, response=None, info=None, *, item=None):

        url = urlparse(item["req_url"]).path
        title = item["title"]
        ext = "." + item["extension"]

        path = url + title + ext

        return path
