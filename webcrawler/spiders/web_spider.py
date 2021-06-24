import os, scrapy
from urllib.parse import unquote

from scrapy.http.request import Request
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from ..items import PageItem, FileItem, VideoItem


class WebSpider(CrawlSpider):
    """
    Custom class that inherits from CrawlSpider with an additional login
    feature and rules for the extraction of files, videos, and html files
    """

    name = "webspider"

    # Gets sensitive information from env variables
    login_url = os.environ.get("URL")
    http_user = os.environ.get("USER")
    http_pass = os.environ.get("PASS")

    # Basic url info
    web_domain = os.environ.get("URL").split("/")[2]
    home_page = "https://" + web_domain + "/dashboard/"

    # List of url phrases that should be ignored
    ignore_list = [
        "logout",
        "next",
        "wp-login",
        "wp-admin",
        "wp-toolbar",
        "wp-content",
    ]

    # Flag that tracks login attempts, stopping script if 5 attempts are
    # made
    login_attempts = 0

    rules = (
        # Rule for extracting domain links to follow. File extensions
        # are denied to let them flow to the next rule
        Rule(
            LinkExtractor(
                allow_domains=web_domain,
                deny=ignore_list,
                deny_extensions=["pdf", "zip", "xlsx", "docx", "rtf"],
            ),
            callback="parse_page",
            follow=True,
        ),
        # Rule for extracting files with extensions (except .php scripts)
        Rule(
            LinkExtractor(
                allow=r".+\.\w{1,5}(?=$)",
                deny_extensions=["php"],
            ),
            callback="parse_file",
        ),
        # Rule for extracting iframes that are a cover for mp4 files we
        # want to extract
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
        """
        Overrides the default start_requests process to allow for an
        initial login, passing the login request to self.checklogin() to
        see if login is successful.
        """

        self.logger.info(f"MYLOG: Logging in: {self.login_url}")

        # Login information passed to website
        formdata = {
            "log": self.http_user,
            "pwd": self.http_pass,
            "wp-submit": "Log In",
            "testcookie": "1",
        }

        return [
            scrapy.FormRequest(
                self.login_url,
                formdata=formdata,
                # dont_filter=True to allow for later logins
                dont_filter=True,
                callback=self.check_login,
            )
        ]

    def check_login(self, response):
        """
        Checks if login is successful by examining response for its
        status code and the phrase 'logout', returning a request to
        start the crawl from the home page.
        """

        # Successful login returns request
        if "logout" in response.text and response.status < 400:
            self.logger.info(f"MYLOG: Login succeeded: {response.status}")
            # dont_filter=True is necessary, otherwise this would be
            # seen as a repeated request (the first being the login) and
            # the crawler will fail to start
            return Request(self.home_page, dont_filter=True)

        # Failed login increments login_attempts flag, warns the user,
        # and reattempts the login attempt. If there are 5 attempts,
        # warn the user and the script ceases
        else:
            self.login_attempts += 1

            if self.login_attempts < 5:
                self.logger.warn(
                    f"Login failed: {response.status}\n"
                    f"Login attempts: {self.attempts}\n"
                    "Reattempting login"
                )
                return self.start_requests()

            else:
                self.logger.warn("5 login attempts failed")

    def parse_page(self, response):
        """
        Parses html responses, creating a PageItem()
        containing the pages' title, extension(html) and its response
        information for download.
        """

        page = PageItem()

        page["title"] = os.path.basename(response.url.rstrip("/"))
        page["extension"] = "html"

        page["req_url"] = response.url
        page["file_urls"] = [response.url]

        return page

    def parse_file(self, response):
        """
        Parses file (non-video) responses for its
        title (from url), the original url that generated the request
        (so the file can be stored in the right directory)
        """
        file = FileItem()

        # Splits url into body and ext for title and extension extraction
        half, ext = response.url.rsplit(".", 1)
        # unquote() is used to convert %xx escapes in url to unicode
        file["title"] = unquote(half.rsplit("/", 1)[1])
        file["extension"] = ext

        file["req_url"] = str(
            response.request.headers.get("Referer", None), "utf-8"
        )
        file["file_urls"] = [response.url]

        return file

    def parse_iframe(self, response):
        """
        Parses iframe url responses for direct links to .mp4 files,
        extracting the link to highest quality video for download
        """

        raw_urls = response.css("script::text").re(
            r'"url":"(https://vod.*?\.mp4)".*?"quality":"(\d{3,4})p"'
        )

        urls, qualities = raw_urls[::2], raw_urls[1::2]
        # Zips urls and corresponding qualities into one list
        zip_urls = [(url, int(qual)) for url, qual in zip(urls, qualities)]

        # Maximum quality video url is selected based on corresponding
        # qualities
        hq_url, qual = max(zip_urls, key=lambda x: x[1])

        video = VideoItem()

        video["title"] = response.css("title::text").get()[:-30]
        video["extension"] = hq_url.rsplit(".", 1)[1]

        video["iframe_url"] = response.url
        video["quality"] = qual

        video["req_url"] = str(
            response.request.headers.get("Referer", None), "utf-8"
        )
        video["file_urls"] = [hq_url]

        return video


# Command for running webcrawler (for reference)
# scrapy crawl webspider -s JOBDIR=crawls/webspider-1
