import asyncio

asyncio.run()

result = await asyncio.gather()

done, pending = await asyncio.wait(tasks)

await asyncio.wait_for()  # Deprecated
asyncio.as_completed()

