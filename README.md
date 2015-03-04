# Srishti2015
Design and implementation of a full-text search engine for the given news dataset with news headlines and newsURL.
It allows people to search from a large set of news articles and get results ranked according to relevance to search query.
A very basic implementation of news search engine is done by making use of concepts involved in collective intelligence algorithms.

The system is designed to perform the following operations. 
● News articles crawling from URL. 
● Data Indexing 
● Searching relevant results
● Ranking

Crawling : The general method to crawl documents is to start with a small set of documents 
and follow links to others. But in the given scenario, we have provided with full­featured news 
dataset to start with, so no need of crawling other linked articles in breadth first manner. So here in this context crawling  means extracting the news content of given news entry using URL given. As some URLs are 
missing domain names, they are also completed by making use of source field in the given dataset. The crawler uses the Beautiful Soup AP for extracting news articles contents. 
 
Indexing: After the collection of news articles from URL,they need to be indexed. This usually involves 
creating a big table of the articles and the locations of all different words. 
 
Searching: Retrieving every news article with a given set of words is fairly straightforward 
once we have term frequency vectors for each news article indexed in database, but the real magic is how the results are sorted. This involves proper ranking of the results on the basis of how relevant they are. 
 
Ranking : Results are ranked using normalized score of different metrics such as word frequency,word distance. 

Here, we have not used PageRank for ranking as news articles are not linked with each other or other web-pages. If we can manage to extract the links while crawling content from URLs, then pagerank can also be applied.

Searchengine.py contains both crawler and searcher python classes for crawling,indexing and searching,ranking tasks respectively. These classes functionality can be tested through web-based interactive computational environment Ipython Notebook using files Searcher.ipynb and Crawler.ipynb files.


