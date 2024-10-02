from typing import List, Union, Awaitable

from openai.types.chat import ChatCompletion
from tenacity import retry, stop_after_attempt, retry_if_exception_type, wait_fixed
from openai import AsyncOpenAI, APIStatusError, OpenAIError

# Настраиваем пользовательскую логику ожидания
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
async def chat_gpt_api(
        openai_client: AsyncOpenAI,
        system_prompt: str,
        user_prompt: str,
        code: str,
        gpt_model: str = "gpt-4o-mini"
) -> Union[tuple[str, int], str]:
    """
    Отправляет код файла на ревью в ChatGPT и получает результат.

    :param gpt_model:
    :param user_prompt: User prompt for chatGPT
    :param system_prompt: System prompt for chatGPT
    :param openai_client: OpenAI client
    :param code: Код для ревью
    :return: Результат анализа и количество токенов
    """
    try:
        response = await openai_client.chat.completions.create(
            model=gpt_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{user_prompt}:\n\n{code}"}
            ]
        )

        return response.choices[0].message.content.strip(), response.usage.total_tokens
    except APIStatusError as e:
        print(f"An error occurred: {str(e)}")
        raise
    except OpenAIError as e:
        print(f"An error occurred: {str(e)}")
        raise
