from ipaddress import ip_address
from ipaddress import ip_network

from fastapi import HTTPException
from fastapi import Request
from fastapi import status

from config import ADMIN_ALLOWED_NETWORKS


PRIVILEGED_ROLES = {
    "coach",
    "admin",
    "master",
}


def client_ip_from_request(request: Request) -> str | None:
    cloudflare_ip = str(
        request.headers.get(
            "CF-Connecting-IP",
            "",
        )
    ).strip()
    if cloudflare_ip:
        return cloudflare_ip
    if request.client is None:
        return None
    return str(request.client.host or "").strip() or None


def allowed_networks():
    result = []
    for value in ADMIN_ALLOWED_NETWORKS:
        try:
            result.append(ip_network(value, strict=False))
        except ValueError as exc:
            raise RuntimeError(
                "ADMIN_ALLOWED_NETWORKS contém endereço/rede inválido: " + value
            ) from exc
    return tuple(result)


def privileged_ip_allowed(client_ip: str | None) -> bool:
    networks = allowed_networks()
    if not networks:
        return True
    if not client_ip:
        return False
    try:
        address = ip_address(client_ip)
    except ValueError:
        return False
    return any(
        address.version == network.version and address in network
        for network in networks
    )


def require_role_network_access(role: str, request: Request) -> None:
    if role not in PRIVILEGED_ROLES:
        return
    if privileged_ip_allowed(client_ip_from_request(request)):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Acesso administrativo não autorizado a partir desta rede.",
    )
