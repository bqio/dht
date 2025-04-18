import asyncio
import asyncudp
import bencode
import util

NODE_ID = util.generate_node_id()


def is_ping_packet(packet: dict[str, bencode.SupportedTypes]) -> bool:
    return packet["y"] == "q" and packet["q"] == "ping"


def is_find_node_packet(packet: dict[str, bencode.SupportedTypes]) -> bool:
    return packet["y"] == "q" and packet["q"] == "find_node"


def is_get_peers_packet(packet: dict[str, bencode.SupportedTypes]) -> bool:
    return packet["y"] == "q" and packet["q"] == "get_peers"


def is_announce_peer_packet(packet: dict[str, bencode.SupportedTypes]) -> bool:
    return packet["y"] == "q" and packet["q"] == "announce_peer"


async def handle_query(sock: asyncudp.Socket, data: bytes, addr: tuple[str, int]):
    packet = bencode.decode_dict(data)

    print(f"[QUERY] {addr}: {packet}")

    if is_ping_packet(packet):
        handle_ping(sock, packet, addr)
    elif is_find_node_packet(packet):
        handle_find_node(sock, packet, addr)
    elif is_get_peers_packet(packet):
        handle_get_peers(sock, packet, addr)
    elif is_announce_peer_packet(packet):
        handle_announce_peer(sock, packet, addr)
    else:
        handle_error(sock, packet, addr, 204, "Method Unknown")


def handle_ping(
    sock: asyncudp.Socket,
    packet: dict[str, bencode.SupportedTypes],
    addr: tuple[str, int],
):
    response = {"t": packet["t"], "y": "r", "r": {"id": NODE_ID}}
    sock.sendto(bencode.encode_dict(response), addr)


def handle_find_node(
    sock: asyncudp.Socket,
    packet: dict[str, bencode.SupportedTypes],
    addr: tuple[str, int],
):
    # TODO nodes implementation
    response = {"t": packet["t"], "y": "r", "r": {"id": NODE_ID, "nodes": []}}
    sock.sendto(bencode.encode_dict(response), addr)


def handle_get_peers(
    sock: asyncudp.Socket,
    packet: dict[str, bencode.SupportedTypes],
    addr: tuple[str, int],
):
    pass


def handle_announce_peer(
    sock: asyncudp.Socket,
    packet: dict[str, bencode.SupportedTypes],
    addr: tuple[str, int],
):
    pass


def handle_error(
    sock: asyncudp.Socket,
    packet: dict[str, bencode.SupportedTypes],
    addr: tuple[str, int],
    error_code: int,
    error_message: str,
):
    error = {"t": packet["t"], "y": "e", "e": [error_code, error_message]}
    sock.sendto(bencode.encode_dict(error), addr)


async def udp_server():
    sock = await asyncudp.create_socket(local_addr=("127.0.0.1", 6881))

    print(f"Node ({NODE_ID.hex()}) has been started")

    while True:
        data, addr = await sock.recvfrom()
        await handle_query(sock, data, addr)


asyncio.run(udp_server())
