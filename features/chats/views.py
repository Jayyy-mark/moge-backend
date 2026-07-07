from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Document
from .orchestration.orchestration import ChatOrchestrator
from .services.rag import store_document


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def chat(request):
    message = request.data.get("message")
    file = request.FILES.get("file")
    document_id = request.data.get("document_id")

    try:
        payload, status = ChatOrchestrator().handle(request.user, message, file=file, document_id=document_id)
        return Response(payload, status=status)
    except RuntimeError as error:
        return Response({"error": str(error)}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_chat_document(request):
    file = request.FILES.get("file")
    if not file:
        return Response({"error": "File required"}, status=400)

    try:
        document = Document.objects.create(file=file)
        upload_info = store_document(document.file.path, user_id=str(request.user.id))
        return Response(
            {
                "document_id": document.id,
                "file_name": file.name,
                "document_status": upload_info,
            },
            status=201,
        )
    except RuntimeError as error:
        return Response({"error": str(error)}, status=500)
