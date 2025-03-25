# Create your models here.
from django.db import models
from django.contrib.auth.models import User  # Assuming you have user authentication

class QuizScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.CharField(max_length=255)
    score = models.IntegerField()
    total_questions = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.topic} - Score: {self.score}/{self.total_questions}"