from django.urls import path

from . import views

urlpatterns = [
    path("config/", views.WebAppConfigView.as_view()),
    path("me/", views.MeView.as_view()),
    path("faq/", views.FAQListView.as_view()),
    path("catalog/categories/", views.CategoryListView.as_view()),
    path("catalog/products/", views.ProductListView.as_view()),
    path("catalog/products/<int:pk>/", views.ProductDetailView.as_view()),
    path("cart/", views.CartView.as_view()),
    path("cart/add/", views.CartAddView.as_view()),
    path("cart/update/<int:product_id>/", views.CartUpdateView.as_view()),
    path("cart/remove/<int:product_id>/", views.CartRemoveView.as_view()),
    path("orders/", views.OrderListView.as_view()),
    path("orders/create/", views.OrderCreateView.as_view()),
]
