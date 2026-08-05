from .models import AuditEvent


events: list[AuditEvent] = []



def save(
    event: AuditEvent
):
    """
    Save audit event.
    """

    events.append(
        event
    )



def get_last_hash(
    business_id: str
) -> str | None:
    """
    Get latest hash.
    """

    business_events = [
        event
        for event in events
        if event.businessId == business_id
    ]


    if not business_events:
        return None


    return business_events[-1].eventHash



def list_by_business(
    business_id: str
) -> list[AuditEvent]:

    return [
        event
        for event in events
        if event.businessId == business_id
    ]



def verify_chain(
    business_id: str
) -> bool:

    business_events = (
        list_by_business(
            business_id
        )
    )


    previous_hash = None


    for event in business_events:

        if event.previousHash != previous_hash:
            return False


        previous_hash = event.eventHash


    return True
class AuditRepositoryAdapter:
    """
    Compatibility wrapper.
    """

    def save(
        self,
        event: AuditEvent
    ):
        return save(event)


    def get_last_hash(
        self,
        business_id: str
    ):
        return get_last_hash(
            business_id
        )


    def list_by_business(
        self,
        business_id: str
    ):
        return list_by_business(
            business_id
        )


    def verify_chain(
        self,
        business_id: str
    ):
        return verify_chain(
            business_id
        )


audit_repository = AuditRepositoryAdapter()