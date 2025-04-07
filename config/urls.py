from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from shop.views import ProductViewSet, CategoryViewSet, CartViewSet, CommentViewSet, home, login_view, register_view, \
    logout_view, cart_view, product_detail, add_to_cart, add_to_favorites, remove_from_cart, user_profile, checkout, \
    success, product_manage_view, product_edit_view, product_delete_view, category_manage_view, category_edit_view, \
    category_delete_view
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'comments', CommentViewSet, basename='comment')

schema_view = get_schema_view(
    openapi.Info(
        title="Online Shop API",
        default_version='v1',
        description="Olcha.uz ga o'xshash online do'kon API",
    ),
    public=True,
)

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('api/', include(router.urls)),
                  path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
                  path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
                  path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
                  path('', home, name='home'),
                  path('login/', login_view, name='login'),
                  path('register/', register_view, name='register'),
                  path('logout/', logout_view, name='logout'),
                  path('cart/', cart_view, name='cart'),
                  path('profile/', user_profile, name='user_profile'),
                  path('product/<slug:slug>/', product_detail, name='product_detail'),
                  path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
                  path('remove_from_cart/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
                  path('add-to-favorites/<int:product_id>/', add_to_favorites, name='add_to_favorites'),
                  path('checkout/', checkout, name='checkout'),
                  path('success/', success, name='success'),
                  path('manage/products/', product_manage_view, name='product_manage'),
                  path('manage/products/edit/<int:pk>/', product_edit_view, name='product_edit'),
                  path('manage/products/delete/<int:pk>/', product_delete_view, name='product_delete'),
                  path('manage/categories/', category_manage_view, name='category_manage'),
                  path('manage/categories/edit/<int:pk>/', category_edit_view, name='category_edit'),
                  path('manage/categories/delete/<int:pk>/', category_delete_view, name='category_delete'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
