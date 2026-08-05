from .schemas import WorkflowState


class WorkflowRepository:
    """
    In-memory workflow repository.

    Week1 implementation.
    """

    def __init__(self):
        self._storage: dict[
            str,
            WorkflowState
        ] = {}


    def save(
        self,
        state: WorkflowState,
    ):
        self._storage[
            state.businessId
        ] = state


    def get(
        self,
        business_id: str,
    ) -> WorkflowState | None:

        return self._storage.get(
            business_id
        )


    def exists(
        self,
        business_id: str,
    ) -> bool:

        return (
            business_id
            in self._storage
        )


repository = WorkflowRepository()