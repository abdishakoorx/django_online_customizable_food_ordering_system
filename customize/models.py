from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
from datetime import time
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class User(AbstractUser):
    is_customer = models.BooleanField(default=False)
    is_restaurant = models.BooleanField(default=False)

    class Meta:
        swappable = 'AUTH_USER_MODEL'

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    username = models.CharField(max_length=100)
    contact = models.CharField(max_length=100)
    groups = models.ManyToManyField(Group, related_name='customer_set', blank=True)
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customer_set',
        blank=True,
    )

    def __str__(self):
        return self.username

class Restaurant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    username = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    contact = models.CharField(max_length=100)
    image = models.ImageField(upload_to='images', blank=True)
    location = models.CharField(max_length=100)
    opentime = models.TimeField(default=time (7, 0, 0))
    closetime = models.TimeField(default=time (23, 0, 0))
    groups = models.ManyToManyField(Group, related_name='restaurant_set', blank=True)
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='restaurant_set',
        blank=True,
    )

    def __str__(self):
        return self.username
    


class Menu(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)

    
    def __str__(self):
        return f'Menu for {self.restaurant.name}'
    


class Category(models.Model):
    STARTER = 'STARTER'
    RICE = 'RICE'
    PASTA = 'PASTA'
    MEAT = 'MEAT'
    BURGER = 'BURGER'
    PIZZA = 'PIZZA'
    BREAD = 'BREAD'
    SALAD = 'SALAD'
    OTHER_COURSE = 'OTHER_COURSE'
    DESSERT = 'DESSERT'
    DRINK = 'DRINK'
    TOPPING = 'TOPPING'
    CATEGORY_CHOICES = [
        (STARTER, 'Starter'),
        (OTHER_COURSE, 'Other courses'),
        (DESSERT, 'Dessert'),
        (DRINK, 'Drink'),
        (RICE, 'Rice'),
        (PASTA, 'Pasta'),
        (MEAT, 'Meat'),
        (BURGER, 'Burger'),
        (BREAD, 'Bread'),
        (PIZZA, 'Pizza'),
        (SALAD, 'Salad'),
        (TOPPING, 'Topping'),
    ]
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    def __str__(self):
        return self.get_name_display()




class MenuItem(models.Model):
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='images/')
    price = models.IntegerField()
    calories = models.IntegerField()
    protein = models.IntegerField()
    carbs = models.IntegerField()
    fat = models.IntegerField()

    def average_rating(self):
        reviews = self.reviews.all()
        if reviews:
            total_ratings = sum(review.rating for review in reviews)
            average = total_ratings / len(reviews)
            return round(average, 1)
        return None

    def __str__(self):
        return self.name


class Order(models.Model):
    TAKE_AWAY = 'TAKE_AWAY'
    DINE_IN = 'DINE_IN'
    ORDER_TYPE_CHOICES = [
        (TAKE_AWAY, 'Take-away'),
        (DINE_IN, 'Dine-in'),
    ]
    ORDER_PREPARING = 'ORDER_PREPARING'
    ORDER_READY = 'ORDER_READY'
    ORDER_DISPATCHED = 'ORDER_DISPATCHED'
    ORDER_STATUS_CHOICES = [
        (ORDER_PREPARING, 'Order is being prepared'),
        (ORDER_READY, 'Order is ready for you'),
        (ORDER_DISPATCHED, 'Order dispatched'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    created_on = models.DateTimeField(default=timezone.now)
    menu_items = models.ManyToManyField(MenuItem)
    special_instructions = models.TextField(blank=True)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default=ORDER_PREPARING)
    price = models.IntegerField(default=0)
    fat = models.IntegerField(default=0)
    carbs = models.IntegerField(default=0)
    protein = models.IntegerField(default=0)
    calories = models.IntegerField(default=0)
    def __str__(self):
        return f'Order #{self.pk}'
    



class Review(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='reviews')
    customer_name = models.ForeignKey(Customer, on_delete=models.CASCADE)
    review_text = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Review for {self.menu_item.name} by {self.customer_name}"