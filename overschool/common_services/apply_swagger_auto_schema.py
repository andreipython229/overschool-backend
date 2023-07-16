import inspect

from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema


def apply_swagger_auto_schema(tags=[], default_schema=None, excluded_methods=[]):

    exclude = [
        "__init__",
        "_allowed_methods",
        "_clean_data",
        "_get_ip_address",
        "_get_response_ms",
        "_get_user",
        "_get_view_method",
        "_get_view_name",
        "check_object_permissions",
        "check_permissions",
        "check_throttles",
        "determine_version",
        "dispatch",
        "filter_queryset",
        "finalize_response",
        "get_authenticate_header",
        "get_authenticators",
        "get_content_negotiator",
        "get_exception_handler",
        "get_exception_handler_context",
        "get_extra_action_url_map",
        "get_format_suffix",
        "get_object",
        "get_paginated_response",
        "get_parser_context",
        "get_parsers",
        "get_permissions",
        "get_queryset",
        "get_renderer_context",
        "get_renderers",
        "get_serializer",
        "get_serializer_class",
        "get_serializer_context",
        "get_success_headers",
        "get_throttles",
        "get_view_description",
        "get_view_name",
        "handle_exception",
        "handle_log",
        "http_method_not_allowed",
        "initial",
        "initialize_request",
        "options",
        "paginate_queryset",
        "perform_authentication",
        "perform_content_negotiation",
        "perform_create",
        "perform_destroy",
        "perform_update",
        "permission_denied",
        "raise_uncaught_exception",
        "reverse_action",
        "setup",
        "should_log",
        "throttled",
    ]

    exclude.extend(excluded_methods) if excluded_methods else None

    if default_schema == None:
        tags = (
            [
                "default_tags",
            ]
            if not tags
            else tags
        )
        default_schema = swagger_auto_schema(tags=tags)

    def decorator_fn(view_cls):
        for _, method in inspect.getmembers(view_cls, predicate=inspect.isfunction):
            if method.__name__ not in exclude:
                setattr(
                    view_cls, method.__name__, method_decorator(default_schema)(method)
                )
        return view_cls

    return decorator_fn
