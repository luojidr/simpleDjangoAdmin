from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, connections


class ESearch(object):
    """
    https://github.com/elastic/elasticsearch-dsl-py
    https://elasticsearch-dsl.readthedocs.io/en/latest/
    """

    def __init__(self):

        self._s = Search()

    @staticmethod
    def setup():
        connections.create_connection(host=["192.168.190.128:9200"], timeout=20)


if __name__ == "__main__":
    client = Elasticsearch('192.168.190.128:9200')
    indexs = client.indices.get('*')
    print(indexs)


