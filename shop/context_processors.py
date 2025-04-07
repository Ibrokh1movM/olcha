from .models import Cart


def cart_items(request):
    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)
        cart_count = cart_items.count()
        return {'cart_items': cart_items, 'cart_count': cart_count}
    return {'cart_items': [], 'cart_count': 0}
