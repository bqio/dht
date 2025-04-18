from __future__ import annotations

import bencode
import util
import asyncudp
import asyncio

type NodeID = bytes
type NodeAddr = tuple[str, int]
type NodeSocket = asyncudp.Socket

BOOTSTRAP_NODES = [
    ("router.bittorrent.com", 6881),
    ("dht.transmissionbt.com", 6881),
    ("127.0.0.1", 6881),
]


class Node:
    def __init__(self, node_id: NodeID):
        self.node_id: NodeID = node_id

    async def connect(self, addr: NodeAddr) -> Session:
        return await Session.create(self, addr)

    async def bootstrap(self) -> list[NodeAddr]:
        active_nodes = []
        for addr in BOOTSTRAP_NODES:
            try:
                async with await self.connect(addr) as session:
                    await session.ping()
                    active_nodes.append(addr)
            except (TimeoutError, OSError):
                continue
        return active_nodes


class Session:
    def __init__(self, node: Node, sock: NodeSocket, addr: NodeAddr):
        self.node: Node = node
        self.sock: NodeSocket = sock
        self.addr: NodeAddr = addr

    @classmethod
    async def create(cls: Session, node: Node, addr: NodeAddr) -> Session:
        sock = await asyncudp.create_socket(remote_addr=addr)
        return cls(node, sock, addr)

    async def __aenter__(self) -> Session:
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()

    async def close(self) -> None:
        if self.sock:
            self.sock.close()

    async def _send_query(self, query: Query) -> dict[str, bencode.SupportedTypes]:
        self.sock.sendto(query.serialized)
        data, _ = await asyncio.wait_for(self.sock.recvfrom(), timeout=5.0)
        return bencode.decode_dict(data)

    async def ping(self) -> Response:
        try:
            decoded = await self._send_query(PingQuery(self.node.node_id))
            return Response(decoded)
        except asyncio.TimeoutError:
            raise TimeoutError("Server not respond")

    async def find_node(self, target_id: NodeID) -> FindNodeResponse:
        try:
            decoded = await self._send_query(
                FindNodeQuery(self.node.node_id, target_id)
            )
            return FindNodeResponse(decoded)
        except asyncio.TimeoutError:
            raise TimeoutError("Server not respond")


class Response:
    def __init__(self, decoded: dict[str, bencode.SupportedTypes]):
        self.id: NodeID = decoded["r"]["id"]
        self.t: bytes = decoded["t"]

    def __repr__(self):
        return str(self.__dict__)


class FindNodeResponse(Response):
    def __init__(self, decoded: dict[str, bencode.SupportedTypes]):
        super().__init__(decoded)
        self.nodes = decoded["r"]["nodes"]


class Query:
    def __init__(self, node_id: NodeID, method: str):
        self.t = util.generate_transaction_id()
        self.y = "q"
        self.q = method
        self.a = {"id": node_id}

    @property
    def serialized(self) -> bytes:
        return bencode.encode_dict(self.__dict__)


class PingQuery(Query):
    def __init__(self, node_id: NodeID):
        super().__init__(node_id, "ping")


class FindNodeQuery(Query):
    def __init__(self, node_id: NodeID, target_id: NodeID):
        super().__init__(node_id, "find_node")
        self.a["target"] = target_id
