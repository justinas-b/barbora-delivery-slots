import os
from Barbora import Barbora


barbora = Barbora(
    username=os.getenv("username"),
    password=os.getenv("password"),
    msteams_webhook=os.getenv("webhook")
)
barbora.run_once()
# barbora.run_loop()
