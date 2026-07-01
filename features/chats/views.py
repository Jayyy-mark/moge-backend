from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .orchestration.orchestration import ChatOrchestrator


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def chat(request):
    message = request.data.get("message")
    file = request.FILES.get("file")

    try:
        payload, status = ChatOrchestrator().handle(request.user, message, file=file)
        return Response(payload, status=status)
    except RuntimeError as error:
        return Response({"error": str(error)}, status=500)
