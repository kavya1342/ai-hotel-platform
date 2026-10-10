import asyncio

from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import BaseModel, Field

from app.core.config import settings
from app.models.guest_request import (
    GuestRequestCategory,
    GuestRequestPriority,
)


class GuestRequestAIClassification(BaseModel):
    category: GuestRequestCategory
    priority: GuestRequestPriority
    summary: str = Field(
        min_length=3,
        max_length=500,
    )


class GeminiClassificationError(Exception):
    pass


RETRYABLE_STATUS_CODES = {
    429,
    500,
    502,
    503,
    504,
}

MAX_ATTEMPTS = 3


async def classify_guest_request(
    message: str,
) -> GuestRequestAIClassification:
    prompt = f"""
Classify the following hotel guest-service request.

Classification guidance:
- Housekeeping includes cleaning, towels, linen and toiletries.
- Maintenance includes broken appliances, plumbing, electrical,
  air-conditioning and room repairs.
- Food and beverage includes meals, drinks and room service.
- Front desk includes billing, check-in, checkout and reservation help.
- Transportation includes taxis, airport transfers and vehicle requests.
- Use OTHER when none of these categories apply.

Priority guidance:
- URGENT: immediate safety, security or medical risk.
- HIGH: an essential room facility is unusable.
- MEDIUM: important but not immediately disruptive.
- LOW: optional or non-urgent request.

Provide a concise one-sentence summary.

Guest message:
{message}
""".strip()

    client = genai.Client(
        api_key=settings.gemini_api_key,
    )

    async_client = client.aio

    try:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = (
                    await async_client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=(
                                GuestRequestAIClassification
                            ),
                        ),
                    )
                )

                if response.parsed is not None:
                    return (
                        GuestRequestAIClassification.model_validate(
                            response.parsed
                        )
                    )

                if response.text:
                    return (
                        GuestRequestAIClassification
                        .model_validate_json(
                            response.text
                        )
                    )

                raise GeminiClassificationError(
                    "Gemini returned an empty classification."
                )

            except APIError as error:
                is_retryable = (
                    error.code
                    in RETRYABLE_STATUS_CODES
                )

                is_last_attempt = (
                    attempt == MAX_ATTEMPTS
                )

                if (
                    not is_retryable
                    or is_last_attempt
                ):
                    raise GeminiClassificationError(
                        "Gemini could not classify "
                        "the guest request."
                    ) from error

                delay_seconds = 2 ** (attempt - 1)

                await asyncio.sleep(delay_seconds)

            except GeminiClassificationError:
                raise

            except Exception as error:
                raise GeminiClassificationError(
                    "Gemini could not classify "
                    "the guest request."
                ) from error

        raise GeminiClassificationError(
            "Gemini classification failed "
            "after all retry attempts."
        )

    finally:
        await async_client.aclose()