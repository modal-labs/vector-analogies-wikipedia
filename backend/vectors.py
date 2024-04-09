import modal

from common import generate_batches

MODEL_ID = "BAAI/bge-small-en-v1.5"
MODEL_SLUG = MODEL_ID.split("/")[-1]

BATCH_SIZE = 512

LAUNCH_FLAGS = [
    "--model-id",
    MODEL_ID,
    "--port",
    "8000",
    "--max-client-batch-size",
    str(BATCH_SIZE),
    "--max-batch-tokens",
    str(BATCH_SIZE * 512),
]


GPU_CONFIG = modal.gpu.A10G()
GPU_CONCURRENCY = 4


if isinstance(GPU_CONFIG, modal.gpu.A10G):
    DOCKER_IMAGE = (
        "ghcr.io/huggingface/text-embeddings-inference:86-0.4.0"  # Ampere 86 for A10s
    )
elif isinstance(GPU_CONFIG, modal.gpu.A100):
    DOCKER_IMAGE = (
        "ghcr.io/huggingface/text-embeddings-inference:0.4.0"  # Ampere 80 for A100s
    )
elif isinstance(GPU_CONFIG, modal.gpu.T4):
    DOCKER_IMAGE = (
        "ghcr.io/huggingface/text-embeddings-inference:0.3.0"  # Turing for T4s
    )

tei_image = (
    modal.Image.from_registry(
        DOCKER_IMAGE,
        add_python="3.10",
    )
    .dockerfile_commands("ENTRYPOINT []")
    .pip_install("httpx")
)

with tei_image.imports():
    import asyncio

    import numpy as np

stub = modal.Stub("text-embeddings-inference-wikipedia-wcs", image=tei_image)


def spawn_server():
    import socket
    import subprocess

    process = subprocess.Popen(["text-embeddings-router"] + LAUNCH_FLAGS)

    # Poll until webserver at 127.0.0.1:8000 accepts connections before running inputs.
    while True:
        try:
            socket.create_connection(("127.0.0.1", 8000), timeout=1).close()
            print("Webserver ready!")
            return process
        except (socket.timeout, ConnectionRefusedError):
            # Check if launcher webserving process has exited.
            # If so, a connection can never be made.
            retcode = process.poll()
            if retcode is not None:
                raise RuntimeError(f"launcher exited unexpectedly with code {retcode}")


@stub.cls(
    gpu=GPU_CONFIG,
    image=tei_image,
    concurrency_limit=GPU_CONCURRENCY,
    allow_concurrent_inputs=True,
    retries=3,
)
class TextEmbeddingsInference:
    @modal.build()
    def download_model(self):
        # Wait for server to start. This downloads the model weights when not present.
        spawn_server()

    @modal.enter()
    def open_connection(self):
        # If the process is running for a long time, the client does not seem to close the connections, results in a pool timeout
        from httpx import AsyncClient

        self.process = spawn_server()
        self.client = AsyncClient(base_url="http://127.0.0.1:8000", timeout=30)

    @modal.exit()
    def terminate_connection(self):
        self.process.terminate()

    async def _embed(self, chunk_batch):
        texts = [chunk[3] for chunk in chunk_batch]
        res = await self.client.post("/embed", json={"inputs": texts})
        return np.array(res.json())

    @modal.method()
    async def embed(self, chunks):
        """Embeds a list of texts.  id, url, title, text = chunks[0]"""

        # in order to send more data per request, we batch requests to
        # `TextEmbeddingsInference` and make concurrent requests to the endpoint
        coros = [
            self._embed(chunk_batch)
            for chunk_batch in generate_batches(chunks, batch_size=BATCH_SIZE)
        ]

        embeddings = np.concatenate(await asyncio.gather(*coros))
        return chunks, embeddings
