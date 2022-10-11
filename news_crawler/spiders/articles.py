""" This module gets the URLs from urls.txt, loops through them
    and initiates the requests to be processed by the middlewares
    and pipelines.
"""
import scrapy
from dateutil.parser import isoparse
from news_crawler.items import ArticleItem


def process_response(response) -> list:
    """ This function gets the response which is the html of the url page
        use scrapy's selectors to get the desired Xpath and css of each element
        to get the details of the article.
    """
    img_counter = 0
    result = {}
    images = []
    text = ''
    tags = []
    result['article_url'] = \
        response.xpath('//meta[@property="og:url"]/@content').get()

    article = response.css('article')

    # The date is stored as ISO format (string), and as year, month, and
    # time seperately, to be used for filtering with time while querying.
    created_at = article.css('time').xpath('@datetime').get(default='')
    result['created_at'] = {
        "ISO_datetime": created_at,
        "year": isoparse(created_at).year if created_at else created_at,
        "month": isoparse(created_at).month if created_at else created_at,
        "day": isoparse(created_at).day if created_at else created_at,
        "time": str(isoparse(created_at).time()) if created_at else created_at,
        }

    # the name of the article
    result['headline'] = article.xpath('//*[@id="main-heading"]/text()') \
                                .get(default='not-found')
    # in some article there are one or many authors, in others the authors are
    # not specified, so we store an empty list for the latter case.
    result['author(s)'] = []
    for item in article.xpath('./div'):
        div = item.xpath('@data-component').get()

        # Below are the tags condition based on the html structure
        # after going through the html script
        match div:
            # the author(s) name(s)
            case 'byline-block':
                author = item.css('div::text') \
                            .getall()[0] \
                            .replace('By ', '') \
                            .strip()
                result['author(s)'].append(author.split(' and '))

            # the text of the article
            case 'text-block':
                tmp = item.css('p::text, a::text, b::text').getall()
                text += \
                    f"{tmp[0] if tmp else ''}\n"

            # some article include a list of points in the text, and they are
            # included in different tags
            case 'unordered-list-block':
                for li in item.css('ul').css('li'):
                    tmp = li.css('li::text, p::text, a::text, b::text') \
                            .getall()
                    text += f"- {' '.join(tmp)}\n"

            # the images' links and description
            # when there's an image, a image identifier is created
            # such as Image-0 for reference because the images are stored as
            # links and in the text their reference
            case 'image-block':
                img = item.css('img')
                img_alt = img.xpath('@alt').get()
                if img_alt != 'line':
                    text += f"\t@Image-{img_counter}\n"
                    images.append({
                        'image_ref': f'Image-{img_counter}',
                        'source': img.xpath('@src').get(),
                        'description': img_alt
                    })
                    img_counter += 1

            # the subheadlines (or subtitles)
            case 'subheadline-block':
                text += f"---{item.css('span::text').getall()[0]}---\n"

            case _:
                pass

    # the tags of the article
    tags_path = article.xpath("//section[contains(@data-component, \
                            'tag-list')]")
    for item in tags_path.css('ul').xpath('./li'):
        tags.append(item.css('a::text').get())

    result['text'] = text
    result['images'] = images
    result['tags'] = tags

    return result


class ArticleSpider(scrapy.Spider):
    # the name of the spider
    name = 'news_crawler'

    # allowed_domains should prevent any other domain of being processed
    # but for some reasons it is not, and I did not find any
    # solution YET other than it is a bug
    allowed_domains = ['bbc.com']

    def start_requests(self) -> scrapy.Request:
        """ Gets the urls from the text file, puts them
            in a list, and yields each request accordingly
        """
        url_file = open('urls.txt')
        start_urls = url_file.read().splitlines()
        url_file.close()
        for url in start_urls:
            self.logger.info(f'Getting {url}')
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response) -> ArticleItem:
        """ Calls the process_response function above, gets the result
            and create and ArticleItem object from items.py
        """
        self.logger.info(f'Processing article from {response.url}')

        result = process_response(response)

        item = ArticleItem()
        item['article_url'] = result['article_url']
        item['created_at'] = result['created_at']
        item['headline'] = result['headline']
        item['author'] = result['author(s)']
        item['text'] = result['text']
        item['images'] = result['images']
        item['tags'] = result['tags']

        yield item
