from rest_framework import routers
from SlideDB.views import ConceptViewSet, SlideTypeViewSet, SlideViewSet

# Create router for SlideDB URLs.
router = routers.DefaultRouter()
router.register(r'concepts', ConceptViewSet)
router.register(r'slidetypes', SlideTypeViewSet)
router.register(r'slides', SlideViewSet)

