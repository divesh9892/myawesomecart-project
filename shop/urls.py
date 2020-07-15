from django.conf.urls import url
from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.index, name="ShopHome"),
    path("about/", views.about, name="AboutUs"),
    path("contact/", views.contact, name="ContactUs"),
    path("tracker/", views.tracker, name="TrackingStatus"),
    path("search/", views.search, name="Search"),
    path("products/<int:myid>", views.productView, name="ProductView"),
    path("checkout/", views.checkout, name="Checkout"),
    path("handlerequest/", views.handlerequest, name="HandleRequest"),
    path("login/", views.loginPage, name="Login"),
    path("logout/", views.logoutUser, name="Logout"),
    path("register/", views.registerPage, name="Register"),
    path("orderhistory/", views.your_orders, name="OrderHistory"),
    path("invoice/<int:myid>", views.invoice, name="Invoice"),
    path('comment/<int:pk>/approve/', views.comment_approve, name='comment_approve'),
    path('comment/<int:pk>/remove/', views.comment_remove, name='comment_remove'),
    url(r'^ratings/', include('star_ratings.urls', namespace='ratings')),
    path('products/<int:pk>/comment/', views.add_comment_to_post, name='add_comment_to_post'),

    #path("ordervalid/", views.ordervalid, name="OrderValid"),
]
