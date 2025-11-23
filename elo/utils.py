from django.core.paginator import Paginator

class Navigation:
    def __init__(self, pages: Paginator, page_number: int):
        self.pages = pages
        self.current_page_number = page_number

    def needs_previous(self):
        return self.current_page_number > 1

    def needs_previous2(self):
        return self.current_page_number > 2

    def needs_dots_before(self):
        return self.current_page_number > 3

    def needs_dots_after(self):
        return self.pages.num_pages - self.current_page_number >= 3

    def needs_next(self):
        return self.pages.num_pages > self.current_page_number

    def needs_next2(self):
        return self.pages.num_pages -1 > self.current_page_number

    def previous_page_number(self):
        return self.current_page_number - 1

    def previous2_page_number(self):
        return self.current_page_number - 2

    def next_page_number(self):
        return self.current_page_number + 1

    def next2_page_number(self):
        return self.current_page_number + 2