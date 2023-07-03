from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, View
from .models import User, Customer, Restaurant, Order, MenuItem, Menu, Category, models, Review
from .forms import RestaurantSignUpForm, CustomerSignUpForm, LoginForm


# Create your views here.

def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'About.html')

def terms(request):
    return render(request, 'terms.html')

def privacy(request):
    return render(request, 'privacy.html')

def contact(request):
    return render(request, 'Contact.html')

def signup(request):
    return render(request, 'Signup.html')

def signup_customer(request):
    return render(request, 'signup_customer.html')

def signup_restaurant(request):
    return render(request, 'signup_restaurant.html')


def logout_view(request):
    logout(request)
    return redirect('index')



def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.is_customer:
                return redirect('/restaurant_list')
            elif user.is_restaurant:
                return redirect('/restaurant/orders')
            else:
                 #Handle other user types if applicable
                pass
        else:
             #Handle invalid login credentials
            pass
    else:
        pass

    form = LoginForm()


    return render(request, 'Login.html', {'form': form})



class CustomerSignUpView(CreateView):
    model = User
    form_class = CustomerSignUpForm
    template_name = 'signup_customer.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'customer'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('login')
    


class RestaurantSignUpView(CreateView):
    model = User
    form_class = RestaurantSignUpForm
    template_name = 'signup_restaurant.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'restaurant'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('login')
    


@login_required
def restaurant_list(request):
    restaurants = Restaurant.objects.all()
    context = {'restaurants': restaurants}
    return render(request, 'restaurant_list.html', context)


@login_required
def restaurant_detail(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    menu = restaurant.menu_set.first()
    menu_items = menu.menuitem_set.all()
    context = {'restaurant': restaurant, 'menu_items': menu_items}
    return render(request, 'restaurant_detail.html', context)




class ordersave(LoginRequiredMixin, View):
    @login_required
    def get(self, request, restaurant_id):
        menu = get_object_or_404(Menu, restaurant_id=restaurant_id)
        desired_order = [
            Category.STARTER,
            Category.RICE,
            Category.PASTA,
            Category.MEAT,
            Category.BREAD,
            Category.BURGER,
            Category.PIZZA,
            Category.OTHER_COURSE,
            Category.SALAD,
            Category.TOPPING,
            Category.DESSERT,
            Category.DRINK,
        ]
        categories = Category.objects.filter(name__in=desired_order).order_by(
            models.Case(
                *[models.When(name=name, then=pos) for pos, name in enumerate(desired_order)]
            )
        )
        menu_items_by_category = {}

        for category in categories:
            menu_items = MenuItem.objects.filter(menu=menu, category=category)
            menu_items_by_category[category] = menu_items

        context = {
            'menu': menu,
            'menu_items_by_category': menu_items_by_category
        }
        
        return render(request, 'order.html', context)

    
    @login_required
    def post(self, request, restaurant_id):
        order_items = {'items': []}
        items = request.POST.getlist('items[]')

        for item in items:
            menu_item = MenuItem.objects.get(pk=int(item))
            item_data = {
                'id' : menu_item.pk,
                'name' : menu_item.name,
                'price' : menu_item.price,
                'calories' : menu_item.calories,
                'protein' : menu_item.protein,
                'carbs' : menu_item.carbs,
                'fat' : menu_item.fat,
            }

            order_items['items'].append(item_data)

            price = 0
            calories = 0
            protein = 0
            carbs = 0
            fat = 0
            item_ids = []

        for item in order_items['items']:
            price += item['price']
            calories += item['calories']
            protein += item['protein']
            carbs += item['carbs']
            fat += item['fat']
            item_ids.append(item['id'])


        special_instructions = request.POST.get('instructions', '')  # Added special instructions
        order_type = request.POST.get('order_type', '')  # Added order type
        customer = request.user.customer
        restaurant = Restaurant.objects.get(pk=restaurant_id)

        order = Order.objects.create(
            restaurant=restaurant,
            customer=customer,
            price=price,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat,
            special_instructions=special_instructions,  # Set special instructions
            order_type=order_type  # Set order type
        )
        order.menu_items.add(*item_ids)


        context = {
            'items' : order_items['items'],
            'price' : price,
            'calories': calories,
            'protein' : protein,
            'carbs' : carbs,
            'fat' : fat
        }

        return render(request, 'order_confirmation.html', context)




@login_required
def order_history(request):
    orders = Order.objects.filter(customer=request.user.customer)
    return render(request, 'order_history.html', {'orders': orders})




@login_required
def restaurant_orders(request):
    orders = Order.objects.filter(restaurant=request.user.restaurant)
    displayed_reviews = set()

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        order_status = request.POST.get('order_status')
        order = get_object_or_404(Order, id=order_id, restaurant=request.user.restaurant)
        order.order_status = order_status
        order.save()
        return redirect('restaurant_orders') 
    
    for order in orders:
        for item in order.menu_items.all():
            if item not in displayed_reviews:
                # Retrieve and display the reviews for the current menu item
                reviews = item.reviews.all()
                displayed_reviews.add(item)  # Add the menu item to the set
    
    return render(request, 'restaurant_orders.html', {'orders': orders})



@login_required
def order_statuss(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        order_status = request.POST.get('order_status')
        order = get_object_or_404(Order, pk=order_id, restaurant=request.user.restaurant)
        order.order_status = order_status
        order.save()
        return redirect('restaurant_orders')



@login_required
def submit_item_review(request, item_id):
    if request.method == 'POST':
        review_text = request.POST.get('review')
        rating = request.POST.get('rating')
        menu_item = MenuItem.objects.get(pk=item_id)
        customer = request.user.customer

        review = Review(menu_item=menu_item, customer_name=customer, review_text=review_text, rating=rating)
        review.save()
    
    return redirect('order_history')



@login_required
def item_reviews(request, item_id):
    menu_item = get_object_or_404(MenuItem, pk=item_id)
    reviews = menu_item.reviews.all()
    return render(request, 'item_reviews.html', {'menu_item': menu_item, 'reviews': reviews})
