def static_lazy(path):
    from django.templatetags.static import static
    from django.utils.functional import lazy
    return lazy(lambda: static(path), str)()


if __name__ == "__main__":
    print(static_lazy('css/fonts.css'))