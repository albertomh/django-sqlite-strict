from django import VERSION as DJANGO_VERSION
from django.db import models
from django.db.models.functions import ExtractYear

from django_sqlite_strict.fields import StrictDecimalField


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


class Legacy(models.Model):
    """Rebuilt from a hand-made non-STRICT table in the conversion test."""

    name = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)


class Order(models.Model):
    """Exercises StrictDecimalField's integer minor-unit storage."""

    total_price = StrictDecimalField(max_digits=18, decimal_places=2, null=True)


class Indexed(models.Model):
    email = models.EmailField(db_index=True)


class Author(models.Model):
    name = models.CharField(max_length=100, unique=True)


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)


class Book(models.Model):
    title = models.CharField(max_length=50, unique=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    published = models.DateField(null=True)
    tags = models.ManyToManyField(Tag, related_name="books")


if DJANGO_VERSION >= (5, 0):

    class GeneratedBook(models.Model):
        author = models.ForeignKey(
            Author,
            on_delete=models.CASCADE,
        )
        published = models.DateField()

        year = models.GeneratedField(
            expression=ExtractYear("published"),
            output_field=models.IntegerField(),
            db_persist=True,
        )
