import datetime
import pdfkit
from django.db.models import Sum
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.template.loader import get_template
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required 
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, View
from .models import User, Customer, Restaurant, Order, MenuItem, Menu, Category, models, Review, UserActivity, Transaction
from .forms import RestaurantSignUpForm, CustomerSignUpForm, LoginForm, ReportFilterForm
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse_lazy
from intasend import APIService
from datetime import date, timedelta
from django.db.models import Q
from django.utils import timezone


token = "ISSecretKey_test_bcac21b8-cd50-4f88-ba07-7ca0daa8c075"
publishable_key = "ISPubKey_test_5545533a-3242-43e2-a737-cbbff8e5dfa2"
service = APIService(token=token, publishable_key=publishable_key, test=True)


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
    user = request.user

    # Determine the content type of the User model
    user_content_type = ContentType.objects.get_for_model(get_user_model())

    # Create a UserActivity instance with the user and content type
    UserActivity.objects.create(
        user=user,
        activity_type='logout',
        content_type=user_content_type,
        object_id=user.id
    )

    logout(request)
    
    return redirect('index')



def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            try:
                # Determine the content type of the User model
                user_content_type = ContentType.objects.get_for_model(get_user_model())

                # Create a UserActivity instance with the user and content type
                UserActivity.objects.create(
                    user=user,
                    activity_type='login',
                    content_type=user_content_type,
                    object_id=user.id
                )
            except Exception as e:
                print(f"Error creating UserActivity: {e}")

            if user.is_customer:
                return redirect('/restaurant_list')
            elif user.is_restaurant:
                return redirect('restaurant_profile')
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
    success_url = reverse_lazy('login') 

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'customer'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.instance

        # Determine the content type of the User model
        user_content_type = ContentType.objects.get_for_model(get_user_model())

        # Create a UserActivity instance with the user and content type
        UserActivity.objects.create(
            user=user,
            activity_type='signup_customer',
            content_type=user_content_type,
            object_id=user.id
        )

        login(self.request, user)
        return response
    


class RestaurantSignUpView(CreateView):
    model = User
    form_class = RestaurantSignUpForm
    template_name = 'signup_restaurant.html'
    success_url = reverse_lazy('login') 

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'restaurant'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.instance

        # Determine the content type of the User model
        user_content_type = ContentType.objects.get_for_model(get_user_model())

        # Create a UserActivity instance with the user and content type
        UserActivity.objects.create(
            user=user,
            activity_type='signup_restaurant',
            content_type=user_content_type,
            object_id=user.id
        )

        login(self.request, user)
        return response
    


@login_required(login_url = 'login')
def restaurant_list(request):
    restaurants = Restaurant.objects.all()

    search_query = request.GET.get('search')

    if search_query:
        restaurants = Restaurant.objects.filter(name__icontains=search_query)
    else:
        restaurants = Restaurant.objects.all()

    context = {'restaurants': restaurants}
    return render(request, 'restaurant_list.html', context)





class ordersave(LoginRequiredMixin, View):
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

        search_query = request.GET.get('search')

        if search_query:
            # Filter menu items by the search query
            menu_items = MenuItem.objects.filter(
                Q(menu=menu, category__in=categories),
                Q(name__icontains=search_query) | Q(description__icontains=search_query)
            )
            # Group the items based on their category
            for category in categories:
                menu_items_by_category[category] = menu_items.filter(category=category)
        else:
            # No search query, retrieve all menu items based on categories
            for category in categories:
                menu_items = MenuItem.objects.filter(menu=menu, category=category)
                menu_items_by_category[category] = menu_items

        context = {
            'menu': menu,
            'menu_items_by_category': menu_items_by_category
        }
        
        return render(request, 'order.html', context)
    

    def post(self, request, restaurant_id):
        item_ids = request.POST.getlist('items[]')
        if not item_ids:
            # If no items are selected, show an error message
            messages.error(request, 'Please select at least one item before proceeding to checkout.')
            return redirect('order', restaurant_id=restaurant_id)
        request.session['cart_items'] = item_ids
        request.session['restaurant_id'] = restaurant_id
        special_instructions = request.POST.get('instructions', '')
        order_type = request.POST.get('order_type')

        request.session['special_instructions'] = special_instructions
        request.session['order_type'] = order_type
        
        
        menu_items = MenuItem.objects.filter(pk__in=item_ids)
        total_price = sum(menu_item.price for menu_item in menu_items)

        response = service.collect.checkout(
            phone_number =  "254708374149",
            email = "abc@gmail.com",
            amount = 10,
            currency = "KES",
            comment = "Payment for food",
        )
    
        payment_link = response.get("url")
        payment_status = response.get("paid")

        

        if payment_status == True:
            print("Payment successful")
        else:
            context = {
                'menu_items': menu_items,
                'total_price': total_price,
                'item_ids': item_ids,
                'payment_link': payment_link,
                'payment_status': payment_status
            }
            return render(request, 'cart.html', context) 


def order_confirmation(request):
    order_items = {'items': []}
    item_ids = request.session.get('cart_items')
    restaurant_id = request.session.get('restaurant_id')
    special_instructions = request.session.get('special_instructions')
    order_type = request.session.get('order_type')
    
    price = 0
    calories = 0
    protein = 0
    carbs = 0
    fat = 0

    for item_id in item_ids:
        menu_item = MenuItem.objects.get(pk=int(item_id))
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

        price += menu_item.price
        calories += menu_item.calories
        protein += menu_item.protein
        carbs += menu_item.carbs
        fat += menu_item.fat


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
        special_instructions=special_instructions,  
        order_type=order_type  
    )
    order.menu_items.add(*item_ids)

    transaction = Transaction.objects.create(
        customer=customer,
        restaurant=restaurant,
        order=order,
        amount=price,
    )

    context = {
        'items': order_items['items'],
        'price': price,
        'calories': calories,
        'protein': protein,
        'carbs': carbs,
        'fat': fat,
        'transaction': transaction,
    }

    return render(request, 'order_confirmation.html', context)
    

@login_required(login_url = 'login')
def order_history(request):
    orders = Order.objects.filter(customer=request.user.customer)

    if request.method == 'POST':
        fromdate = request.POST.get('fromdate')
        todate = request.POST.get('todate')

        if fromdate and todate:
            # Filter orders based on date range
            filtered_orders = orders.filter(created_on__range=[fromdate, todate])

        context = {
            'orders': filtered_orders,
            'fromdate': fromdate,
            'todate': todate,
            }
        return render(request, 'order_history.html', context)
    
    else:
        context = {
            'orders': orders,
        }

        return render(request, 'order_history.html', context)





@login_required(login_url = 'login')
def customer_receipt(request):
    orders = Order.objects.filter(customer=request.user.customer)

    if request.method == 'POST':
        fromdate = request.POST.get('fromdate')
        todate = request.POST.get('todate')

        if fromdate and todate:
            # Filter orders based on date range
            filtered_orders = orders.filter(created_on__range=[fromdate, todate])

        context = {
            'orders': filtered_orders,
            'fromdate': fromdate,
            'todate': todate,
            }
        return render(request, 'customer_receipt.html', context)
    
    else:
        context = {
            'orders': orders,
        }

        return render(request, 'customer_receipt.html', context)



@login_required(login_url = 'login')
def download_customer_receipt(request):
    orders = Order.objects.filter(customer=request.user.customer)

    fromdate = request.GET.get('fromdate')
    todate = request.GET.get('todate')

    if fromdate and todate:
        # Filter orders based on date range
        filtered_orders = orders.filter(created_on__range=[fromdate, todate])

    else:
        filtered_orders = orders


    template_path = 'customer_receipt.html'
    context = {
        'orders': filtered_orders,
        'fromdate': fromdate,
        'todate': todate,
    }

    # Load the HTML template
    template = get_template(template_path)
    html = template.render(context)

    # Create a PDF file
    pdf_file = HttpResponse(content_type='application/pdf')
    pdf_file['Content-Disposition'] = 'attachment; filename="customer_receipt.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=pdf_file)

    # Check if PDF generation was successful
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')

    return pdf_file





@login_required(login_url = 'login')
def restaurant_orders(request):
    orders = Order.objects.filter(restaurant=request.user.restaurant)
    displayed_reviews = set()

    # Handle order status update
    if request.method == 'POST' and 'order_status' in request.POST:
        order_id = request.POST.get('order_id')
        order_status = request.POST.get('order_status')
        order = get_object_or_404(Order, id=order_id, restaurant=request.user.restaurant)
        order.order_status = order_status
        order.save()
        return redirect('restaurant_orders')

    # Handle filtering based on the date range
    if request.method == 'POST' and 'fromdate' in request.POST and 'todate' in request.POST:
        fromdate = request.POST.get('fromdate')
        todate = request.POST.get('todate')

        if fromdate and todate:
            # Filter orders based on date range
            orders = orders.filter(created_on__range=[fromdate, todate])

    # Retrieve displayed reviews for menu items
    for order in orders:
        for item in order.menu_items.all():
            if item not in displayed_reviews:
                reviews = item.reviews.all()
                displayed_reviews.add(item)

    context = {
        'orders': orders,
    }

    return render(request, 'restaurant_orders.html', context)






@login_required(login_url = 'login')
def restaurant_receipt(request):
    orders = Order.objects.filter(restaurant=request.user.restaurant)

    if request.method == 'POST':
        fromdate = request.POST.get('fromdate')
        todate = request.POST.get('todate')

        if fromdate and todate:
            # Filter orders based on date range
            filtered_orders = orders.filter(created_on__range=[fromdate, todate])

        context = {
            'orders': filtered_orders,
            'fromdate': fromdate,
            'todate': todate,
            }
        return render(request, 'restaurant_receipt.html', context)
    
    else:
        context = {
            'orders': orders,
        }

        return render(request, 'restaurant_receipt.html', context)





@login_required
def download_restaurant_receipt(request):
    user = request.user
    restaurant = user.restaurant
    orders = Order.objects.filter(restaurant=request.user.restaurant)

    fromdate = request.GET.get('fromdate')
    todate = request.GET.get('todate')

    if fromdate and todate:
        # Filter orders based on date range
        filtered_orders = orders.filter(created_on__range=[fromdate, todate])

    else:
        filtered_orders = orders


    template_path = 'restaurant_receipt.html'
    context = {
        'orders': filtered_orders,
        'fromdate': fromdate,
        'todate': todate,
    }

    # Load the HTML template
    template = get_template(template_path)
    html = template.render(context)

    # Create a PDF file
    pdf_file = HttpResponse(content_type='application/pdf')
    pdf_file['Content-Disposition'] = 'attachment; filename="restaurant_receipt.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=pdf_file)

    # Check if PDF generation was successful
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')

    return pdf_file



@login_required(login_url = 'login')
def order_statuss(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        order_status = request.POST.get('order_status')
        order = get_object_or_404(Order, pk=order_id, restaurant=request.user.restaurant)
        order.order_status = order_status
        order.save()
        return redirect('restaurant_orders')



@login_required(login_url = 'login')
def submit_item_review(request, item_id):
    if request.method == 'POST':
        review_text = request.POST.get('review')
        rating = request.POST.get('rating')
        menu_item = MenuItem.objects.get(pk=item_id)
        customer = request.user.customer

        review = Review(menu_item=menu_item, customer_name=customer, review_text=review_text, rating=rating)
        review.save()
    
    return redirect('order_history')



@login_required(login_url = 'login')
def item_reviews(request, item_id):
    menu_item = get_object_or_404(MenuItem, pk=item_id)
    reviews = menu_item.reviews.all()
    return render(request, 'item_reviews.html', {'menu_item': menu_item, 'reviews': reviews})





@login_required(login_url = 'login')
def customer_profile(request):
    user = request.user
    customer = user.customer

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update':
            username = request.POST.get('username')
            contact = request.POST.get('contact')
            email = request.POST.get('email')
            
            # Update user and customer details
            user.username = username
            user.email = email
            user.save()

            customer.contact = contact
            customer.save()

        elif action == 'delete':
            customer.delete()
            user.delete()
            # Perform any other necessary cleanup tasks
            return redirect('index')
        
        elif action == 'change_password':
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # To update the session with the new password
                messages.success(request, 'Your password was successfully updated!')
                return redirect('customer_profile')
            else:
                messages.error(request, 'Please correct the errors below.')

        return redirect('customer_profile')
    
    else:
        password_form = PasswordChangeForm(user)

    return render(request, 'customer_profile.html', {'customer': customer, 'password_form': password_form})


@login_required(login_url = 'login')
def restaurant_profile(request):
    user = request.user
    restaurant = user.restaurant

    categories = Category.objects.all()

    if request.method == 'GET':
        search_query = request.GET.get('search')
        if search_query:
            menu_items = MenuItem.objects.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query),
                menu__in=restaurant.menus.all()
            )
        else:
            menu_items = MenuItem.objects.filter(menu__in=restaurant.menus.all())

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update':
            username = request.POST.get('username')
            contact = request.POST.get('contact')
            image = request.POST.get('image')
            email = request.POST.get('email')
            opentime = request.POST.get('opentime')
            closetime = request.POST.get('closetime')
            
            # Update user and restaurant details
            user.username = username
            user.email = email
            user.save()

            restaurant.contact = contact
            restaurant.opentime = opentime
            restaurant.closetime = closetime
            restaurant.image = image
            restaurant.save()

        elif action == 'delete':
            restaurant.delete()
            user.delete()
            # Perform any other necessary cleanup tasks
            return redirect('home')
        
        elif action == 'add':
            # Get the menu for the restaurant
            menu_id = request.POST.get('menu_id')
            menu = get_object_or_404(Menu, id=menu_id)

            # Get the form data for the new menu item
            name = request.POST.get('name')
            description = request.POST.get('description')
            image = request.FILES.get('image')
            price = request.POST.get('price')
            calories = request.POST.get('calories')
            protein = request.POST.get('protein')
            fat = request.POST.get('fat')
            carbs = request.POST.get('carbs')
            category_id = request.POST.get('category')
            category = get_object_or_404(Category, id=category_id)

            # Create the new menu item
            menu_item = MenuItem(menu=menu, category=category, name=name, description=description, image=image, price=price, calories=calories, protein=protein, fat=fat, carbs=carbs)
            menu_item.save()

        elif action == 'update_menu_item':
            # Get the menu item to update
            menu_item_id = request.POST.get('menu_item_id')
            menu_item = get_object_or_404(MenuItem, id=menu_item_id)

            # Get the updated form data
            updated_name = request.POST.get('updated_name')
            updated_description = request.POST.get('updated_description')
            updated_image = request.FILES.get('updated_image')
            updated_price = request.POST.get('updated_price')

            # Update the menu item
            menu_item.name = updated_name
            menu_item.description = updated_description
            if updated_image:
                menu_item.image = updated_image
            menu_item.price = updated_price
            menu_item.save()

        elif action == 'delete_menu_item':
            # Get the menu item to delete
            menu_item_id = request.POST.get('menu_item_id')
            menu_item = get_object_or_404(MenuItem, id=menu_item_id)

            # Delete the menu item
            menu_item.delete()

        elif action == 'change_password':
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # To update the session with the new password
                messages.success(request, 'Your password was successfully updated!')
                return redirect('restaurant_profile')
            else:
                messages.error(request, 'Please correct the errors below.')

        return redirect('restaurant_profile')

    else:
        password_form = PasswordChangeForm(user)

    return render(request, 'restaurant_profile.html', {'restaurant': restaurant, 'categories': categories, 'password_form': password_form, 'menu_items': menu_items})




@login_required
@staff_member_required
def report_view(request):
    customers = Customer.objects.all()
    restaurants = Restaurant.objects.all()
    orders = Order.objects.all()
    transactions = Transaction.objects.all()

    total_amount = transactions.aggregate(Sum('amount'))['amount__sum']

    if request.method == 'POST':
        fromdate = request.POST.get('fromdate')
        todate = request.POST.get('todate')

        if fromdate and todate:
            # Filter customers based on date range
            filtered_customers = customers.filter(user__date_joined__range=[fromdate, todate])

            # Filter restaurants based on date range
            filtered_restaurants = restaurants.filter(user__date_joined__range=[fromdate, todate])

            # Filter orders based on date range
            filtered_orders = orders.filter(created_on__range=[fromdate, todate])

            # Filter transactions based on date range
            filtered_transactions = transactions.filter(timestamp__range=[fromdate, todate])

        

        context = {
            'customers': filtered_customers,
            'restaurants': filtered_restaurants,
            'orders': filtered_orders,
            'transactions': filtered_transactions,
            'fromdate': fromdate,
            'todate': todate,
            'total_amount': total_amount,
            }
        return render(request, 'report.html', context)
    
    else:
        context = {
            'customers': customers,
            'restaurants': restaurants,
            'orders': orders,
            'transactions': transactions,
            'total_amount': total_amount,
        }

        return render(request, 'report.html', context)




@login_required
@staff_member_required
def download_report(request):
    fromdate = request.GET.get('fromdate')
    todate = request.GET.get('todate')

    customers = Customer.objects.all()
    restaurants = Restaurant.objects.all()
    orders = Order.objects.all()
    transactions = Transaction.objects.all()

    total_amount = transactions.aggregate(Sum('amount'))['amount__sum']

    if fromdate and todate:
        # Filter customers based on date range
        filtered_customers = customers.filter(user__date_joined__range=[fromdate, todate])

        # Filter restaurants based on date range
        filtered_restaurants = restaurants.filter(user__date_joined__range=[fromdate, todate])

        # Filter orders based on date range
        filtered_orders = orders.filter(created_on__range=[fromdate, todate])

        # Filter transactions based on date range
        filtered_transactions = transactions.filter(timestamp__range=[fromdate, todate])

    else:
        filtered_customers = customers
        filtered_restaurants = restaurants
        filtered_orders = orders
        filtered_transactions = transactions


    template_path = 'report.html'
    context = {
        'customers': filtered_customers,
        'restaurants': filtered_restaurants,
        'orders': filtered_orders,
        'transactions': filtered_transactions,
        'fromdate': fromdate,
        'todate': todate,
        'total_amount': total_amount,
    }

    # Load the HTML template
    template = get_template(template_path)
    html = template.render(context)

    # Create a PDF file
    pdf_file = HttpResponse(content_type='application/pdf')
    pdf_file['Content-Disposition'] = 'attachment; filename="report.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=pdf_file)

    # Check if PDF generation was successful
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')

    return pdf_file
