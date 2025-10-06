from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import FitnessClass, Booking
from django import forms
from .forms import FitnessClassForm
from django.contrib.admin.views.decorators import staff_member_required
import stripe
from django.conf import settings
from django.utils import timezone
import datetime

@staff_member_required
def create_class(request):
    if request.method == 'POST':
        form = FitnessClassForm(request.POST)
        if form.is_valid():
            class_date = form.cleaned_data['date']
            class_time = form.cleaned_data['time']
            class_price = form.cleaned_data['price']
            max_participants = form.cleaned_data['max_participants']

            # Combine and make timezone-aware
            class_datetime = datetime.datetime.combine(class_date, class_time)
            class_datetime = timezone.make_aware(class_datetime, timezone.get_current_timezone())

            # Validation checks
            if class_datetime < timezone.now():
                form.add_error(None, "You cannot create a class scheduled in the past.")
            elif class_price < 0:
                form.add_error('price', "Price cannot be negative.")
            elif max_participants < 1:
                form.add_error('max_participants', "There must be at least 1 spot.")
            else:
                form.save()
                return redirect('fitness_class_list')
    else:
        form = FitnessClassForm()

    return render(request, 'classes/create_class.html', {'form': form})



def fitness_class_list(request):
    classes = FitnessClass.objects.all().order_by('date', 'time')

    if request.user.is_authenticated:
        user_bookings = Booking.objects.filter(user=request.user).values_list('fitness_class_id', flat=True)
    else:
        user_bookings = []
    for fitness_class in classes:
        fitness_class.spots_left = fitness_class.max_participants - fitness_class.bookings.count()
    context = {
        'classes': classes,
        'user_bookings': user_bookings,
    }
    
    return render(request, 'classes/class_list.html', context)


def fitness_class_detail(request, class_id):
    class_obj = get_object_or_404(FitnessClass, id=class_id)
    spots_left = class_obj.max_participants - class_obj.bookings.count()

    # Check for booking success in GET params and add message
    if request.GET.get('booking') == 'success':
        messages.success(request, "Your booking and payment were successful! 🎉")

    context = {
        'class_obj': class_obj,
        'spots_left': spots_left,
    }
    return render(request, 'classes/class_detail.html', context)


@login_required
def book_fitness_class(request, class_id):
    class_obj = get_object_or_404(FitnessClass, id=class_id)

    if class_obj.bookings.count() >= class_obj.max_participants:
        messages.error(request, "Sorry, this class is fully booked.")
        return redirect('fitness_class_detail', class_id=class_id)

    if Booking.objects.filter(user=request.user, fitness_class=class_obj).exists():
        messages.info(request, "You’ve already booked this class.")
        return redirect('fitness_class_detail', class_id=class_id)

    if request.method == 'POST':
        # Store booking info in session to use after Stripe payment
        request.session['class_id'] = class_id
        return redirect('start_checkout_session')

    return render(request, 'classes/book_class.html', {'class_obj': class_obj})

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related('fitness_class')
     
    if request.GET.get('booking') == 'success':
        messages.success(request, "Your booking and payment were successful! 🎉")
    return render(request, 'classes/my_bookings.html', {'bookings': bookings})

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if request.method == 'POST':
        booking.delete()
        messages.success(request, "Booking cancelled successfully.")
    return redirect('fitness_class_list')



@login_required
def start_checkout_session(request):
    class_id = request.session.get('class_id')
    class_obj = get_object_or_404(FitnessClass, id=class_id)

    stripe.api_key = settings.STRIPE_SECRET_KEY

    success_url = request.build_absolute_uri(f'/classes/{class_id}/?booking=success')

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'unit_amount': int(class_obj.price * 100),
                'product_data': {'name': class_obj.title},
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=success_url,
        cancel_url=request.build_absolute_uri(f'/classes/{class_id}/'),
        metadata={
            'user_id': request.user.id,
            'class_id': class_id
        }
    )

    return redirect(session.url, code=303)

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WH_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session['metadata']['user_id']
        class_id = session['metadata']['class_id']

        from django.contrib.auth.models import User
        try:
            user = User.objects.get(id=user_id)
            class_obj = FitnessClass.objects.get(id=class_id)

            # Prevent overbooking & duplicates
            if class_obj.bookings.count() < class_obj.max_participants and \
               not Booking.objects.filter(user=user, fitness_class=class_obj).exists():
                Booking.objects.create(user=user, fitness_class=class_obj)
        except Exception:
            pass

    return HttpResponse(status=200)
