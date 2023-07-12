import inspect

from django.utils.decorators import method_decorator


def apply_swagger_auto_schema(decorator):
    def decorator_fn(view_cls):
        for _, method in inspect.getmembers(view_cls, predicate=inspect.isfunction):
            setattr(view_cls, method.__name__, method_decorator(decorator)(method))
        return view_cls

    return decorator_fn
