from rest_framework import routers
from Search.views import SearchIndexViewSet, SearchResultViewSet, SearchQueryViewSet, SearchSessionViewSet
#from Search.serchIndexView import SearchSessionViewSet

# Create router for SlideDB URLs.
router = routers.DefaultRouter()
router.register(r'index', SearchIndexViewSet)
router.register(r'sessions', SearchSessionViewSet)
router.register(r'queries', SearchQueryViewSet)
router.register(r'results', SearchResultViewSet)


