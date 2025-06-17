from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Item, OCRUpload
from collections import Counter
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.http import JsonResponse, HttpResponse
from django.template.loader import get_template
from PIL import Image
import pytesseract
import io
import re
from django.db.models import Q
from xhtml2pdf import pisa
from django.utils.timezone import localtime
from django.db.models import Count
import json
from django.http import JsonResponse


# Tesseract path (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def landing_page(request):
    return render(request, 'landing.html')


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            return redirect('add_item')
    return render(request, 'register.html')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Item
from PIL import Image
import pytesseract

@login_required
def add_item(request):
    context = {}
    print("[DEBUG] User:", request.user)

    if request.method == 'POST':
        print("[DEBUG] POST received:", request.POST)

        # OCR form submission
        if 'ocr_submit' in request.POST and request.FILES.get('ocr_image'):
            image = request.FILES['ocr_image']
            try:
                img = Image.open(image)
                extracted_text = pytesseract.image_to_string(img)
                items = [line.strip() for line in extracted_text.split('\n') if line.strip()]
                context['ocr_items'] = items
                print(f"[DEBUG] OCR extracted: {items}")
            except Exception as e:
                print("[ERROR] OCR processing failed:", e)

        # Manual form submission
        else:
            name = request.POST.get('name', '').strip()
            category = request.POST.get('category', '').strip()
            quantity = int(request.POST.get('quantity', 1))
            purchased = request.POST.get('purchased') == 'True'

            if name and category:
                try:
                    Item.objects.create(
                        user=request.user,
                        name=name,
                        category=category,
                        quantity=quantity,
                        purchased=purchased
                    )
                    print(f"[DEBUG] Item saved: {name}, {category}, {quantity}, purchased={purchased}")
                    return redirect('item_list')
                except Exception as e:
                    print("[ERROR] Failed to save item:", e)
            else:
                print("[WARNING] Missing fields in manual form submission.")

    return render(request, 'add_item.html', context)

from django.db.models import Q

@login_required
def item_list(request):
    query = request.GET.get('q', '')
    print("[DEBUG] Search query:", query)

    if query:
        items_purchased = Item.objects.filter(
            user=request.user,
            purchased=True
        ).filter(
            Q(name__icontains=query) | Q(category__icontains=query)
        )
        items_pending = Item.objects.filter(
            user=request.user,
            purchased=False
        ).filter(
            Q(name__icontains=query) | Q(category__icontains=query)
        )
    else:
        items_purchased = Item.objects.filter(user=request.user, purchased=True)
        items_pending = Item.objects.filter(user=request.user, purchased=False)

    print(f"[DEBUG] Purchased: {items_purchased.count()}, Pending: {items_pending.count()}")

    return render(request, 'item_list.html', {
        'items_purchased': items_purchased,
        'items_pending': items_pending,
    })


@login_required
def edit_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, user=request.user)
    if request.method == 'POST':
        item.name = request.POST['name']
        item.quantity = request.POST['quantity']
        item.category = request.POST['category']
        item.notes = request.POST['notes']
        item.purchased = 'purchased' in request.POST
        try:
            item.save()
            print(f"[DEBUG] Updated item {item.id}")
        except Exception as e:
            print("[ERROR] Failed to update item:", e)
        return redirect('item_list')
    return render(request, 'edit_item.html', {'item': item})


@login_required
def delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, user=request.user)
    item.delete()
    return redirect('item_list')


@login_required
def export_pdf(request):
    items = Item.objects.filter(user=request.user)
    template = get_template('item_pdf.html')
    html = template.render({'items': items})
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="shopping_list.pdf"'
    pisa.CreatePDF(io.BytesIO(html.encode('UTF-8')), dest=response)
    return response


@login_required
def ocr_upload(request):
    if request.method == 'POST' and request.FILES.get('ocr_image'):
        image_file = request.FILES['ocr_image']
        path = default_storage.save('ocr_images/' + image_file.name, image_file)
        full_path = default_storage.path(path)
        img = Image.open(full_path)
        text = pytesseract.image_to_string(img)
        items = [re.sub(r'[^a-zA-Z ]+', '', line).strip().lower() for line in text.splitlines() if line.strip()]
        
        # Save items to database
        for item in items:
            print(f"Saving item: {item}")
            Item.objects.create(
                name=item,
                category='Unknown',
                quantity=1,
                user=request.user,
                source='OCR'
            )

        # Also keep them in session (optional)
        request.session['ocr_items'] = items
        
        return redirect('ocr_result')
    return render(request, 'ocr_upload.html')


@login_required
def ocr_result(request):
    items = request.session.get('ocr_items', [])
    return render(request, 'ocr_result.html', {'items': items})



# Admin Check
def is_admin(user):
    return user.is_superuser or user.groups.filter(name='Admin').exists()


@user_passes_test(is_admin)
@login_required
def dashboard(request):
    user = request.user
    items = Item.objects.filter(user=user)

    purchased_items_list = items.filter(purchased=True)
    pending_items_list = items.filter(purchased=False)

    total_items = items.count()
    purchased_count = purchased_items_list.count()
    pending_count = pending_items_list.count()

    category_data = items.values('category').annotate(count=Count('id')).order_by()
    labels = [entry['category'] for entry in category_data]
    data = [entry['count'] for entry in category_data]

    context = {
        'total_items': total_items,
        'purchased_items': purchased_count,
        'pending_items': pending_count,
        'labels': json.dumps(labels),
        'data': json.dumps(data),
        'purchased_items_list': purchased_items_list,
        'pending_items_list': pending_items_list,
    }
    return render(request, 'dashboard.html', context)

from django.shortcuts import redirect, get_object_or_404
from .models import Item

@login_required
def mark_purchased(request, item_id):
    item = get_object_or_404(Item, id=item_id, user=request.user)
    item.purchased = True
    item.save()
    return redirect('item_list')

from django.shortcuts import redirect, get_object_or_404
from .models import Item
from django.contrib.auth.decorators import login_required

@login_required
def mark_pending(request, item_id):
    item = get_object_or_404(Item, id=item_id, user=request.user)
    item.purchased = False
    item.save()
    return redirect('item_list')


@login_required
def add_item_ajax(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category = request.POST.get('category', '')
        quantity = request.POST.get('quantity', '1')

        if name:
            Item.objects.create(
                user=request.user,
                name=name,
                category=category,
                quantity=quantity
            )
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Missing name'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


@login_required
def view_ocr_uploads(request):
    ocr_items = Item.objects.filter(user=request.user, source='OCR').order_by('-id')
    return render(request, 'ocr_uploaded_items.html', {'uploads': ocr_items})
