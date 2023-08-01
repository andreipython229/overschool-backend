from rest_framework import serializers


class SubscriptionSerializer(serializers.Serializer):
    to_pay_sum = serializers.DecimalField(max_digits=10, decimal_places=2)
    days_interval = serializers.IntegerField(min_value=1)
    pays_count = serializers.IntegerField(min_value=1)
    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(max_length=15, required=False)

    def validate(self, data):
        user = self.context.get('user')

        if 'phone' in data:
            phone = data['phone']
        else:

            phone = user.phone_number if user else None

        data['phone'] = phone

        if user:
            data['first_name'] = user.first_name
            data['last_name'] = user.last_name
            data['email'] = user.email

        return data
