// static/js/main.js
document.addEventListener('DOMContentLoaded', () => {
    const addToCartButtons = document.querySelectorAll('.add-to-cart');
    const addToFavoritesButtons = document.querySelectorAll('.add-to-favorites');
    const removeFromCartButtons = document.querySelectorAll('.remove-from-cart');

    addToCartButtons.forEach(button => {
        button.addEventListener('click', async (e) => {
            const productId = e.target.dataset.productId;
            const response = await fetch('/api/cart/add_to_cart/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + localStorage.getItem('access_token'),
                },
                body: JSON.stringify({product_id: productId, quantity: 1}),
            });
            if (response.ok) {
                alert('Product added to cart!');
                window.location.reload();
            } else {
                alert('Please login to add to cart.');
            }
        });
    });

    addToFavoritesButtons.forEach(button => {
        button.addEventListener('click', async (e) => {
            const productId = e.target.dataset.productId;
            const response = await fetch(`/api/products/${productId}/add_to_favorites/`, {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + localStorage.getItem('access_token'),
                },
            });
            if (response.ok) {
                e.target.innerHTML = '❤️';
            } else {
                alert('Please login to add to favorites.');
            }
        });
    });

    removeFromCartButtons.forEach(button => {
        button.addEventListener('click', async (e) => {
            const cartId = e.target.dataset.cartId;
            const response = await fetch(`/api/cart/${cartId}/`, {
                method: 'DELETE',
                headers: {
                    'Authorization': 'Bearer ' + localStorage.getItem('access_token'),
                },
            });
            if (response.ok) {
                alert('Product removed from cart!');
                window.location.reload();
            } else {
                alert('Error removing product.');
            }
        });
    });
});