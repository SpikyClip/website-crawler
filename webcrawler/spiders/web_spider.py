import os, scrapy
from scrapy.http.request import Request
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.utils.python import unique
from scrapy.shell import inspect_response
from ..items import PageItem, FileItem, VideoItem


class WebSpider(CrawlSpider):
    name = "webspider"
    login_url = os.environ.get("URL")
    attempts = 0

    web_domain = os.environ.get("URL").split("/")[2]
    home_page = "https://" + web_domain + "/dashboard/"

    deny_list = ["logout", "next", "wp-login", "wp-admin", "wp-toolbar"]

    rules = (
        # Rule for extracting files with extensions
        Rule(
            LinkExtractor(
                deny="wp-content",
                allow=r".+\.\w{1,5}(?=$)",
                deny_extensions=["php"],
            ),
            callback="parse_file",
        ),
        # Rule for extracting domain links to follow
        Rule(
            LinkExtractor(
                allow_domains=web_domain,
                deny=deny_list,
                deny_extensions=["pdf", "zip", "xlsx", "docx", "rtf"],
            ),
            callback="parse_page",
            follow=True,
        ),
        # Rule for extracting iframes
        Rule(
            LinkExtractor(
                allow_domains="player.vimeo.com",
                tags="iframe",
                attrs=("data-src", "src"),
            ),
            callback="parse_iframe",
        ),
    )

    def start_requests(self):
        login_url = self.login_url
        self.logger.info(f"MYLOG: Logging in: {login_url}")
        formdata = {
            "log": os.environ.get("USER"),
            "pwd": os.environ.get("PASS"),
            "wp-submit": "Log In",
            "testcookie": "1",
        }
        return [
            scrapy.FormRequest(
                login_url, formdata=formdata, callback=self.check_login
            )
        ]

    def check_login(self, response):
        if "logout" in response.text and response.status < 400:
            self.logger.info(f"MYLOG: Login succeeded: {response.status}")

            home_page_links = LinkExtractor(
                deny=self.deny_list, allow_domains=self.web_domain
            ).extract_links(response)

            for link in home_page_links:
                yield Request(link.url)

        else:
            self.attempts += 1
            if self.attempts < 5:
                self.logger.warn(
                    f"Login failed: {response.status}\n"
                    f"Attempts: {self.attempts}\n"
                    "Reattempting login"
                )
                return self.start_requests()
            else:
                self.logger.warn("5 attempts failed")

    def parse_file(self, response):
        self.logger.info(f"Parsing file: {response.url}")
        file = FileItem()

        half, ext = response.url.rsplit(".", 1)
        title = half.rsplit("/", 1)[1]

        file["req_url"] = response.url

        file["title"] = title
        file["extension"] = ext

        file["file_urls"] = [response.url]

        return file

    def parse_iframe(self, response):
        self.logger.info(f"Parsing iframe: {response.url}")
        raw_urls = response.css("script::text").re(
            r'"url":"(https://vod.*?\.mp4)".*?"quality":"(\d{3,4})p"'
        )
        zip_urls = [
            (url, int(qual)) for url, qual in zip(raw_urls[::2], raw_urls[1::2])
        ]
        hq_url, qual = max(zip_urls, key=lambda x: x[1])

        title = response.css("title::text").get()[:-30]

        video = VideoItem()
        video["req_url"] = str(
            response.request.headers.get("Referer", None), "utf-8"
        )
        video["iframe_url"] = response.url

        video["title"] = title
        video["extension"] = hq_url.rsplit(".", 1)[1]
        video["quality"] = qual

        video["file_urls"] = [hq_url]

        return video

    def parse_page(self, response):
        self.logger.info(f"Parsing page: {response.url}")
        page = PageItem()

        page["title"] = (
            response.css("title::text")
            .get()
            .replace(" \u2013 Members Area", "")
        )
        page["extension"] = "html"

        page["req_url"] = str(
            response.request.headers.get("Referer", None), "utf-8"
        )
        page["file_urls"] = [response.url]

        return page
