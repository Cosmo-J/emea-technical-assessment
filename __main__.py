import hypercorn
import asyncio
import restate

from app.services.greeter import greeter
from app.services.OrderIngestion import OrderIngestion
from app.services.Isa95Mapper import Isa95Mapper


app = restate.app(services=[OrderIngestion,Isa95Mapper])


def main():
    """Entry point for running the app."""
    conf = hypercorn.Config()
    conf.bind = ["0.0.0.0:9080"]
    asyncio.run(hypercorn.asyncio.serve(app, conf))


if __name__ == "__main__":
    main()
