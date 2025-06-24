from django.db import models
from django.contrib.auth.models import User

class FitnessClass(models.Model):
    title = models.CharField(max_length=255)
    instructor = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    description = models.TextField()
    max_participants = models.PositiveIntegerField()

    def __str__(self):
        return self.title

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    fitness_class = models.ForeignKey(FitnessClass, on_delete=models.CASCADE, related_name='bookings')
    booked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} booking for {self.fitness_class.title}'
