""" This module handles the middlewares.
    Each class represents a middleware that must be installed
    in settings.py. Middlewares alters with the Request and the
    Response based on what we need.
"""

from scrapy import signals, Request
from scrapy.http import Response
import pymongo
from scrapy.exceptions import IgnoreRequest
import logging
from user_agent import generate_user_agent

# Get the logging instance initiated by Scrapy framework
logger = logging.getLogger(__name__)


class ShowUserAgentMiddleware:
    """ This middleware prints and logs the current user-agent.
        It has been created for testing purposes and is not installed
        in settings.py. In order to use it we have to install it.
    """
    def process_request(self, request, spider) -> None:
        logger.info(f"User Agent: {request.headers['User-Agent']}")
        print(f"User Agent: {request.headers['User-Agent']}")


class ShuffleUserAgentMiddleware:
    """ This module generate random user agents using the user_agent
        library and add it to each request.
    """
    @classmethod
    def from_crawler(cls, crawler):
        """ Used for signal spider logs.
            Whenever a spider is opened or closed, it will be logged.
        """
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    def process_request(self, request, spider) -> None:
        logger.info(f"Changing User Agent for {request.url}")

        # generate user-agent for mac, linux and windows browsers
        u_agent = generate_user_agent(os=('mac', 'linux', 'win'))
        request.headers['User-Agent'] = u_agent

    def spider_opened(self, spider) -> None:
        spider.logger.info('Spider %s opened from %s.%s'
                           % (spider.name, __name__, __class__.__name__))

    def spider_closed(self, spider) -> None:
        spider.logger.info('Spider %s closed from %s.%s'
                           % (spider.name, __name__, __class__.__name__))


class NewsCrawlerDownloaderMiddleware:
    """ This module is used check the request right before is begins,
        and the response right after it gets.
    """
    # MongoDB collection name
    collection_name = 'articles'

    def __init__(self, mongo_uri, mongo_db) -> None:
        """ Assigns the mongo uri and db name after getting them
           from the classmethod"""
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        """ Same as in each middleware class, but this time we
            create the instance with mongo_uri and mongo_db
        """
        s = cls(
                mongo_uri=crawler.settings.get('MONGO_URI'),
                mongo_db=crawler.settings.get('MONGO_DATABASE')
            )
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s

    def process_request(self, request, spider) -> None:
        """ Checks if the request's URL has been processed before,
            by searching for its existence in the MongoDB collection.
        """
        url = request.url
        col = self.db[self.collection_name]
        cursor = col.find_one({"article_url": url})
        if cursor:
            # if the url was found in the db, ignorr the request
            # and log the event
            logger.info(f'{url} is already processed. Ignoring request!')
            raise IgnoreRequest
        return None

    def process_response(self, request, response, spider) -> Response:
        """ If the response status is anything other than 200,
            the request is ignored, the event is logged, and the url is
            appended to a error_urls.txt file.
        """
        # Excluding https://www.bbc.com/robots.txt since it needs different
        # implementation and it needs to be processed no matter what
        if not request.url.endswith("robots.txt"):
            # get the response status from the headers
            response_status = \
                    response.headers['X-Bbc-Origin-Response-Status'] \
                    .decode('utf-8')

            url = request.url
            # check the status and act accordingly
            if response_status == '200':
                logger.info(f"GET {url} 200")
                return response
            else:
                logger.warning(f"GET {url} {response_status}."
                               + "Ignoring request!")

                with open('error_urls.txt', 'a') as f:
                    f.write(f'{url}\n')

                logger.warning(f"Saved to error_urls.txt.")
                raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider) -> None:
        """ We can use this function to handle exceptions.
            We just need exceptions to occur to go through them.
            Needs more trials and errors.
        """
        pass

    def spider_opened(self, spider) -> None:
        """ When the spider is opened, a MongoDB connector instance is
            created and the connection is opened.
        """
        spider.logger.info('Spider %s opened from %s.%s'
                           % (spider.name, __name__, __class__.__name__))
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def spider_closed(self, spider) -> None:
        """ Closes the DB connection when the spider is closed.
        """
        spider.logger.info('Spider %s closed from %s.%s'
                           % (spider.name, __name__, __class__.__name__))
        self.client.close()
