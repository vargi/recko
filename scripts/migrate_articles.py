import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from models.articles import Article, ArticleLike, ArticleIndexed


for article in Article.q.all():
    article_indexed = ArticleIndexed(**{"url": article.url})
    article_indexed.save()
    print article.id