import redis
from bson import ObjectId
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from models.articles import Article, ArticleMatch
from scipy.spatial import distance
from config import REDIS_HOST
from app import db
redisconn = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0)

def calculate_euclidaen_distance(new_article, matched_article):
    "Calculate the euclidaen distance between matched url and recored url"
    new_article_kws = {i['name']: i['score'] for i in new_article.keywords if i['score'] >= 50}
    matched_article_kws = {i['name']: i['score'] for i in matched_article.keywords if i['score'] >= 50}
    all_keywords = [i for i in [i["name"] for i in new_article.keywords if i["score"] >= 50]] + \
                   [i for i in [i["name"] for i in matched_article.keywords if i["score"] >= 50]]

    a = tuple([new_article_kws.get(i, 0) for i in all_keywords])
    b = tuple([matched_article_kws.get(i, 0) for i in all_keywords])
    try:
        dst = distance.euclidean(a,b)
        return dst
    except:
        print a,b


def calculate_article(article):
    words = [i['name'] for i in article.keywords if i.get("score", 0) > 45]
    matching_urls = Article.q.filter({"keywords.name": {"$in": words},
                                      "_id": {"$ne": article._id}}).all()
    count = 0
    bulk = db.test.initialize_ordered_bulk_op()
    for i in matching_urls:
        print i.id
        if count > 200:
            bulk.execute()
            bulk = db.test.initialize_ordered_bulk_op()
            count = 0
        dst = calculate_euclidaen_distance(article, i)
        if not ArticleMatch.q.filter({"match1": article.id, "match2": i.id}).first():
            bulk.insert(
                {"match1": article.id,
                 "match2": i.id,
                 "dst": dst}
            );
            bulk.insert(
                {"match2": article.id,
                 "match1": i.id,
                 "dst": dst}
            );
            print 'inserted->', i.id
            count += 1


def calculate_all():
    articles = Article.q.chunked_all()
    for article in articles:
        if not article.keywords:
            continue
        calculate_article(article)


def calculater():
    while True:
        id = redisconn.blpop('queue')
        article = Article.q.fetch_by_id(id[1])
        if article:
            try:
                calculate_article(article)
            except Exception as e:
                print(e)


if __name__ == "__main__":
    calculate_all()