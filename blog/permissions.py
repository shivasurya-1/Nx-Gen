from rest_framework.permissions import BasePermission


# class IsAdminOnly(BasePermission):
#     def has_permission(self, request, view):
#         return request.user.is_authenticated and (
#             request.user.is_superuser or request.user.role in ['admin', 'Blog_admin']
#         )


class IsAdminOnly(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            (
                request.user.is_superuser or
                request.user.role == "blog_admin"
            )
        )