"""
Shop URL Configuration
"""

from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='products'),
    path('category/<slug:slug>/', views.CategoryProductsView.as_view(), name='category'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('cart/', views.CartView.as_view(), name='cart'),
    path('cart/add/<int:product_id>/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.UpdateCartItemView.as_view(), name='update_cart_item'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('checkout/success/', views.CheckoutSuccessView.as_view(), name='checkout_success'),
    path('orders/', views.OrderListView.as_view(), name='orders'),
    path('order/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('apply-coupon/', views.ApplyCouponView.as_view(), name='apply_coupon'),
]
