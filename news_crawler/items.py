import scrapy


class ArticleItem(scrapy.Item):
    """ Initiate fields for an article item
    """
    article_url = scrapy.Field()
    created_at = scrapy.Field()
    headline = scrapy.Field()
    author = scrapy.Field()
    text = scrapy.Field()
    images = scrapy.Field()
    tags = scrapy.Field()
