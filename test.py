import asyncio
import util

from orm import Node


async def main():
    node = Node(util.generate_node_id())

    active_nodes = await node.bootstrap()

    print(active_nodes)


if __name__ == "__main__":
    asyncio.run(main())
