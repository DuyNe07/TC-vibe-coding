"""APP REGISTRY - every app (feature) MUST be listed here, under the URL prefix of the person who builds it.

    ("anhthy", "leave_request")   ->  /anhthy-leave-request   (landing page)
                                      /anhthy-leave-request-<page slug>   (other pages)

Read by the frontend (router: URLs, Home cards, menu) and the backend (gateway: an unregistered app's controller
refuses every call). An app missing from this list is NOT shown and `scripts/check.py` fails until it is added.
Prefix: the builder's short name, lower-case letters and digits only (e.g. "anhthy", "duyne07", "xuan2894").
One line per app, so branches never conflict. `scripts/new_feature.py` adds the line; never remove another app's line.
"""

APPS: tuple[tuple[str, str], ...] = (
    # (url prefix, feature key)
    ("duyne07", "sample_product_import"),
    ("xuan2894", "yarn_costing"),
)
