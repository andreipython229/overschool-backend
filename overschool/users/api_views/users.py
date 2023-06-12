from common_services.mixins import LoggingMixin, WithHeadersViewSet
# from django.contrib.auth.decorators import login_required
# from django.shortcuts import render
from rest_framework import viewsets
from users.models import User
from users.permissions import OwnerUserPermissions
from users.serializers import UserSerializer


# from users.services import SenderServiceMixin


class UserViewSet(LoggingMixin, WithHeadersViewSet, viewsets.ModelViewSet):
    '''Возвращаем только объекты пользователя, сделавшего запрос\n
    Возвращаем только объекты пользователя, сделавшего запрос'''
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [OwnerUserPermissions]
    http_method_names = ["get", "head"]

    def get_queryset(self):
        # Возвращаем только объекты пользователя, сделавшего запрос
        return User.objects.filter(id=self.request.user.id)

    # @login_required
    # def confirm_code_view(self, request):
    #     user = request.user
    #     if request.method == 'POST':
    #         code = request.POST.get('code')
    #         sender_service = SenderServiceMixin()
    #         if sender_service.confirm_code(code, user):
    #             # Код подтверждения верный, устанавливаем пользователя как аутентифицированного
    #             user.is_authenticated = True
    #             user.save()
    #             return render(request, 'success.html')
    #         else:
    #             # Код подтверждения неверный, отображаем сообщение об ошибке
    #             error_message = 'Invalid confirmation code'
    #             return render(request, 'confirm_code.html', {'error_message': error_message})
    #     else:
    #         return render(request, 'confirm_code.html')
