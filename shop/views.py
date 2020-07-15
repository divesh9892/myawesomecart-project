from django.shortcuts import render
from .models import Product, Contact, Order, OrderUpdate, Comment
from math import ceil
import json
from django.views.decorators.csrf import csrf_exempt
from .forms import CommentForm
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.forms import UserCreationForm
from.forms import CreateUserForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect
from PayTm import Checksum
from decouple import config
# Create your views here.

MERCHANT_KEY = config('MERCHANT_KEY')
MID = config('MID')
# MERCHANT_KEY = 'Enter your merchant key'
# MERCHANT_ID = 'Enter your merchant id'


def registerPage(request):
    if request.user.is_authenticated:
        return redirect('ShopHome')
    else:
        form = CreateUserForm()

        if request.method == "POST":
            form = CreateUserForm(request.POST)
            if form.is_valid():
                form.save()
                user = form.cleaned_data.get('username')
                messages.success(request, 'Account Created for ' + user)

                return redirect('Login')
        context = {'form': form}
        return render(request, 'shop/register.html', context)


def loginPage(request):
    if request.user.is_authenticated:
        return redirect('ShopHome')
    else:
        form = UserCreationForm()
        if request.method == 'POST':
            user = request.POST.get('username')

            pwd = request.POST.get('password')

            user = authenticate(request, username=user, password=pwd)

            if user is not None:
                login(request, user)
                return redirect('ShopHome')
            else:
                messages.info(request, "Username or password is incorrect!!")
        context = {'form': form}
        return render(request, 'shop/login.html', context)


def logoutUser(request):

    logout(request)
    return redirect('ShopHome')


def index(request):
    # products = Product.objects.all()
    # print(products)
    # n = len(products)
    # nSlides = n//4 + ceil((n/4)-(n//4))

    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prod = Product.objects.filter(category=cat)
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))
        allProds.append([prod, range(1, nSlides), nSlides])

    # params = {'no_of_slides': nSlides, 'range': range(1, nSlides), 'product': products}
    # allProds = [[products, range(1, nSlides), nSlides],
    #           [products, range(1, nSlides), nSlides]]
    params = {'allProds': allProds}
    return render(request, 'shop/index.html', params)


def searchMatch(query, item):
    # return true only if query matches the item
    if query in item.desc.lower() or query in item.product_name.lower() or query in item.category.lower():
        return True
    else:
        return False


def search(request):
    query = request.GET.get('search')
    allProds = []
    catprods = Product.objects.values('category', 'id')
    cats = {item['category'] for item in catprods}
    for cat in cats:
        prodtemp = Product.objects.filter(category=cat)
        prod = [item for item in prodtemp if searchMatch(query, item)]
        n = len(prod)
        nSlides = n // 4 + ceil((n / 4) - (n // 4))

        if len(prod) != 0:
            allProds.append([prod, range(1, nSlides), nSlides])
    params = {'allProds': allProds, "msg": ""}

    if len(allProds) == 0 or len(query) < 3:
        params = {'msg': "Please make sure to enter relevant search query"}
    return render(request, 'shop/search.html', params)


def about(request):
    return render(request, 'shop/about.html')


def contact(request):
    thank = False
    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        desc = request.POST.get('desc', '')
        contact = Contact(name=name, email=email, phone=phone, desc=desc)
        contact.save()
        thank = True

    return render(request, 'shop/contact.html', {'thank': thank})

@login_required(login_url='Login')
def tracker(request):
    if request.method == 'POST':
        orderId = request.POST.get('orderId', '')
        email = request.user.email
        try:
            order = Order.objects.filter(order_id=orderId, email=email)
            if len(order) > 0:
                update = OrderUpdate.objects.filter(order_id=orderId)
                updates = []
                for item in update:
                    updates.append({'text': item.update_desc, 'time': item.timestamp})
                    response = json.dumps({"status": "success", "updates": updates, "itemsJson": order[0].items_json},
                                          default=str)
                return HttpResponse(response)
            else:
                return HttpResponse('{"status":"noitem"}')
        except Exception as e:
            return HttpResponse('{"status":"error"}')

    return render(request, 'shop/tracker.html')


def productView(request, myid):
    #  Fetch products using id
    product = Product.objects.filter(id=myid)
    comments = Comment.objects.filter(post=product[0]).order_by('-created_date')
    paginator = Paginator(comments, 10)
    page = request.GET.get('page')
    comments = paginator.get_page(page)
    return render(request, 'shop/prodView.html', {'product': product[0], 'comments': comments})

@login_required(login_url='Login')
def add_comment_to_post(request, pk):
    post = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.email = request.user.email
            print(request.user.email)
            comment.save()
            return redirect('/shop/products/'+str(pk), pk=post.pk)
    else:
        form = CommentForm(initial=dict(author=request.user))
    return render(request, 'shop/add_comment_to_post.html', {'form': form})


@login_required(login_url='Login')
def checkout(request):
    if request.method == 'POST':
        items_json = request.POST.get('itemsJson', '')
        name = request.POST.get('name', '')
        amount = request.POST.get('amount', '')
        email = request.user.email
        address = request.POST.get('address1', '') + " " + request.POST.get('address2', '')
        city = request.POST.get('city', '')
        state = request.POST.get('state', '')
        zip_code = request.POST.get('zip_code', '')
        phone = request.POST.get('phone', '')
        order = Order(items_json=items_json, name=name, amount=amount, email=email, address=address, city=city, state=state, zip_code=zip_code, phone=phone)
        order.save()
        update = OrderUpdate(order_id=order.order_id, update_desc="The order has been placed")
        update.save()
        thank = True
        id = order.order_id
        # return render(request, 'shop/checkout.html', {'thank': thank, 'id': id})
        param_dict = {
            'MID': MID,
            'ORDER_ID': str(id),
            'TXN_AMOUNT': str(amount),
            'CUST_ID': email,
            'INDUSTRY_TYPE_ID': 'Retail',
            'WEBSITE': 'WEBSTAGING',
            'CHANNEL_ID': 'WEB',
            'CALLBACK_URL': 'http://127.0.0.1:8000/shop/handlerequest/',
        }
        param_dict['CHECKSUMHASH'] = Checksum.generate_checksum(param_dict, MERCHANT_KEY)
        return render(request, 'shop/paytm.html', {'param_dict': param_dict})

    return render(request, 'shop/checkout.html')


@csrf_exempt
def handlerequest(request):
    form = request.POST
    response_dict = {}
    for i in form.keys():
        response_dict[i] = form[i]
        if i == 'CHECKSUMHASH':
            checksum = form[i]
    verify = Checksum.verify_checksum(response_dict, MERCHANT_KEY, checksum)
    if verify:
        if response_dict['RESPCODE'] == '01':
            print("order successfull")
        else:
            ordid = response_dict['ORDERID']
            order = Order.objects.get(pk=ordid)
            ordupd = OrderUpdate.objects.filter(order_id=order.order_id)
            order.delete()
            ordupd.delete()
            print('order was not successfull because ' + response_dict['RESPMSG'])
    return render(request, 'shop/paymentstatus.html', {'response': response_dict})


@csrf_exempt
@login_required
def comment_approve(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    # prod_id = request.POST['data']
    if request.method == 'POST':
        prod_id = request.POST.get('data')
        request.session['prod_id'] = prod_id
        comment.approved_comment = True
        comment.save()
        # comment.approve()
        return redirect('/shop/products/' + str(prod_id), pk=comment.post.pk)
    prod_id = request.session.get('prod_id')
    return redirect('/shop/products/'+str(prod_id), pk=comment.post.pk)


@csrf_exempt
@login_required
def comment_remove(request, pk):
    comment = get_object_or_404(Comment, pk=pk)

    if request.method == 'POST':
        prod_id = request.POST.get('data')

        request.session['prod_id'] = prod_id

        comment.delete()

        return redirect('/shop/products/' + str(prod_id), pk=comment.post.pk)
    prod_id = request.session.get('prod_id')
    return redirect('/shop/products/' + str(prod_id), pk=comment.post.pk)


@login_required(login_url='Login')
def your_orders(request):
    email = request.user.email
    prod = Order.objects.filter(email=email)
    all_orders = []
    for id in prod:
        y = json.loads(id.items_json)
        for key, value in y.items():
            prod_id = key.split("pr")[1]
            quantity = value[0]
            name = value[1]
            price = value[2]

            context={
             'prod_id': prod_id,
             'amount': price,
             'quantity': quantity,
             'name': name,
             'items': json.loads(id.items_json),
             'order_id': id.order_id,
            }
            all_orders.append(context)

    return render(request, 'shop/orderhistory.html', {'context':all_orders})


@login_required(login_url='Login')
def invoice(request, myid):
    email = request.user.email
    prod = Order.objects.filter(email=email, order_id=myid)
    all_orders = []
    for id in prod:
        cust_name = id.name
        address = id.address
        y = json.loads(id.items_json)
        for key, value in y.items():
            prod_id = key.split("pr")[1]
            quantity = value[0]
            name = value[1]
            price = value[2]

            context = {
                'email': email,
                'cust_name': cust_name,
                'address': address,
                'prod_id': prod_id,
                'amount': price*quantity,
                'amount2': price,
                'quantity': quantity,
                'name': name,
                'items': json.loads(id.items_json),
                'order_id': id.order_id,
            }

            all_orders.append(context)

    return render(request, "shop/invoice.html", {'context': all_orders})

# @csrf_exempt
# def ordervalid(request):
#     if request.method == 'POST':
#         respcode = request.POST.get('data')
#         order_id = request.POST.get('data1')
#         print(respcode)
#         print(order_id)
#         if respcode != '01':
#             order = Order.objects.get(pk=order_id)
#             order.delete()
#             ordupd = OrderUpdate.objects.get(pk=order_id)
#             ordupd.delete()
#             return redirect('/shop/orderhistory/')
#         else:
#             return redirect('/shop/orderhistory/')
