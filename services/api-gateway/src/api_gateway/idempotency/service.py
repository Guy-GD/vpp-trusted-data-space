from .repository import repository


class IdempotencyService:


    def check(
        self,
        key: str | None,
    ):

        if not key:
            return None

        return repository.get(key)



    def save(
        self,
        key: str | None,
        result: dict,
    ):

        if not key:
            return

        repository.save(
            key,
            result,
        )


idempotency_service = IdempotencyService()