from langchain_core.tools import tool
from django.db.models import Q
from features.staffs.models import Staff
from features.departments.models import Department
from features.ranks.models import Rank
from features.roles.models import Role
from features.stypes.models import Stype
from features.documents.models import Document as DBDocument
from features.buildings.models import Building
from features.rooms.models import Room


@tool
def query_database_tool(query: str) -> str:
    """
    Search the system database for information regarding Staff, Departments, Ranks, Roles, Buildings, Rooms, and Document Records.
    Use this tool whenever the user asks about staff members, staff count, departments, ranks, roles, or database metadata.
    """
    query_lower = query.lower().strip()
    results = []

    # 1. Staff Search
    staff_qs = Staff.objects.all().select_related("department", "role", "rank", "stype")
    
    # Check if query is looking for staff count or list
    if any(k in query_lower for k in ["how many staff", "staff count", "total staff", "list staff", "all staff"]):
        total_staff = staff_qs.count()
        results.append(f"Total Staff Count: {total_staff}")
        staff_samples = staff_qs[:15]
        results.append("Staff List Summary:")
        for s in staff_samples:
            dept_name = s.department.department_name if s.department else "N/A"
            role_name = s.role.role_name if s.role else "N/A"
            rank_name = s.rank.rank_name if s.rank else "N/A"
            results.append(
                f"- ID: {s.staff_id} | Name: {s.staff_name} | Dept: {dept_name} | Role: {role_name} | Rank: {rank_name} | Email: {s.staff_email} | Phone: {s.staff_ph_number} | Gender: {s.staff_gender}"
            )
    else:
        # Search by specific keyword/name in staff
        terms = [t for t in query_lower.split() if len(t) > 1]
        staff_filter = Q()
        for term in terms:
            staff_filter |= (
                Q(staff_name__icontains=term)
                | Q(staff_id__icontains=term)
                | Q(staff_email__icontains=term)
                | Q(staff_ph_number__icontains=term)
                | Q(department__department_name__icontains=term)
                | Q(role__role_name__icontains=term)
                | Q(rank__rank_name__icontains=term)
            )
        matched_staff = staff_qs.filter(staff_filter).distinct()[:10]
        if matched_staff.exists():
            results.append(f"Matched Staff Members ({matched_staff.count()} found):")
            for s in matched_staff:
                dept_name = s.department.department_name if s.department else "N/A"
                role_name = s.role.role_name if s.role else "N/A"
                rank_name = s.rank.rank_name if s.rank else "N/A"
                results.append(
                    f"- Staff ID: {s.staff_id} | Name: {s.staff_name} | Department: {dept_name} | Role: {role_name} | Rank: {rank_name} | Email: {s.staff_email} | Phone: {s.staff_ph_number} | Address: {s.staff_address}"
                )

    # 2. Department Search
    depts = Department.objects.all()
    if any(k in query_lower for k in ["department", "dept"]):
        results.append("\nDepartments in Database:")
        for d in depts:
            staff_count = d.staffs.count()
            results.append(f"- {d.department_name} (Code: {d.department_id}) - Staff Count: {staff_count}")

    # 3. Document Records in DB
    doc_qs = DBDocument.objects.filter(is_archived=False, is_recycled=False)
    terms = [t for t in query_lower.split() if len(t) > 2]
    doc_filter = Q()
    for term in terms:
        doc_filter |= Q(document_name__icontains=term) | Q(document_id__icontains=term) | Q(description__icontains=term)
    
    matched_docs = doc_qs.filter(doc_filter).distinct()[:10]
    if matched_docs.exists():
        results.append("\nMatched Document Metadata in Database:")
        for doc in matched_docs:
            staff_name = doc.staff.staff_name if doc.staff else "N/A"
            file_url = doc.document.url if doc.document else "N/A"
            results.append(
                f"- Document ID: {doc.document_id} | Name: {doc.document_name} | Staff: {staff_name} | File URL: {file_url} | Description: {doc.description or 'N/A'}"
            )

    if not results:
        return f"No database records found matching query: '{query}'. You can try searching by staff name, department name, or document title."

    return "\n".join(results)
