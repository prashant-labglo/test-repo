from rest_framework import routers
from Search.views import (
    SearchIndexViewSet, SearchResultViewSet, SearchResultRatingViewSet, SearchQueryInvocationViewSet,
    SearchQueryViewSet
)

# Create router for SlideDB URLs.
router = routers.DefaultRouter()
router.register(r'indices', SearchIndexViewSet)
router.register(r'queries', SearchQueryInvocationViewSet)
router.register(r'results', SearchResultViewSet)
router.register(r'ratings', SearchResultRatingViewSet)
router.register(r'searchqueries', SearchQueryViewSet)
