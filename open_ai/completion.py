from typing import Awaitable, Optional, Union
from openai.types.chat import ChatCompletion
from tenacity import retry, stop_after_attempt, retry_if_exception_type
from openai import AsyncOpenAI, APIStatusError, OpenAIError, OpenAI


def custom_wait(e):
    if isinstance(e, APIStatusError):
        retry_after = e.response.headers.get("Retry-After")
        if retry_after:
            retry_after_seconds = int(retry_after)
            print(f"Received Retry-After header, retrying after {retry_after_seconds} seconds...")
            return retry_after_seconds
        else:
            # Если Retry-After не указан, используем фиксированное ожидание
            return 4
    else:
        # Ожидание по умолчанию для других типов ошибок
        return 4


@retry(
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((APIStatusError, OpenAIError)),
    wait=custom_wait
)
async def create_completion_async(
        openai_client: AsyncOpenAI,
        *,
        system_prompt: str,
        user_prompt: str,
        gpt_model: str = "gpt-4o-mini",
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        response_format: Optional[dict] = None
) -> Awaitable[ChatCompletion]:
    """
    :param response_format: json_schema
    :param top_p: 0 - random, 1 - deterministic
    :param temperature: 0 - deterministic, 1 - random
    :param openai_client: OpenAI client
    :param system_prompt: System prompt for chatGPT
    :param user_prompt: User prompt for chatGPT
    :param gpt_model:
    :return: Результат генерации
    """

    completion_params = {
        "model": gpt_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{user_prompt}"}
        ],
    }

    if temperature is not None:
        completion_params["temperature"] = temperature

    if top_p is not None:
        completion_params["top_p"] = top_p

    if response_format is not None:
        completion_params["response_format"] = response_format

    try:
        completion = await openai_client.chat.completions.create(**completion_params)

        content = completion.choices[0].message.content
        refusal = completion.choices[0].message.refusal

        if refusal is not None:
            print(refusal)
            raise APIStatusError
        return content

    except APIStatusError as e:
        print(f"An error occurred: {str(e)}")
        raise
    except OpenAIError as e:
        print(f"An error occurred: {str(e)}")
        raise
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise


def create_completion(
        openai_client: OpenAI,
        *,
        system_prompt: str,
        user_prompt: str,
        gpt_model: str = "gpt-4o-mini",
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        response_format: Optional[dict] = None
) -> Union[ChatCompletion, str]:
    """
    :param response_format: json_schema
    :param top_p: 0 - random, 1 - deterministic
    :param temperature: 0 - deterministic, 1 - random
    :param openai_client: OpenAI client
    :param system_prompt: System prompt for chatGPT
    :param user_prompt: User prompt for chatGPT
    :param gpt_model:
    :return: Результат генерации
    """

    completion_params = {
        "model": gpt_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{user_prompt}"}
        ],
    }

    if temperature is not None:
        completion_params["temperature"] = temperature

    if top_p is not None:
        completion_params["top_p"] = top_p

    if response_format is not None:
        completion_params["response_format"] = response_format

    try:
        completion = openai_client.chat.completions.create(**completion_params)

        content = completion.choices[0].message.content
        refusal = completion.choices[0].message.refusal

        if refusal is not None:
            print(refusal)
            raise APIStatusError
        return content

    except APIStatusError as e:
        print(f"An error occurred: {str(e)}")
        raise
    except OpenAIError as e:
        print(f"An error occurred: {str(e)}")
        raise
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise