import os, scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.utils.python import unique
from scrapy.shell import inspect_response
from ..items import PageItem, FileItem, VideoItem


class WebSpider(CrawlSpider):
    name = "web_spider"
    start_urls = [os.environ.get("URL")]
    attempts = 0

    web_domain = os.environ.get("URL").split("/")[2]
    home_page = "https://" + web_domain + "/dashboard/"

    deny_list = ["logout", "next", "wp-login", "wp-admin"]

    rules = (
        # Rule for extracting domain links to follow
        Rule(
            LinkExtractor(
                deny=deny_list, allow_domains=web_domain, unique=True
            ),
            callback="parse_page",
            follow=True,
        ),
        # Rule for extracting files with extensions
        Rule(
            LinkExtractor(allow=r".+\.\w{1,5}(?=$)", deny_extensions=[]),
            callback="parse_file",
        ),
        # Rule for extracting iframes
        Rule(
            LinkExtractor(
                restrict_text="vimeo",
                tags="iframe",
                attrs=("data-src", "src"),
            ),
            callback="parse_iframe",
        ),
    )

    def parse_start_url(self, response):
        formdata = {
            "log": os.environ.get("USER"),
            "pwd": os.environ.get("PASS"),
            "wp-submit": "Log In",
            "testcookie": "1",
        }
        return scrapy.FormRequest.from_response(
            response, formdata=formdata, callback=self.check_login
        )

    def check_login(self, response):
        inspect_response(response, self)
        if "logout" in response.text and response.status < 400:
            self.log(f"Login succeeded: {response.status}")
            return scrapy.Request(self.home_page)

        else:
            self.attempts += 1
            if self.attempts < 5:
                self.log(
                    f"Login failed: {response.status}\n"
                    f"Attempts: {self.attempts}\n"
                    "Reattempting login"
                )
                self.parse_start_url(self.start_urls[0])
            else:
                self.log("5 attempts failed")

    def parse_file(self, response):
        file = FileItem()

        half, ext = response.url.rsplit(".", 1)
        title = half.rsplit("/", 1)[1]

        file["req_url"] = response.request.header.get("Referer")
        file["file_url"] = response.url
        file["title"] = title
        file["body"] = response.body
        file["extension"] = "." + ext

        return file

    def parse_iframe(self, response):
        video = VideoItem()

        raw_urls = response.css("script::text").re(
            r'"url":"(https://vod.*?\.mp4)".*?"quality":"(\d{3,4})p"'
        )
        zip_urls = [
            (url, int(qual)) for url, qual in zip(raw_urls[::2], raw_urls[1::2])
        ]
        hq_url, qual = max(zip_urls, key=lambda x: x[1])

        title = response.css("title::text").get()[:-30]

        video["req_url"] = response.request.header.get("Referer")
        video["iframe_url"] = response.url
        video["vid_url"] = hq_url
        video["title"] = title
        video["quality"] = qual
        video["extension"] = "." + hq_url.rsplit(".", 1)[1]

        return video

    def parse_page(self, response):
        page = PageItem()
        page["page_url"] = response.url
        page["title"] = (
            response.css("title::text")
            .get()
            .replace(" \u2013 Members Area", "")
        )
        page["body"] = response.body

        return page
