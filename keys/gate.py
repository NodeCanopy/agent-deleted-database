DESTRUCTIVE = {"volumeDelete", "volumeRestore"}


class NeedsApproval(Exception):
    pass


class Gate:
    """The agent's only way to the API."""

    def __init__(self, api):
        self.api = api
        self.pending = []
        self.approved = []

    def mutate(self, secret, op, **args):
        request = (op, args)
        if op in DESTRUCTIVE and request not in self.approved:
            self.pending.append(request)
            raise NeedsApproval(f"held {op}, waiting for a human")
        return self.api.mutate(secret, op, **args)

    def approve(self, op, **args):
        self.pending.remove((op, args))
        self.approved.append((op, args))
