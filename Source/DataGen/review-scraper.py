import html
import json
import scrapy
import subprocess
import time
from urllib.parse import urlparse

class ReviewScraper(scrapy.Spider):
    name = 'RedditECigReviews'
    start_urls = [
        'https://www.reddit.com/r/electronic_cigarette/wiki/anthony_vapes_reviews'
    ]

    def __init__(self):
        self.download_delay = 0.1 # 100 ms of delay per page

    def parse(self, response):
        for review_url in self.get_reviews_urls(response):
            req = response.follow(review_url['link'], self.parse_review_page)
            req.meta['info'] = review_url
            yield req

    def get_reviews_urls(self, response):
        paras = response.css('.md.wiki>p')
        start_selection = False
        for para in paras:
            text = para.css('::text').extract_first()
            if text == 'Review Links':
                start_selection = True
            elif start_selection:
                link = urlparse(para.css("a::attr(href)").extract_first())
                link = link._replace(query=None).geturl()
                if link[-1] == '/':
                    link = link[:-1]
                yield {
                    'product': text,
                    'link': f'{link}.json'
                }

    def parse_review_page(self, response):
        json_response = json.loads(response.text)
        title = json_response[0]['data']['children'][0]['data']['title']
        date = time.strftime('%a, %d %b %Y %H:%M:%S %Z', time.localtime(int(json_response[0]['data']['children'][0]['data']['created_utc'])))
        description_html = html.unescape(
            json_response[0]['data']['children'][0]['data']['selftext_html']
        )
        description = scrapy.http.HtmlResponse(url='description', body=description_html.encode('utf8'))
        info = response.meta['info']
        return {
            'product': info['product'],
            'review_url': info['link'],
            'title': title,
            'createdAt': date,
            'description': self.parse_description(description)
        }

    def parse_description(self, description):
        specs = description.xpath(
            "//h2[text()[contains(translate(., 'MANUFCTRE', 'manufctre'), 'manufacturer')]]/following-sibling::ul[1]/li/text()").getall()
        pros = description.xpath("//h2[text()[contains(translate(., 'PROS', 'pros'), 'pros')]]/following-sibling::ul[1]/li/text()").getall()
        cons = description.xpath("//h2[text()[contains(translate(., 'CONS', 'cons'), 'cons')]]/following-sibling::ul[1]/li/text()").getall()
        return {
            'specs': specs,
            'pros': pros,
            'cons': cons
        }

if __name__ == '__main__':
    scrapy_command = f'scrapy runspider {__file__} -o ../../data/reviews.jl'
    process = subprocess.Popen(scrapy_command, shell=True)
    process.wait()