from django.db import models

class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_minutes = models.PositiveSmallIntegerField(default=60)
    image = models.ImageField(upload_to='services/', blank=True, null=True)

    @property
    def default_image(self):
        service_name = self.name.casefold()
        image_by_keyword = (
            (('facial', 'skin'), 'facial.jpg'),
            (('braid',), 'braiding.jpg'),
            (('treatment',), 'hair-treatment.jpg'),
            (('haircut', 'hair cut', 'styling'), 'haircut.jpg'),
            (('manicure', 'nail'), 'manicure.jpg'),
            (('pedicure', 'foot'), 'pedicure.jpg'),
        )
        for keywords, image_name in image_by_keyword:
            if any(keyword in service_name for keyword in keywords):
                return f'images/services/{image_name}'
        return 'images/services/salon-service.jpg'

    def __str__(self):
        return self.name

