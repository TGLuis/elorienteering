from django.core.cache import cache
from elo.models import PageView

class PageViewMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        path = request.path
        if "api" in path or "admin" in path:
            return response

        # Check if the count is in the cache
        page_views = cache.get(path)

        if page_views is None:
            # If not in cache, get the count from the database and update the cache
            page_view, created = PageView.objects.get_or_create(path=path)
            page_views = page_view.count
            cache.set(path, page_views)

        # Increment the count in the cache and update the database
        page_views += 1
        cache.set(path, page_views)
        PageView.objects.filter(path=path).update(count=page_views)

        return response