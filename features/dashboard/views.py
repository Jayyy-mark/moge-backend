from rest_framework.views import APIView, Response, Request
from .helpers import getDepartmentCount, getDocumentCount, getStaffCount
from common.security.authorization.roles import Roles


class DashboardView(APIView):

    def get(self, request: Request) -> Response:
        # Determine department scope for non-admin users
        department_id = None
        if request.user.role not in Roles.PRIVILEGED:
            staff = getattr(request.user, "staff", None)
            if staff is not None:
                department_id = staff.department_id

        return Response({
            "summary": {
                "count": {
                    "staffs": getStaffCount(department_id=department_id),
                    "documents": getDocumentCount(department_id=department_id),
                    "departments": getDepartmentCount(),
                }
            }
        })