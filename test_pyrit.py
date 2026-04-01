import asyncio
from pyrit.models import MessagePiece
from pyrit.prompt_target import OpenAIChatTarget
from pyrit.memory import CentralMemory, SQLiteMemory

memory = SQLiteMemory(db_path=":memory:")
CentralMemory.set_memory_instance(memory)

target = OpenAIChatTarget(model_name="test", endpoint="http://localhost", api_key="dummy")
print("Target hasattr set_system_prompt:", hasattr(target, "set_system_prompt"))
print("CentralMemory methods:", dir(CentralMemory.get_memory_instance()))
