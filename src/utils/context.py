from llama_index.core.workflow import Context


async def append(context: Context, key: str, value: str):
    values = await context.get(key, [])

    if not isinstance(values, list):
        values = [values]

    values.append(value)

    await context.set(key, values)
