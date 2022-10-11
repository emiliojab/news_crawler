""" This module implements a pipeline to store data after.
    Same as middleware, it has to be installed in settings.py,
    and gets triggered after the middlewares finish their work.
"""
import pymongo
import scrapy
from itemadapter import ItemAdapter
import logging

# get the logging instance created by Scrapy
logger = logging.getLogger(__name__)


class MongoDBPipeline(object):
    """ This class gets the data from articles.py after the
        response has been processed (cleansed and structured),
        and store them in MongoDB.
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
        """ Create the instance with mongo_uri and mongo_db
        """
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE')
        )

    def open_spider(self, spider) -> None:
        """ When the spider is opened, a MongoDB connector instance is
            created and the connection is opened.
        """
        logger.info('Connecting to MongoDB.')
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider) -> None:
        """ Close the spide and the DB connection
        """
        logger.info('Closing MongoDB connection.')
        self.client.close()

    def process_item(self, item, spider) -> scrapy.Item:
        """ Gets the structure of the crawled article from items.py, and
            inserting the item as dict into MongoDB
        """
        logger.info(f"Inserting article from {item['article_url']}"
                    + " into MongoDB.")
        self.db[self.collection_name].insert_one(ItemAdapter(item).asdict())
        return item
