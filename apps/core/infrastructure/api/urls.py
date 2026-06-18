from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from apps.core.infrastructure.api.views import (
    AreaViewSet,
    ClientViewSet,
    SpecialtyViewSet,
    TechnologyViewSet,
    UserProfileViewSet,
    ProjectViewSet,
    SprintViewSet,
    TaskViewSet,
    TagViewSet,
    CommentViewSet,
)

router = DefaultRouter()
router.register(r'areas', AreaViewSet, basename='api-area')
router.register(r'clients', ClientViewSet, basename='api-client')
router.register(r'specialties', SpecialtyViewSet, basename='api-specialty')
router.register(r'technologies', TechnologyViewSet, basename='api-technology')
router.register(r'profiles', UserProfileViewSet, basename='api-profile')
router.register(r'projects', ProjectViewSet, basename='api-project')
router.register(r'sprints', SprintViewSet, basename='api-sprint')
router.register(r'tasks', TaskViewSet, basename='api-task')
router.register(r'tags', TagViewSet, basename='api-tag')
router.register(r'comments', CommentViewSet, basename='api-comment')

urlpatterns = [
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('', include(router.urls)),
]
