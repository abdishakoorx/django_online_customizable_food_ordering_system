"""
URL configuration for customdishes project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  #path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  #path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, #path
    2. Add a URL to urlpatterns:  #path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from customize import views
from django.conf import settings
from django.conf.urls.static import static
from customize.views import CustomerSignUpView, RestaurantSignUpView, ordersave


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('contact/', views.contact, name='contact'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('signup_customer/', CustomerSignUpView.as_view(), name='signup_customer'),
    path('signup_restaurant/', RestaurantSignUpView.as_view(), name='signup_restaurant'),
    path('login/', views.user_login, name='login'),
    path('restaurant_list/', views.restaurant_list, name='restaurant_list'),
    path('restaurant/orders/', views.restaurant_orders, name='restaurant_orders'),
    path('order/<int:restaurant_id>/', ordersave.as_view(), name='order'),
    path('restaurant/orders/update_status/', views.order_statuss, name='order_statuss'),
    path('order/history/', views.order_history, name='order_history'),
    path('submit_item_review/<int:item_id>/', views.submit_item_review, name='item_review'),
    path('item/reviews/<int:item_id>/', views.item_reviews, name='item_reviews'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
