/*
    Stripe payment flow for class bookings
    Based on: https://stripe.com/docs/payments/accept-a-payment
*/
$(document).ready(function() {

    // 1. Initialize variables from hidden HTML elements
    //var stripePublicKey = $('#id_stripe_public_key').text().slice(1, -1);
    //var clientSecret = $('#id_client_secret').text().slice(1, -1);
    var stripePublicKey = JSON.parse(document.getElementById('id_stripe_public_key').textContent);
    var clientSecret = JSON.parse(document.getElementById('id_client_secret').textContent);

    
    // CRITICAL: Check for key existence and EXIT EARLY if missing
    if (!stripePublicKey || !clientSecret || stripePublicKey.length < 5) {
        // Log an error to the console for debugging
        console.error("Stripe keys not correctly loaded. Check element IDs and slicing.");
        // Hide the payment form so the user can't proceed
        $('#payment-form').hide();
        // You might want to display a user-friendly error message here as well
        $('#card-errors').html('Payment cannot be processed. Please refresh or try again later.');
        return; 
    }

    // 2. Initialize Stripe ONLY if keys are present
    var stripe = Stripe(stripePublicKey);
    var elements = stripe.elements();

    // 3. Define Card Element Style
    var style = {
        base: {
            color: '#000',
            fontFamily: 'Lato, sans-serif',
            fontSmoothing: 'antialiased',
            fontSize: '16px',
            '::placeholder': {
                color: '#aab7c4'
            }
        },
        invalid: {
            color: '#dc3545',
            iconColor: '#dc3545'
        }
    };

    // 4. Create and Mount the Card Element
    var card = elements.create('card', { style: style });
    // This line injects the actual card input fields into the HTML div
    card.mount('#card-element'); 

    // 5. Handle realtime validation errors on the card element
    card.addEventListener('change', function (event) {
        var errorDiv = document.getElementById('card-errors');
        if (event.error) {
            var html = `
                <span class="icon" role="alert">
                    <i class="fas fa-times"></i>
                </span>
                <span>${event.error.message}</span>
            `;
            $(errorDiv).html(html);
        } else {
            errorDiv.textContent = '';
        }
    });

    // 6. Handle form submit
    var form = document.getElementById('payment-form');

    form.addEventListener('submit', function (ev) {
        ev.preventDefault();
        card.update({ 'disabled': true });
        $('#submit-button').attr('disabled', true);
        
        // Use standard fadeToggle for consistency
        $('#payment-form').fadeToggle(100);
        $('#loading-overlay').fadeToggle(100);

        // Get CSRF token
        var csrfToken = $('input[name="csrfmiddlewaretoken"]').val();
        var postData = {
            'csrfmiddlewaretoken': csrfToken,
            'client_secret': clientSecret,
        };
        var url = '/classes/cache_class_payment_data/';

        $.post(url, postData).done(function () {
            stripe.confirmCardPayment(clientSecret, {
                payment_method: {
                    card: card,
                },
            }).then(function (result) {
                if (result.error) {
                    var errorDiv = document.getElementById('card-errors');
                    var html = `
                        <span class="icon" role="alert">
                            <i class="fas fa-times"></i>
                        </span>
                        <span>${result.error.message}</span>`;
                    $(errorDiv).html(html);

                    // Re-enable form
                    $('#payment-form').fadeToggle(100);
                    $('#loading-overlay').fadeToggle(100);
                    card.update({ 'disabled': false });
                    $('#submit-button').attr('disabled', false);
                } else {
                    if (result.paymentIntent.status === 'succeeded') {
                        // Redirect to my_bookings page after successful payment
                        window.location.href = myBookingsUrl;
                    }
                }
            });
        }).fail(function () {
            // Reload if there's a Django error message
            location.reload();
        });
    });
});