document.addEventListener('DOMContentLoaded', () => {
    const addToCartButtons = document.querySelectorAll('.add-to-cart');
    const addToFavoritesButtons = document.querySelectorAll('.add-to-favorites');
    const removeFromCartButtons = document.querySelectorAll('.remove-from-cart');
    const updateQuantityForms = document.querySelectorAll('form[action="{% url "cart" %}"]');

    // Xabarlarni tozalash funksiyasi
    const clearMessages = () => {
        const messageContainer = document.getElementById('message-container');
        if (messageContainer) {
            messageContainer.innerHTML = '';
        }
    };

    // Add to Cart funksiyasi
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
                clearMessages(); // Eski xabarlarni tozalash
                const messageContainer = document.getElementById('message-container');
                messageContainer.innerHTML = `
                    <div class="alert alert-success alert-dismissible fade show" role="alert">
                        Product added to cart!
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>`;
                setTimeout(() => {
                    const message = messageContainer.querySelector('.alert');
                    if (message) {
                        message.classList.remove('show');
                        message.classList.add('fade');
                    }
                }, 3000);
            } else {
                clearMessages();
                const messageContainer = document.getElementById('message-container');
                messageContainer.innerHTML = `
                    <div class="alert alert-danger alert-dismissible fade show" role="alert">
                        Please login to add to cart.
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>`;
                setTimeout(() => {
                    const message = messageContainer.querySelector('.alert');
                    if (message) {
                        message.classList.remove('show');
                        message.classList.add('fade');
                    }
                }, 3000);
            }
        });
    });

    // Add to Favorites funksiyasi
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
                clearMessages();
                const messageContainer = document.getElementById('message-container');
                messageContainer.innerHTML = `
                    <div class="alert alert-success alert-dismissible fade show" role="alert">
                        Product added to favorites!
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>`;
                e.target.innerHTML = '❤️';
                setTimeout(() => {
                    const message = messageContainer.querySelector('.alert');
                    if (message) {
                        message.classList.remove('show');
                        message.classList.add('fade');
                    }
                }, 3000);
            } else {
                clearMessages();
                const messageContainer = document.getElementById('message-container');
                messageContainer.innerHTML = `
                    <div class="alert alert-danger alert-dismissible fade show" role="alert">
                        Please login to add to favorites.
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>`;
                setTimeout(() => {
                    const message = messageContainer.querySelector('.alert');
                    if (message) {
                        message.classList.remove('show');
                        message.classList.add('fade');
                    }
                }, 3000);
            }
        });
    });

    // Remove from Cart funksiyasi
    removeFromCartButtons.forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            const productId = button.closest('form').querySelector('input[name="product_id"]').value;
            const response = await fetch('/cart/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
                body: new URLSearchParams({
                    'action': 'remove',
                    'product_id': productId,
                }),
            });
            if (response.ok) {
                clearMessages();
                const messageContainer = document.getElementById('message-container');
                messageContainer.innerHTML = `
                    <div class="alert alert-success alert-dismissible fade show" role="alert">
                        Product removed from cart!
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>`;
                window.location.reload();
            } else {
                clearMessages();
                const messageContainer = document.getElementById('message-container');
                messageContainer.innerHTML = `
                    <div class="alert alert-danger alert-dismissible fade show" role="alert">
                        Error removing product.
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>`;
            }
        });
    });

    // Update Quantity funksiyasi
    const updateQuantityForms = document.querySelectorAll('form[action="{% url "cart" %}"]');
    updateQuantityForms.forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const productId = form.querySelector('input[name="product_id"]').value;
            const quantity = form.querySelector('input[name="quantity"]').value;
            const action = form.querySelector('input[name="action"]').value;

            const response = await fetch('/cart/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
                body: new URLSearchParams({
                    'action': action,
                    'product_id': productId,
                    'quantity': quantity,
                }),
            });
            if (response.ok) {
                clearMessages();
                const messageContainer = document.getElementById('message-container');
                messageContainer.innerHTML = `
                    <div class="alert alert-success alert-dismissible fade show" role="alert">
                        Quantity updated!
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>`;
                window.location.reload();
            } else {
                clearMessages();
                const messageContainer = document.getElementById('message-container');
                messageContainer.innerHTML = `
                    <div class="alert alert-danger alert-dismissible fade show" role="alert">
                        Error updating quantity.
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>`;
            }
        });
    });

    function refreshToken() {
        const refreshToken = localStorage.getItem('refresh_token');
        return fetch('/api/token/refresh/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({refresh: refreshToken}),
        })
            .then(response => response.json())
            .then(data => {
                if (data.access) {
                    localStorage.setItem('access_token', data.access);
                    return data.access;
                } else {
                    throw new Error('Tokenni yangilashda xatolik yuz berdi.');
                }
            });
    }

    // Infinite Scroll funksiyasi
    let page = 1;
    let loading = false;
    const productContainer = document.querySelector('.product-container');

    if (productContainer) {
        window.addEventListener('scroll', async () => {
            if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 100 && !loading) {
                loading = true;
                productContainer.classList.add('loading');
                page++;

                let url = `?page=${page}`;
                const category = new URLSearchParams(window.location.search).get('category') || '';
                const search = new URLSearchParams(window.location.search).get('search') || '';
                if (category) url += `&category=${category}`;
                if (search) url += `&search=${search}`;

                try {
                    const response = await fetch(url);
                    if (!response.ok) {
                        loading = false;
                        productContainer.classList.remove('loading');
                        return;
                    }

                    const data = await response.text();
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(data, 'text/html');
                    const newProducts = doc.querySelector('.product-container');

                    if (newProducts && newProducts.children.length > 0) {
                        productContainer.insertAdjacentHTML('beforeend', newProducts.innerHTML);
                    } else {
                        window.removeEventListener('scroll', this);
                    }
                } catch (error) {
                    console.error('Error loading more products:', error);
                } finally {
                    loading = false;
                    productContainer.classList.remove('loading');
                }
            }
        });
    }
});

// main.js
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.querySelector('form[action="{% url "login" %}"]');
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            fetch('/login/', {
                method: 'POST',
                body: new FormData(loginForm),
            }).then(response => {
                if (response.ok) {
                    window.location.href = '/'; // Sahifani yangilash
                }
            });
        });
    }
});