from django.shortcuts import render
from .models import Plan

def plans_view(request):
    """Plans selection view."""
    plans = Plan.objects.filter(is_active=True).order_by('sort_order', 'price')
    
    context = {
        'plans': plans,
    }
    
    return render(request, 'subscriptions/plans.html', context)
# Create your views here.
