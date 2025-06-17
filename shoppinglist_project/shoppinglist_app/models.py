from django.contrib.auth.models import User
from django.db import models

class Item(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # ✅ Add this line
    name = models.CharField(max_length=200)
    quantity = models.IntegerField(default=1)
    category = models.CharField(max_length=100, blank=True)
    purchased = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=50, default='manual') 

    def __str__(self):
        return self.name

class OCRUpload(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    extracted_items = models.JSONField()  # or TextField if you're saving as text
