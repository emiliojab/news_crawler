""" This is a unittester module, that tests the result of a fake
    sample.html file whic is a clone to an existing bbc news article.
    It tests the most important parts of the MongoDB insertion mechanism,
    which are the data types of the fields used for querying with the API.
"""
import unittest
from news_crawler.spiders.articles import process_response
from scrapy.selector import Selector


class TestAdd(unittest.TestCase):

    def test_parse(self) -> None:
        """ This function gets the sample.html file, assign it to
            a scrapy selector in order to implement the scraping
            methods without starting a reactor and spiders.
        """
        file = open('sample.html', 'r')
        text = file.read()
        fake_response = Selector(text=text)
        file.close()

        # use the process_response function that cleanse and structure
        # the page
        result = process_response(fake_response)

        # asserting the datatypes
        self.assertIsInstance(result['created_at']['ISO_datetime'], str)
        self.assertIsInstance(result['created_at']['year'], int)
        self.assertIsInstance(result['created_at']['month'], int)
        self.assertIsInstance(result['created_at']['day'], int)
        self.assertIsInstance(result['created_at']['time'], str)

        self.assertIsInstance(result['tags'], list)

        self.assertIsInstance(result['author(s)'], list)


if __name__ == '__main__':
    unittest.main()
