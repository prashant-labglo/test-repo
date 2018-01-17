from rest_framework import routers
from SlideDB.views import ConceptViewSet, SubConceptViewSet, ConstructViewSet, SlideViewSet

# Create router for SlideDB URLs.
router = routers.DefaultRouter()
router.register(r'concepts', ConceptViewSet)
router.register(r'subconcepts', SubConceptViewSet)
router.register(r'constructs', ConstructViewSet)
router.register(r'slides', SlideViewSet)

