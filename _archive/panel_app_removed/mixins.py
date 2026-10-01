from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Faqat o'qituvchi/administrator (yoki superuser) kira oladi."""

    def test_func(self):
        return bool(self.request.user.is_authenticated and self.request.user.can_manage_content)
