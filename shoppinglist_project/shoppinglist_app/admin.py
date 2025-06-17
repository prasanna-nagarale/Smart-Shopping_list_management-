from django.contrib import admin
from .models import Item  # replace Item with your actual model name


class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'category', 'user')  # show user in list
    list_filter = ('user',)  # enable "By user" filter

admin.site.register(Item, ItemAdmin)
  # replace Item with your actual model name
