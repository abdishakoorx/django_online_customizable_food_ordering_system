from django.contrib import admin

# Register your models here.

from .models import  User, Customer, Restaurant, Order, Menu, MenuItem, Category, Review, UserActivity


admin.site.register(User)
admin.site.register(Customer)
admin.site.register(Restaurant) 
admin.site.register(Order)
admin.site.register(MenuItem)
admin.site.register(Menu)
admin.site.register(Category)
admin.site.register(Review)
admin.site.register(UserActivity)