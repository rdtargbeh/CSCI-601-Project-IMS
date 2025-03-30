from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum
from .models import Inventory, Product

@receiver(post_save, sender=Inventory)
def update_product_stock(sender, instance, **kwargs):
    total_stock = instance.product.inventories.aggregate(total_stock=Sum('quantity'))['total_stock'] or 0
    Product.objects.filter(pk=instance.product.pk).update(stock=total_stock)
