from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Request,
)

from fastapi.responses import (
    HTMLResponse,
)

from fastapi.templating import (
    Jinja2Templates,
)

from .config import get_settings
from .gemini_flash import generate_outline
from .gemini_pro import generate_story
from .image_generator import generate_image
from .layout_builder import build_comic_layout
from .exporters import save_pdf

from .schemas import PromptRequest


router = APIRouter()

settings = get_settings()

templates = Jinja2Templates(
    directory=str(
        settings.templates_dir
    )
)


def make_title(
    request: PromptRequest
) -> str:

    return (
        f"{request.character_name}'s Adventure"
    )


def generate_comic(
    request: PromptRequest
):

    outline = generate_outline(
        request
    )

    story = generate_story(
        request,
        outline
    )

    layout = build_comic_layout(
        outline,
        story
    )

    pdf_path = save_pdf(
        layout,
        title=make_title(request)
    )

    return (
        make_title(request),
        layout,
        pdf_path
    )


@router.get(
    "/",
    response_class=HTMLResponse
)
async def home(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "error": None
        }
    )


@router.post(
    "/generate",
    response_class=HTMLResponse
)
async def generate(
    request: Request,

    story_prompt: str = Form(...),

    character_name: str = Form(...),

    setting: str = Form(...),

    tone: str = Form(...),

    art_style: str = Form(...)
):

    try:

        prompt_request = PromptRequest(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style
        )

        title, layout, pdf_path = (
            generate_comic(
                prompt_request
            )
        )

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "title": title,
                "layout": layout,
                "pdf_url":
                    f"/static/{pdf_path}"
            }
        )

    except Exception as exc:

        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "error": str(exc)
            },
            status_code=500
        )


@router.post(
    "/generate-comic/json"
)
async def generate_comic_json(
    payload: PromptRequest
):

    try:

        title, layout, pdf_path = (
            generate_comic(
                payload
            )
        )

        return {
            "title": title,
            "layout": layout,
            "pdf_url":
                f"/static/{pdf_path}"
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc


@router.post(
    "/test-image"
)
async def test_image(
    prompt: str = Form(...)
):

    try:

        path = generate_image(
            prompt,
            panel_number=0,
            title="test_image"
        )

        return {
            "image_url":
                f"/static/{path}",

            "image_path":
                path
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        ) from exc


@router.get(
    "/export-success",
    response_class=HTMLResponse
)
async def export_success(
    request: Request,
    pdf_url: str | None = None
):

    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "pdf_url": pdf_url
        }
    )