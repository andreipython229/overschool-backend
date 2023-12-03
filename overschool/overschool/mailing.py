from django.core.mail.backends.smtp import EmailBackend
from django.core.mail.utils import DNS_NAME


class MyEmailBackend(EmailBackend):
    def open(self):
        if self.connection:
            return False

        connection_params = {"local_hostname": DNS_NAME.get_fqdn()}
        if self.timeout is not None:
            connection_params["timeout"] = self.timeout
        try:
            self.connection = self.connection_class(
                self.host, self.port, **connection_params
            )

            if not self.use_ssl and self.use_tls:
                self.connection.starttls(
                    keyfile=self.ssl_keyfile, certfile=self.ssl_certfile
                )
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except OSError:
            if not self.fail_silently:
                raise
