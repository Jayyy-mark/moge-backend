from features.staffs.models import Staff
from features.departments.models import Department
from features.documents.models import Document


def getStaffCount(department_id=None):
    if department_id is not None:
        return Staff.objects.filter(department_id=department_id).count()
    return Staff.objects.count()

def getDepartmentCount():
    return Department.objects.count()

def getDocumentCount(department_id=None):
    if department_id is not None:
        return Document.objects.filter(staff__department_id=department_id).count()
    return Document.objects.count()