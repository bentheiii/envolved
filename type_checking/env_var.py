from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager, nullcontext

from envolved import EnvVar, env_var, inferred_env_var
from envolved.describe import exclude_from_description

number_ev = env_var("NUMBER", type=int)
i: int = number_ev.get()

ignored_number_ev = exclude_from_description(env_var("IGNORED_NUMBER", type=int))
j: int = ignored_number_ev.get()


# test contravariance
@asynccontextmanager
async def cont(a: int, b: str) -> AsyncIterator[int]:
    yield a


base_ev: EnvVar[AbstractAsyncContextManager[int | None]] = exclude_from_description(
    env_var("SEQ_", type=cont, args={"a": inferred_env_var(), "b": inferred_env_var()})
)
seq_ev = base_ev.with_prefix("SEQ_")
seq_ev.default = nullcontext()


async def test_cont() -> int | None:
    async with seq_ev.get() as t:
        return t
