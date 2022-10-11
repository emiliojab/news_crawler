from dotenv import load_dotenv
import os
import urllib

load_dotenv()

BOT_NAME = 'news_crawler'

SPIDER_MODULES = ['news_crawler.spiders']
NEWSPIDER_MODULE = 'news_crawler.spiders'

# MongoDB Configuration
user = os.getenv("MONGODB_USER")
password = os.getenv("MONGODB_PASSWORD")
pwd = urllib.parse.quote_plus(password)
host = os.getenv("MONGODB_HOST")
port = os.getenv("MONGODB_PORT")
MONGO_URI = f'mongodb://{user}:{pwd}@{host}:{port}/?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&directConnection=true&ssl=false'
MONGO_DATABASE = os.getenv("MONGODB_DATABASE")

# Logger custom settings
LOG_FILE = 'crawler.log'
LOG_LEVEL = 'INFO'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure a delay for requests for the same website (default: 0)
DOWNLOAD_DELAY = 3

# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    'news_crawler.middlewares.NewsCrawlerDownloaderMiddleware': 545,
    'news_crawler.middlewares.ShuffleUserAgentMiddleware': 550,
    # 'news_crawler.middlewares.ShowUserAgentMiddleware': 555,
}

# Enable or disable spider middlewares
SPIDER_MIDDLEWARES = {
    'scrapy.spidermiddlewares.offsite.OffsiteMiddleware': 100,
}

# Configure item pipelines
ITEM_PIPELINES = {
  "news_crawler.pipelines.MongoDBPipeline": 600
}
