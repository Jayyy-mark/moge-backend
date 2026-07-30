from rest_framework.views import APIView, Request, Response
from django.db.models import Q
from features.staffs.presentation.staff_serializers import StaffCreateSerializer, StaffUpdateSerializer, StaffResponseSerializer, StaffGetByColumnSerializer
from features.staffs.application.contracts.request_contracts import StaffCreateContract, StaffUpdateContract, StaffDeleteContract, StaffGetByIdContract, StaffGetByColumnContract
from features.staffs.application.services.staff_service import StaffService
from common.security.authorization.roles import Roles


def get_staff_department_filter(request) -> Q:
    """
    Returns a Q filter scoping staffs to the requesting user's department.
    Admins/super admins get an empty Q() (no restriction).
    For others: filter by department_id = user.staff.department_id.
    If the user has no linked staff/department, returns a safe empty-result filter.
    """
    if request.user.role in Roles.PRIVILEGED:
        return Q()

    staff = getattr(request.user, "staff", None)
    if staff is None or staff.department_id is None:
        return Q(pk__in=[])

    return Q(department_id=staff.department_id)

class StaffController(APIView):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def toApiResponse(self,data)->Response:
        return Response(data=data)

    def post(self, request: Request)->Response:
        serializer = StaffCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        contract = StaffCreateContract(**serializer.validated_data)

        staff,message = StaffService.createStaff(contract)

        return self.toApiResponse({"staff" : StaffResponseSerializer(staff).data, "message" : message})
    
    def get(self, request: Request)->Response:

        from features.staffs.models import Staff
        from features.staffs.infrastructure.staff_mapper import StaffMapper

        dept_filter = get_staff_department_filter(request)

        if dept_filter == Q():
            # Admin — use the existing service (fetches all)
            staffs = StaffService.allStaffs()
        else:
            # Non-admin — filter directly at DB level
            staff_qs = Staff.objects.select_related(
                "department", "role", "rank", "stype"
            ).filter(dept_filter)
            staffs = [StaffMapper.toContract(StaffMapper.toEntity(s)) for s in staff_qs]

        res = StaffResponseSerializer(staffs, many=True)

        return self.toApiResponse({"staffs": res.data})

    def put(self, request : Request, id:int)->Response:

        serializer = StaffUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        contract = StaffUpdateContract(**serializer.validated_data)
        
        staff,message = StaffService.updateStaff(contract)

        res= StaffResponseSerializer(staff)

        return self.toApiResponse({"staff" : res.data, "message" : message})
    
    def delete(self, request:Request, id:int)->Response:
        contract = StaffDeleteContract(id=id)

        message = StaffService.deleteStaff(contract)

        return self.toApiResponse({"message" : message})
    
class GetStaffByIdView(APIView):
    def get(self, request:Request, id:int)->Response:

        contract = StaffGetByIdContract(id=id)

        staff = StaffService.getStaffsById(contract)

        return Response({
            "staff" : StaffResponseSerializer(staff).data
        })
    
class GetStaffByColumnView(APIView):

    def get(self, request:Request)->Response:

        from features.staffs.models import Staff
        from features.staffs.infrastructure.staff_mapper import StaffMapper
        from features.shared.helpers.helper import removeNoneValue

        serializer = StaffGetByColumnSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        dept_filter = get_staff_department_filter(request)

        if dept_filter == Q():
            # Admin — use existing service
            contract = StaffGetByColumnContract(**serializer.validated_data)
            staffs = StaffService.getStaffsByColumn(contract)
        else:
            # Non-admin — apply both the column search filter and dept filter
            from features.staffs.infrastructure.staff_mapper import StaffMapper
            contract = StaffGetByColumnContract(**serializer.validated_data)
            from features.staffs.application.usecases.getByColumn_usecase import GetByColumnUseCase
            # Get base query filtered by column
            model_data = removeNoneValue({
                "staff_id": serializer.validated_data.get("staff_id"),
                "staff_name": serializer.validated_data.get("staff_name"),
                "staff_email": serializer.validated_data.get("staff_email"),
                "staff_address": serializer.validated_data.get("staff_address"),
                "staff_ph_number": serializer.validated_data.get("staff_ph_number"),
                "staff_gender": serializer.validated_data.get("staff_gender"),
                "department_id": serializer.validated_data.get("department_id"),
                "role_id": serializer.validated_data.get("role_id"),
                "rank_id": serializer.validated_data.get("rank_id"),
                "stype_id": serializer.validated_data.get("stype_id"),
            })
            staff_qs = Staff.objects.select_related(
                "department", "role", "rank", "stype"
            ).filter(dept_filter).filter(**model_data)
            staffs = [StaffMapper.toContract(StaffMapper.toEntity(s)) for s in staff_qs]

        return Response({
            "staffs": StaffResponseSerializer(staffs, many=True).data
        })
    




        



        




