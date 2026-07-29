from django.db import models


class KitchenSink(models.Model):
    """One column per built-in field type with a non-STRICT default decltype."""

    big_integer = models.BigIntegerField(null=True)
    binary = models.BinaryField(null=True)
    boolean = models.BooleanField(default=False)
    char = models.CharField(max_length=100)
    date = models.DateField(null=True)
    datetime = models.DateTimeField(null=True)
    decimal = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    duration = models.DurationField(null=True)
    floating = models.FloatField(null=True)
    generic_ip = models.GenericIPAddressField(null=True)
    integer = models.IntegerField(null=True)
    json = models.JSONField(null=True)
    positive_big = models.PositiveBigIntegerField(null=True)
    positive_int = models.PositiveIntegerField(null=True)
    positive_small = models.PositiveSmallIntegerField(null=True)
    slug = models.SlugField(null=True)
    small_integer = models.SmallIntegerField(null=True)
    text = models.TextField(null=True)
    time = models.TimeField(null=True)
    uuid = models.UUIDField(null=True)
    parent = models.ForeignKey(
        "self", null=True, on_delete=models.SET_NULL, related_name="children"
    )
    siblings = models.ManyToManyField("self")
