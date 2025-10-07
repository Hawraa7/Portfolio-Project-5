document.addEventListener("DOMContentLoaded", function() {
    // --- Get keys safely ---
    const stripePublicKey = JSON.parse(document.getElementById('id_stripe_public_key').textContent);
    const clientSecret = JSON.parse(document.getElementById('id_client_secret').textContent);

    console.log("Stripe public key:", stripePublicKey);
    console.log("Client secret:", clientSecret);

    // --- Initialize Stripe ---
    const stripe = Stripe(stripePublicKey);
    const elements = stripe.elements();

    const style = {
        base: {
            color: '#000',
            fontFamily: '"Lato", sans-serif',
            fontSmoothing: 'antialiased',
            fontSize: '16px',
            '::placeholder': { color: '#888' }
        },
        invalid: { color: '#dc3545', iconColor: '#dc3545' }
    };

    const card = elements.create('card', { style });
    card.mount('#card-element');

    // --- Display card errors ---
    card.on('change', function(event) {
        const errorDiv = document.getElementById('card-errors');
        errorDiv.textContent = event.error ? event.error.message : '';
    });

    // --- Form submission ---
    const form = document.getElementById('payment-form');
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        document.getElementById('submit-button').disabled = true;
        document.getElementById('loading-overlay').style.display = 'block';

        const { error, paymentIntent } = await stripe.confirmCardPayment(clientSecret, {
            payment_method: {
                card: card,
                billing_details: {
                    name: form.querySelector('input[name="full_name"]')?.value || 'Zouzou Fitness User',
                }
            }
        });

        if (error) {
            document.getElementById('card-errors').textContent = error.message;
            document.getElementById('submit-button').disabled = false;
            document.getElementById('loading-overlay').style.display = 'none';
        } else if (paymentIntent && paymentIntent.status === 'succeeded') {
            window.location.href = typeof myBookingsUrl !== "undefined" ? myBookingsUrl : "/";
        }
    });
});
