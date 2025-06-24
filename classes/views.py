import stripe
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import FitnessClass, Booking
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from .forms import FitnessClassForm  # we will create this form next

@staff_member_required
def create_class(request):
    if request.method == 'POST':
        form = FitnessClassForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('class_list')
    else:
        form = FitnessClassForm()
    return render(request, 'classes/create_class.html', {'form': form})



stripe.api_key = settings.STRIPE_SECRET_KEY
@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related('fitness_class')
    return render(request, 'classes/my_bookings.html', {'bookings': bookings})



def class_list(request):
    classes = FitnessClass.objects.all()

    # Get list of class IDs that the user has booked
    booked_class_ids = []
    if request.user.is_authenticated:
        booked_class_ids = Booking.objects.filter(user=request.user).values_list('fitness_class_id', flat=True)
    return render(request, 'classes/class_list.html', {
        'classes': classes,
        'booked_class_ids': booked_class_ids,
    })


def class_detail(request, class_id):
    fitness_class = get_object_or_404(FitnessClass, id=class_id)
    booked = False
    if request.user.is_authenticated:
        booked = Booking.objects.filter(user=request.user, fitness_class=fitness_class).exists()
    spots_left = fitness_class.max_participants - fitness_class.bookings.count()
    return render(request, 'classes/class_detail.html', {
        'class': fitness_class,
        'booked': booked,
        'spots_left': spots_left,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
    })


@csrf_exempt
def create_subscription_checkout_session(request, class_id):
    if request.method == "POST":
        class_id = request.POST.get("class_id")
        user = request.user

        try:
            checkout_session = stripe.checkout.Session.create(
                success_url = f'http://127.0.0.1:8000/classes/subscription_success/?class_id={class_id}',
                cancel_url=f'http://127.0.0.1:8000/classes/subscription_cancel/?class_id={class_id}',
                mode="subscription",
                line_items=[
                    {
                        "price": 'price_1Rd94oPwYr2TRIKdsLwzMge0',
                        "quantity": 1,
                    }
                ],
                metadata={
                    "user_id": user.id,
                    "class_id": class_id,
                    "payment_type": "subscription",
                },
            )
            return redirect(checkout_session.url)
        except Exception as e:
            return HttpResponse(f"Error creating subscription session: {str(e)}", status=500)


def payment_success(request):
    # Extract info from GET params or session (you can customize this)
    class_id = request.GET.get('class_id')

    if not class_id:
        messages.error(request, "Invalid booking confirmation.")
        return redirect('class_list')

    fitness_class = get_object_or_404(FitnessClass, id=class_id)

    # Check if user already booked
    if Booking.objects.filter(user=request.user, fitness_class=fitness_class).exists():
        messages.info(request, "You have already booked this class.")
        return redirect('my_bookings')

    # Check if class is full
    if fitness_class.bookings.count() >= fitness_class.max_participants:
        messages.error(request, "Sorry, this class is fully booked.")
        return redirect('class_list')

    # Create the booking after payment success
    Booking.objects.create(user=request.user, fitness_class=fitness_class)
    messages.success(request, f"You successfully booked {fitness_class.title}!")

    return redirect('my_bookings')




stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def create_checkout_session(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    class_id = request.POST.get('class_id')
    fitness_class = get_object_or_404(FitnessClass, id=class_id)

    # Check if class is fully booked
    if fitness_class.bookings.count() >= fitness_class.max_participants:
        messages.error(request, "This class is fully booked.")
        return redirect('class_detail', class_id=class_id)

    # Check if user already booked the class
    if Booking.objects.filter(user=request.user, fitness_class=fitness_class).exists():
        messages.warning(request, "You already booked this class.")
        return redirect('class_detail', class_id=class_id)

    domain_url = request.build_absolute_uri('/')[:-1]
    success_url = domain_url + f'/classes/success?class_id={fitness_class.id}'
    cancel_url = domain_url + f'/classes/cancel'

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            customer_email=request.user.email,
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': 1500,  # $15 in cents
                    'product_data': {
                        'name': fitness_class.title,
                        'description': f"Class on {fitness_class.date} at {fitness_class.time}"
                    },
                },
                'quantity': 1,
            }],
            metadata={
                'user_id': request.user.id,
                'class_id': fitness_class.id,
                'payment_type': 'single_class',
            },
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return redirect(checkout_session.url)
    except Exception as e:
        messages.error(request, f"Error creating checkout session: {str(e)}")
        return redirect('class_detail', class_id=class_id)


@login_required
def create_subscription_session(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=400)

    domain_url = request.build_absolute_uri('/')[:-1]

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='subscription',
            customer_email=request.user.email,
            line_items=[{
                'price': 'price_1Rd94oPwYr2TRIKdsLwzMge0',  # Replace with your Stripe subscription price ID
                'quantity': 1,
            }],
            metadata={
                'user_id': request.user.id,
                'payment_type': 'subscription',
            },
            success_url=domain_url + '/classes/subscription_success',
            cancel_url=domain_url + '/classes/subscription_cancel',
        )
        return redirect(checkout_session.url)
    except Exception as e:
        messages.error(request, f"Error creating subscription session: {str(e)}")
        return redirect('class_list')


@login_required
def booking_success(request):
    return render(request, 'classes/booking_success.html')


@login_required
def subscription_success(request):
    return render(request, 'classes/subscription_success.html')


def booking_cancel(request):
    return render(request, 'classes/booking_cancel.html')


def subscription_cancel(request):
    return render(request, 'classes/subscription_cancel.html')

@login_required
def book_class(request, class_id):
    fitness_class = get_object_or_404(FitnessClass, id=class_id)

    # Check if booking already exists
    if Booking.objects.filter(user=request.user, fitness_class=fitness_class).exists():
        messages.warning(request, "You have already booked this class.")
        return redirect('book_success')

    # Check spots available
    if fitness_class.bookings.count() >= fitness_class.max_participants:
        messages.error(request, "This class is fully booked.")
        return redirect('class_detail', class_id=class_id)

    # Create booking
    Booking.objects.create(user=request.user, fitness_class=fitness_class)
    messages.success(request, "Class booked successfully!")
    return redirect('book_success')


@login_required
def cancel_booking(request, class_id):
    fitness_class = get_object_or_404(FitnessClass, id=class_id)
    booking = Booking.objects.filter(user=request.user, fitness_class=fitness_class).first()
    if booking:
        booking.delete()
        messages.success(request, "Booking cancelled.")
    else:
        messages.warning(request, "You have no booking for this class.")
    return redirect('class_list')


stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = settings.STRIPE_WH_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Metadata sent in checkout session creation
        user_id = session.get('metadata', {}).get('user_id')
        class_id = session.get('metadata', {}).get('class_id')

        if user_id and class_id:
            try:
                user = User.objects.get(pk=user_id)
                fitness_class = FitnessClass.objects.get(pk=class_id)
            except (User.DoesNotExist, FitnessClass.DoesNotExist):
                return HttpResponse(status=400)

            # Prevent duplicate bookings
            if not Booking.objects.filter(user=user, fitness_class=fitness_class).exists():
                Booking.objects.create(user=user, fitness_class=fitness_class)

    return HttpResponse(status=200)
