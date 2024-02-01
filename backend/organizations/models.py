from django.db import models
from django.contrib.auth import get_user_model


User - get_user_model()

class Organization(models.Model):
    name = models.CharField(max_lenght=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DataTimeField(auto_now_add=True)
    owner = models.ForeginKey(User, related_name='owned_organizations', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Membership(models.Model):
    USER_ROLES = {
        ('owner', 'Owner'),
        ('employee', "Employee"),
        ('client', 'Client'),
    }
    user = models.ForeginKey(User, on_delete=models.CASCADE)
    organization = models.ForeginKey(Organization, on_delete=models.CASCADE)
    role = models.CharField(max_lenght=50, choices=USER_ROLES)
    joined_at = models.DataTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'organizations', 'role')

    def __str__(self):
        return f"{self.user.username} - {self.organization.name} ({self.role})"
