from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.vary import vary_on_cookie
from rest_framework.pagination import PageNumberPagination

from .models import Product, Category, Cart, User, Comment, Order
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page, never_cache
from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import ProductSerializer, CategorySerializer, CartSerializer, CommentSerializer
import stripe
from .permissions import IsAdminOrReadOnly, CanManageProducts, CanManageCategories
import json
from django.conf import settings
from django.http import JsonResponse
from .tasks import send_order_confirmation_email


@vary_on_cookie
def home(request):
    products = Product.objects.all().select_related('category').prefetch_related('images').only('id', 'name', 'slug',
                                                                                                'price', 'discount',
                                                                                                'category__name').order_by(
        'id')

    category_id = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    min_discount = request.GET.get('min_discount')
    search_query = request.GET.get('search', '')

    if category_id:
        products = products.filter(category_id=category_id)
    if min_price:
        products = products.filter(final_price__gte=min_price)
    if max_price:
        products = products.filter(final_price__lte=max_price)
    if min_discount:
        products = products.filter(discount__gte=min_discount)
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    paginator = Paginator(products, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all().prefetch_related('subcategories')
    return render(request, 'index.html', {'page_obj': page_obj, 'categories': categories})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            request.session.modified = True
            messages.success(request, 'Successfully logged in!')
            response = redirect('home')
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'login.html')
    return render(request, 'login.html')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'register.html')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'register.html')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                request.session.modified = True
                messages.success(request, 'Successfully registered!')
                response = redirect('home')
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                return response
            else:
                messages.error(request, 'Registration failed. Please try again.')
                return render(request, 'register.html')
    return render(request, 'register.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'Successfully logged out!')
    response = redirect('home')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@login_required
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user).select_related('product')
    total_price = 0

    if request.method == 'POST':
        action = request.POST.get('action')
        product_id = request.POST.get('product_id')

        if action == 'remove' and product_id:
            try:
                cart_item = Cart.objects.get(user=request.user, product_id=product_id)
                cart_item.delete()
                messages.success(request, 'Product removed from cart!')
                return redirect('cart')
            except Cart.DoesNotExist:
                pass

        elif action == 'update_quantity' and product_id:
            try:
                cart_item = Cart.objects.get(user=request.user, product_id=product_id)
                new_quantity = int(request.POST.get('quantity', 1))
                if new_quantity > 0:
                    cart_item.quantity = new_quantity
                    cart_item.save()
                    messages.success(request, 'Quantity updated!')
                else:
                    cart_item.delete()
                    messages.success(request, 'Product removed from cart!')
                return redirect('cart')
            except Cart.DoesNotExist:
                pass

    for item in cart_items:
        item_total = item.product.final_price * item.quantity
        total_price += item_total

    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total_price})


@login_required
def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Please login to add to cart.')
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart.quantity += 1
        cart.save()
    messages.success(request, 'Product added to cart!')
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def add_to_favorites(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    user = request.user
    if user in product.favorites.all():
        product.favorites.remove(user)
    else:
        product.favorites.add(user)
    next_url = request.GET.get('next', 'home')
    return redirect(next_url)


@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
    cart_item.delete()
    messages.success(request, 'Product removed from cart!')
    return redirect('cart')


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.prefetch_related('images', 'attributes', 'comments'), slug=slug)
    product.final_price = product.price * (1 - product.discount / 100)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id).prefetch_related(
        'images').annotate(like_count=Count('favorites')).order_by('-like_count')[:4]
    for related in related_products:
        related.final_price = related.price * (1 - related.discount / 100)
    return render(request, 'product_detail.html', {'product': product, 'related_products': related_products})


@login_required
def user_profile(request):
    if request.method == 'POST':
        user = request.user
        new_email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')

        if new_email != user.email:
            if User.objects.filter(email=new_email).exclude(id=user.id).exists():
                messages.error(request, 'This email is already in use by another user.')
                return redirect('user_profile')

        user.email = new_email
        user.phone_number = phone_number
        user.address = address
        try:
            user.save()
            messages.success(request, 'Profile updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
        return redirect('user_profile')

    favorites = request.user.favorite_products.all().prefetch_related('images')
    paginator = Paginator(favorites, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'profile.html', {'page_obj': page_obj})


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_available=True).select_related('category').prefetch_related('images',
                                                                                                     'attributes',
                                                                                                     'comments')
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'price', 'discount']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']
    pagination_class = PageNumberPagination

    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_to_favorites(self, request, pk=None):
        product = self.get_object()
        product.favorites.add(request.user)
        return Response({'status': 'added to favorites'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def remove_from_favorites(self, request, pk=None):
        product = self.get_object()
        product.favorites.remove(request.user)
        return Response({'status': 'removed from favorites'})


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().prefetch_related('subcategories', 'products')
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).select_related('product')

    @action(detail=False, methods=['post'])
    def add_to_cart(self, request):
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        product = Product.objects.get(id=product_id)
        cart, created = Cart.objects.get_or_create(user=request.user, product=product)
        if not created:
            cart.quantity += int(quantity)
            cart.save()
        return Response({'status': 'added to cart'})


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().select_related('user', 'product')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        comment = self.get_object()
        if request.user in comment.likes.all():
            comment.likes.remove(request.user)
            return Response({'status': 'unliked'})
        comment.likes.add(request.user)
        return Response({'status': 'liked'})


stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user).select_related('product')
    total_price = sum(item.product.final_price * item.quantity for item in cart_items)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            payment_method = data.get('payment_method')

            intent = stripe.PaymentIntent.create(
                amount=int(total_price * 100),
                currency='usd',
                payment_method=payment_method,
                confirm=True,
                off_session=True,
                metadata={'user_id': request.user.id},
            )

            cart_items.delete()
            return JsonResponse({'success': True})
        except stripe.error.StripeError as e:
            return JsonResponse({'error': str(e)}, status=400)

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY
    })


def success(request):
    messages.success(request, 'Payment successful! Your order has been placed.')
    Cart.objects.filter(user=request.user).delete()
    send_order_confirmation_email.delay(request.user.email)
    return redirect('home')


@login_required
def product_manage_view(request):
    if not request.user.is_superuser:
        messages.error(request, "Bu sahifaga kirishga ruxsatingiz yo‘q.")
        return redirect('home')

    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        discount = request.POST.get('discount', '0')
        description = request.POST.get('description')

        try:
            product = Product(
                name=name,
                category_id=category_id,
                price=Decimal(price),
                discount=Decimal(discount),
                description=description,
                is_available=True
            )
            product.save()
            messages.success(request, f"'{product.name}' mahsuloti muvaffaqiyatli qo‘shildi!")
            return redirect('product_manage')
        except (ValueError, TypeError) as e:
            messages.error(request, "Narx yoki chegirma noto‘g‘ri. Iltimos, to‘g‘ri raqam kiriting.")
        except Exception as e:
            messages.error(request, f"Mahsulot qo‘shishda xatolik: {str(e)}")

    products_list = Product.objects.select_related('category').only('id', 'name', 'category__name', 'price',
                                                                    'discount').order_by('-created_at')
    paginator = Paginator(products_list, 20)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)

    categories = Category.objects.all()
    return render(request, 'product_manage.html', {'products': products, 'categories': categories})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from decimal import Decimal


@login_required
def product_edit_view(request, pk):
    if not request.user.is_superuser:
        messages.error(request, "Bu sahifaga kirishga ruxsatingiz yo‘q.")
        return redirect('home')

    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.category_id = request.POST.get('category')

        price = request.POST.get('price')
        discount = request.POST.get('discount', '0')

        try:
            product.price = Decimal(price)
            product.discount = Decimal(discount)
        except (ValueError, TypeError) as e:
            messages.error(request, "Narx yoki chegirma noto‘g‘ri. Iltimos, to‘g‘ri raqam kiriting.")
            return render(request, 'product_edit.html', {'product': product, 'categories': Category.objects.all()})

        product.description = request.POST.get('description')

        try:
            product.save()
            messages.success(request, f"'{product.name}' mahsuloti muvaffaqiyatli yangilandi!")
            return redirect('product_manage')
        except Exception as e:
            messages.error(request, f"Mahsulotni yangilashda xatolik: {str(e)}")

    categories = Category.objects.all()
    return render(request, 'product_edit.html', {'product': product, 'categories': categories})


@login_required
def product_delete_view(request, pk):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('home')

    product = get_object_or_404(Product, pk=pk)
    product_name = product.name
    try:
        product.delete()
        messages.success(request, f"Product '{product_name}' deleted successfully!")
    except Exception as e:
        messages.error(request, f"Error deleting product: {str(e)}")
    return redirect('product_manage')


@login_required
def category_manage_view(request):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('home')

    if request.method == 'POST':
        name = request.POST.get('name')
        parent_id = request.POST.get('parent', None)

        try:
            category = Category.objects.create(
                name=name,
                parent_id=parent_id if parent_id else None
            )
            messages.success(request, f"Category '{category.name}' created successfully!")
            return redirect('category_manage')
        except Exception as e:
            messages.error(request, f"Error creating category: {str(e)}")

    categories = Category.objects.all().prefetch_related('subcategories')
    return render(request, 'category_manage.html', {'categories': categories})


@login_required
def category_edit_view(request, pk):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('home')

    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.name = request.POST.get('name')
        parent_id = request.POST.get('parent', None)
        category.parent_id = parent_id if parent_id else None

        try:
            category.save()
            messages.success(request, f"Category '{category.name}' updated successfully!")
            return redirect('category_manage')
        except Exception as e:
            messages.error(request, f"Error updating category: {str(e)}")

    categories = Category.objects.all().exclude(id=pk)
    return render(request, 'category_edit.html', {'category': category, 'categories': categories})


@login_required
def category_delete_view(request, pk):
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to access this page.")
        return redirect('home')

    category = get_object_or_404(Category, pk=pk)
    category_name = category.name
    try:
        category.delete()
        messages.success(request, f"Category '{category_name}' deleted successfully!")
    except Exception as e:
        messages.error(request, f"Error deleting category: {str(e)}")
    return redirect('category_manage')
