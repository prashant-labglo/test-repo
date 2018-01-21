from rest_framework import routers
from SlideSearch.views import SearchResultViewSet, SearchQueryViewSet, SearchSessionViewSet

# Create router for SlideDB URLs.
router = routers.DefaultRouter()
router.register(r'sessions', SearchSessionViewSet)
router.register(r'queries', SearchQueryViewSet)
router.register(r'results', SearchResultViewSet)


