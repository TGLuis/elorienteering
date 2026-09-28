from django.core.cache import cache
from elo.models import PageView

class PageViewMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def register_error_code(self, error_code):
        path = f"ERROR-{error_code}"
        self.register_path(path)

    def register_path(self, path):
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

    def register_path_no_cache(self, path):
        page_view, created = PageView.objects.get_or_create(path=path)
        PageView.objects.filter(path=path).update(count=page_view.count+1)

    def register_runner(self, runner_id):
        path = f"RUNNER-{runner_id}"
        self.register_path_no_cache(path)


    def __call__(self, request):
        response = self.get_response(request)

        if response.status_code != 200:
            self.register_error_code(response.status_code)
            return response

        if "elo/runner" in request.path:
            self.register_runner(request.GET.get("id"))

        self.register_path(request.path)
        return response