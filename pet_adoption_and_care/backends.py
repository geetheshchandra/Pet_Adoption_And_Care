from django.contrib.auth.backends import ModelBackend
from .models import Manager

class ManagerBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Attempt to retrieve the Manager with the given manager_id
            manager = Manager.objects.get(manager_id=username)
            # Check if the password matches
            if manager.man_pw == password:
                return manager
        except Manager.DoesNotExist:
            return None