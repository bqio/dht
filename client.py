import asyncio
import asyncudp
import bencode
import util

NODE_ID = util.generate_node_id()

# KRPC Proto Message
# t: Transaction ID
# y: Type of message (q - for query, r - for response, e - for error)
# v: Client version string
# if y is q:
#   has key q: Query method name
#   has key a: Query arguments
#   All queries have an id key and value containing the node ID of the querying node.
# if y is r:
#   has key r: Response return values
#   All responses have an id key and value containing the node ID of the responding node.
# if y is e:
#   has key e: List of error args (0 - integer error code, 1 - string error message)


def send_ping(sock: asyncudp.Socket):
    transaction_id = util.generate_transaction_id()
    query = {"t": transaction_id, "y": "q", "q": "ping", "a": {"id": NODE_ID}}
    sock.sendto(bencode.encode_dict(query))


def send_wrong_packet(sock: asyncudp.Socket):
    transaction_id = util.generate_transaction_id()
    query = {"t": transaction_id, "y": "q", "q": "wrong", "a": {"id": NODE_ID}}
    sock.sendto(bencode.encode_dict(query))


def send_find_node(sock: asyncudp.Socket, target_id: bytes):
    transaction_id = util.generate_transaction_id()
    query = {
        "t": transaction_id,
        "y": "q",
        "q": "find_node",
        "a": {"id": NODE_ID, "target": target_id},
    }
    sock.sendto(bencode.encode_dict(query))


async def send_get_peers():
    pass


async def send_announce_peer():
    pass


async def udp_client():
    sock = await asyncudp.create_socket(remote_addr=("127.0.0.1", 9999))

    send_ping(sock)

    data, addr = await sock.recvfrom()

    print(bencode.decode_dict(data), addr)

    send_find_node(sock, b"aa")

    data, addr = await sock.recvfrom()

    print(bencode.decode_dict(data), addr)

    sock.close()


if __name__ == "__main__":
    asyncio.run(udp_client())
