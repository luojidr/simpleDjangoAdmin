import logging
from collections import OrderedDict

from django.core.paginator import Page
from django.core.paginator import InvalidPage
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

logger = logging.getLogger("django")


class Pagination(PageNumberPagination):
    page_query_param = 'page'
    page_size_query_param = "page_size"

    page_size = 10
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        """
        Paginate a queryset if required, either returning a
        page object, or `None` if pagination is not configured for this view.
        """
        page_size = self.get_page_size(request)
        if not page_size:
            return None

        paginator = self.django_paginator_class(queryset, page_size)
        page_number = request.query_params.get(self.page_query_param, 1)
        if page_number in self.last_page_strings:
            page_number = paginator.num_pages

        try:
            self.page = paginator.page(page_number)
        except InvalidPage as exc:
            # 没有数据时，无需返回异常
            msg = self.invalid_page_message.format(
                page_number=page_number, message=str(exc)
            )
            logger.warning(msg)

            number = int(page_number)
            bottom = (number - 1) * paginator.per_page
            top = bottom + paginator.per_page
            if top + paginator.orphans >= paginator.count:
                top = paginator.count

            self.page = Page(paginator.object_list[bottom:top], number, paginator)

        if paginator.num_pages > 1 and self.template is not None:
            # The browsable API should display pagination controls.
            self.display_page_controls = True

        self.request = request
        return list(self.page)

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('list', data),
            ('total_count', self.page.paginator.count)
        ]))
