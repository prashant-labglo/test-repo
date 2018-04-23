from rest_framework import routers
from Search.views import (
    SearchIndexViewSet, SearchResultViewSet, SearchResultRatingViewSet, SearchQueryTemplateViewSet,
    SearchQueryViewSet
)

# Create router for SlideDB URLs.
router = routers.DefaultRouter()
router.register(r'indices', SearchIndexViewSet)
router.register(r'templates', SearchQueryTemplateViewSet)
router.register(r'queries', SearchQueryViewSet)
router.register(r'results', SearchResultViewSet)
router.register(r'ratings', SearchResultRatingViewSet)
