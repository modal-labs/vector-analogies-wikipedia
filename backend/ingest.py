import json

import modal

from common import cache_dir, volume, image, generate_batches
from vectors import GPU_CONCURRENCY

stub = modal.Stub("wikipedia-wcs", image=image)

WEAVIATE_BATCH = 10 * 5120


@stub.function(
    image=image,
    volumes={
        cache_dir: volume,
    },
    timeout=86400,
)
def embed_dataset(down_scale: float = 1, batch_size: int = 512 * 50):
    """
    Embeds a dataset with the Text Embeddings Inference container and send the results to Weaviate.

    Args:
        down_scale (float): The fraction of the training data to select. Defaults to 1.
        batch_size (int): The batch size to use. Defaults to 512 * 50.

    Returns:
        dict: A dictionary containing the benchmark results.
    """
    import datetime
    import time

    subset = load_dataset_from_disk(down_scale)
    model = modal.Cls.lookup(
        "text-embeddings-inference-wikipedia-wcs", "TextEmbeddingsInference"
    )
    WeaviateClient = modal.Cls.lookup("modal-weaviate", "WeaviateClient")
    text_chunks = generate_chunks_from_dataset(subset, chunk_size=512)
    batches = generate_batches(text_chunks, batch_size=batch_size)

    print("🚀: running embedding engine")
    start = time.perf_counter()
    total, acc_characters = 0, 0
    batch_metadata, batch_embeddings = [], []
    handles = []
    for resp in model.embed.map(batches, order_outputs=False, return_exceptions=True):
        if isinstance(resp, Exception):
            print(f"Exception: {resp}")
            continue

        chunks, embeddings = resp
        acc_characters += sum(map(len, [chunk[3] for chunk in chunks]))
        metadata = [
            {
                "identifier": int(chunk[0]),
                "url": chunk[1],
                "title": chunk[2],
                "content": chunk[3],
                "chunk_index": int(chunk[4]),
            }
            for ii, chunk in enumerate(chunks)
        ]

        batch_metadata.extend(metadata)
        batch_embeddings.extend(embeddings)

        if len(batch_metadata) >= WEAVIATE_BATCH:
            print(f"🧶: inserting batch of size {len(batch_metadata)} into Weaviate")
            handles.append(
                WeaviateClient.insert.spawn(
                    metadata=batch_metadata, vectors=batch_embeddings
                )
            )
            total += len(batch_metadata)
            batch_metadata, batch_embeddings = [], []

    if batch_metadata:
        print(f"🧶: inserting batch of size {len(batch_metadata)} into Weaviate")
        handles.append(
            WeaviateClient.insert.spawn(
                metadata=batch_metadata, vectors=batch_embeddings
            )
        )
        total += len(batch_metadata)
        batch_metadata, batch_embeddings = [], []

    for handle in handles:
        handle.get()
    end = time.perf_counter()
    print(f"🧶: sent {total} rows into Weaviate")
    weaviate_count = WeaviateClient.total_count.remote()
    if weaviate_count != total:
        print(
            f"🧶: Weaviate count mismatch: {weaviate_count} on Weaviate, {total} inserted"
        )

    duration = end - start
    characters = acc_characters
    characters_per_sec = int(characters / duration)
    dataset_chars = 19560538957  # sum(map(len, dataset["train"]["text"]))
    extrapolated_duration_cps_fmt = str(
        datetime.timedelta(seconds=dataset_chars / characters_per_sec)
    )
    resp = {
        "downscale": down_scale,
        "batch_size": batch_size,
        "n_gpu": GPU_CONCURRENCY,
        "duration_mins": duration / 60,
        "characters_per_sec": characters_per_sec,
        "extrapolated_duration": extrapolated_duration_cps_fmt,
    }

    return resp


@stub.local_entrypoint()
def main(down_scale: float = 1.0, annotation: str = ""):
    batch_size = 512 * 2 * GPU_CONCURRENCY
    downscale_str = (
        f"{int(down_scale * 100)}%"
        if down_scale >= 0.01
        else f"{int(down_scale * 1000)}m"
    )
    with open(f"benchmarks-{downscale_str}.json", "a") as f:
        benchmark = embed_dataset.remote(down_scale=down_scale, batch_size=batch_size)
        benchmark["annotation"] = annotation
        f.write(json.dumps(benchmark, indent=2) + "\n")


def load_dataset_from_disk(down_scale: float = 0.01):
    """
    Load a dataset from disk and return a subset of the training data.

    Args:
        down_scale (float): The fraction of the training data to select. Defaults to 0.01.

    Returns:
        Dataset: A subset of the training data.
    """
    import time

    from datasets import load_from_disk

    start = time.perf_counter()

    print(f"💽: loading dataset from {cache_dir}/wikipedia")
    dataset = load_from_disk(f"{cache_dir}/wikipedia")
    print(f"💽: dataset loaded in {time.perf_counter()-start:.2f} seconds")

    ttl_size = len(dataset["train"])

    sample_size = int(ttl_size * down_scale)

    return dataset["train"].select(range(sample_size))


def generate_chunks_from_dataset(xs, chunk_size: int = 512):
    for data in xs:
        id_ = data["id"]
        url = data["url"]
        title = data["title"]
        text = data["text"]
        for idx, chunk_start in enumerate(range(0, len(text), chunk_size)):
            yield (
                id_,
                url,
                title,
                text[chunk_start : chunk_start + chunk_size],
                idx,
            )
