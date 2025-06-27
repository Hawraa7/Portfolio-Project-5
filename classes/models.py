from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta, datetime, time

class FitnessClass(models.Model):
    title = models.CharField(max_length=100, default="Untitled Class")
    instructor = models.CharField(max_length=254)
    date = models.DateTimeField(default=datetime.today) 
    time = models.TimeField(default=datetime.now)
    duration = models.DurationField(default=timedelta(minutes=60)) 
    description = models.TextField()
    max_participants = models.PositiveIntegerField(default=15)
    price = models.DecimalField(max_digits=6, decimal_places=2)


    def __str__(self):
        return f"{self.title} - {self.date} {self.time}"

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    fitness_class = models.ForeignKey(FitnessClass, on_delete=models.CASCADE, related_name='bookings')
    booked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} booking for {self.fitness_class.title}'
