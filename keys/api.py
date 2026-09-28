import time

SCOPE_FOR = {
    "customDomainCreate": "domains",
    "volumeDelete": "volumes:delete",
    "volumeRestore": "volumes:delete",
}

UNDO_WINDOW = 48 * 3600


class Forbidden(Exception):
    pass


class Platform:
    def __init__(self, scoped_tokens=False, delayed_delete=False, clock=time.time):
        self.scoped_tokens = scoped_tokens
        self.delayed_delete = delayed_delete
        self.clock = clock
        self.volumes = {}
        self.trash = {}
        self.tokens = {}
        self.domains = []
        self.handlers = {
            "customDomainCreate": self.add_domain,
            "volumeDelete": self.delete_volume,
            "volumeRestore": self.restore_volume,
        }

    def add_volume(self, volume_id, name, environments, rows, backups=12):
        self.volumes[volume_id] = {
            "name": name,
            "environments": environments,
            "rows": rows,
            "backups": [f"{name}@{n}" for n in range(backups)],
        }

    def add_token(self, secret, name, scopes):
        self.tokens[secret] = {"name": name, "scopes": set(scopes)}

    def mutate(self, secret, op, **args):
        token = self.tokens.get(secret)
        if token is None:
            raise Forbidden("401 unknown token")
        if self.scoped_tokens and SCOPE_FOR[op] not in token["scopes"]:
            raise Forbidden(f"403 token '{token['name']}' cannot {op}")
        return self.handlers[op](**args)

    def rows(self, volume_id):
        volume = self.volumes.get(volume_id)
        return volume["rows"] if volume else 0

    def add_domain(self, domain):
        self.domains.append(domain)
        return f"added {domain}"

    def delete_volume(self, volume_id):
        volume = self.volumes.pop(volume_id)
        where = "+".join(volume["environments"])
        if self.delayed_delete:
            self.trash[volume_id] = (volume, self.clock() + UNDO_WINDOW)
            return f"{volume['name']} ({where}) will be deleted in 48h"
        # backups live on the volume, so they go with it
        return f"deleted {volume['name']} ({where}) and {len(volume['backups'])} backups"

    def restore_volume(self, volume_id):
        volume, purge_at = self.trash.pop(volume_id)
        if self.clock() > purge_at:
            raise Forbidden(f"{volume['name']} is gone, undo window closed")
        self.volumes[volume_id] = volume
        return f"restored {volume['name']}, {volume['rows']:,} rows"
